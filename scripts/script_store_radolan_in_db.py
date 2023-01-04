#!/usr/bin/env python3
"""
Download radolan data and store into db.
Usage:
  script_store_radolan_in_db.py [--db_qtrees=DB_QTREES] [--days=DAYS] [--path_to_bezirke=PATH_TO_BEZIRKE]
  script_store_radolan_in_db.py (-h | --help)
Options:
  --db_qtrees=DB_QTREES                    Database name [default:]
  --days=DAYS                              Number of days to retrieve if no data in db [default: 14]
  --path_to_bezirke=PATH_TO_BEZIRKE        Path to Geojson of Berlin Bezirke [default: ./data/bezirksgrenzen.geojson]
"""
import warnings

from sqlalchemy import create_engine, inspect
import sqlalchemy
import datetime
import geopandas as gpd
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
from qtrees.dwd import get_radolan_data
import os.path
import sys

logger = get_logger(__name__)
warnings.filterwarnings('ignore')


def get_bezirksgrenzen(file_geojson):
    import requests

    url = "https://tsb-opendata.s3.eu-central-1.amazonaws.com/bezirksgrenzen/bezirksgrenzen.geojson"
    response = requests.get(url, stream=True)

    with open(file_geojson, "wb") as handle:
        for data in response.iter_content():
            handle.write(data)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(args, logger)

    # specific args
    print(args)
    days = int(args["--days"])
    path_to_bezirke = args["--path_to_bezirke"]

    if not os.path.exists(path_to_bezirke):
        get_bezirksgrenzen(path_to_bezirke)

    berlin_mask = gpd.GeoDataFrame(
        geometry=[gpd.read_file(path_to_bezirke).geometry.unary_union], crs="EPSG:4326"  # bezirksgrenzen.geojson'
    )

    # write data to db
    try:
        engine = create_engine(
            f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
        )
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()

        last_date = None
        if sqlalchemy.inspect(engine).has_table("radolan", schema="public"):
            with engine.connect() as con:
                rs = con.execute('select MAX("timestamp") from public.radolan')
                last_date = [idx[0] for idx in rs][0]
                logger.debug("Latest timestamp in data: %s. Continue from here.", last_date)

        if last_date is None:
            last_date = now - datetime.timedelta(days=days)
            last_date = last_date.replace(minute=50, second=0, microsecond=0)
        else:
            last_date += delta

        first_iteration = True

        while last_date <= now:
            # hourly
            radolan = get_radolan_data(
                nowcast_date=last_date, mask=berlin_mask, xmin=600,
                xmax=700, ymin=700, ymax=800
            )
            if radolan is None:
                logger.info("Can't get radolan data for '%s'. Skipping...", last_date)
            else:
                radolan_gdf, meta_data = radolan
                radolan_gdf = radolan_gdf.drop(columns=["index_right"])
                radolan_gdf["timestamp"] = meta_data['datetime']
                radolan_gdf = radolan_gdf.reset_index()
                logger.debug("Storing radolan data for '%s'", meta_data['datetime'])

                if first_iteration:
                    with engine.connect() as con:
                        result = con.execute('select id from api.radolan_tiles')
                        tiles = [t[0] for t in list(result.fetchall())]
                    radolan_gdf_grid = radolan_gdf.rename(columns={"index": "id"})
                    radolan_gdf_grid = radolan_gdf_grid[~radolan_gdf_grid.id.isin(tiles)]
                    logger.debug(f"Storing {len(radolan_gdf_grid)} new tiles to the database.")
                    radolan_gdf_grid[["id", "geometry"]].to_postgis("radolan_tiles", engine, if_exists="append", schema="public")

                    first_iteration=False

                radolan_gdf = radolan_gdf.rename(columns={"index": "tile_id"})
                radolan_gdf[["tile_id", "timestamp", "rainfall_mm"]].to_sql("radolan", engine, if_exists="append", schema="public", index=False)

                break
            last_date += delta
    except Exception as e:
        logger.error("Cannot write to db: %s", e)
        exit(121)


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
