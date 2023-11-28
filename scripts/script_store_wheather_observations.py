#!/usr/bin/env python3
"""
Download wheather data and store into db.
Usage:
  script_store_trees_in_db.py [--db_qtrees=DB_QTREES] [--station_id=STATION_ID][--days=DAYS][--start_date=start_date]
  script_store_trees_in_db.py (-h | --help)
Options:
  --db_qtrees=DB_QTREES                        Database name [default:]
  --station_id=STATION_ID                      Station IDs - single or comma-separated [default: 433]
  --start_date=<start_date>                     Start date in YYYY-MM-DD format. 
"""
import pandas as pd
import geopandas as gpd
import sqlalchemy
import datetime
from sqlalchemy import create_engine
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
from qtrees.dwd import get_weather_stations, get_observations
import requests
import sys

logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    station_ids = args["--station_id"].rsplit(sep=',')
    station_ids = list(map(int, station_ids))
   
    if args["--start_date"]:
        start_date = datetime.datetime.strptime(args["--start_date"], '%Y-%m-%d')
    else: 
        start_date = None # will try yesterday

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    stations = get_weather_stations(station_ids)

    gdf = gpd.GeoDataFrame(
        stations, geometry=gpd.points_from_xy(stations.geoLaenge, stations.geoBreite),
        crs='epsg:4326'  # {'init': 'epsg:4326'}
    )
    gdf["von_datum"] = pd.to_datetime(gdf["von_datum"], format='%Y%m%d')
    gdf["bis_datum"] = pd.to_datetime(gdf["bis_datum"], format='%Y%m%d')
    gdf.columns = [x.lower() for x in gdf.columns]
    gdf = gdf.rename(columns={"stations_id": "id", "geobreite": "lat", "geolaenge": "lon"})

    try:
        if sqlalchemy.inspect(engine).has_table("weather_stations", schema="public"):
            with engine.connect() as con:
                rs = con.execute('select "id" from public.weather_stations')
                indices = [idx[0] for idx in rs]
        gdf = gdf[~gdf.id.isin(indices)]
        gdf.to_postgis("weather_stations", engine, if_exists="append", schema="public")
        logger.info(f"Now, new %s weather stations in database.", len(gdf))
    except Exception as e:
        logger.error("Cannot write to weather_stations: %s", e)
        exit(121)

    for idx in station_ids:
        station = stations[stations.stations_id == idx]

        last_date_in_db = None
        with engine.connect() as con:
            rs = con.execute('select MAX("date") from public.weather WHERE station_id=%s' % loc[0])
            last_date_in_db = [idx[0] for idx in rs][0]
            logger.debug("Latest timestamp in data: %s.", last_date_in_db)

        try:
            weather = get_observations(station, start_date)
            weather = weather.rename(columns={"mess_datum": "date",
                                              "qn_3": "quality_wind", "qn_4": "quality",
                                              "rsk": "rainfall_mm", "rskf": "precipation_form",
                                              "sdk": "sunshine_hours", "shk_tag": "snow_cm",
                                              "tmk": "temp_avg_c", "txk": "temp_max_c",
                                              "tnk": "temp_min_c", "tgk": "groundtemp_min_c",
                                              "nm": "cloudcover_mean", "vpm": "vaporpressure_hpa",
                                              "pm": "airpressure_hps", "upm": "humidity_avg_percent",
                                              "fx": "wind_max_ms", "fm": "wind_avg_ms"})
            
        except requests.exceptions.RequestException as e:
            logger.warning(e)
            continue

        try:
            if sqlalchemy.inspect(engine).has_table("weather", schema="public"):
                with engine.connect() as con:
                    rs = con.execute('select "date" from public.weather')
                    indices = [idx[0] for idx in rs]
                    weather = weather[~weather.date.isin(indices)]
                    if len(weather) > 10 or len(weather) == 0:
                        logger.info(f"Got {len(weather)} new entries")
                    else:
                        logger.info(f"Got {len(weather)} new entries: {weather.date}")
                weather = weather.drop(columns=["eor"])
            weather.to_sql("weather", engine, if_exists="append", schema="public", index=False)

            with engine.connect() as con:
                con.execute('REFRESH MATERIALIZED VIEW public.weather_14d_agg')
            logger.info(f"Updated materialized view weather_14d_agg")
        except Exception as e:
            logger.error("Cannot write to weather:", e)
            exit(121)


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass

    # station_ID = 399 # Alex
    # station_ID = 433 # Tempelhof
    # station_ID = 422 # Mitte
