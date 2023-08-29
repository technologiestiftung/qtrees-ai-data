#!/usr/bin/env python3
"""
Download solaranyhwere data and store into db.
Usage:
  script_store_solanywhere_weather_in_db.py [--db_qtrees=DB_QTREES] [--days=DAYS] [--start_date=start_date]
  script_store_solanywhere_weather_in_db.py (-h | --help)
Options:
  --db_qtrees=DB_QTREES                    Database name [default:]
  --days=DAYS                              Number of days to retrieve if no data in db [default: 14]
  --start_date=<start_date>                     Start date in YYYY-MM-DD format. If provided, days will not be used.
"""
import warnings

from sqlalchemy import create_engine
import sqlalchemy
import datetime
import pandas as pd
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
import os.path
import sys
from qtrees.solaranywhere import get_weather
import pytz

logger = get_logger(__name__)
warnings.filterwarnings('ignore')

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    api_key = os.getenv("SOLARANYWHERE_API_KEY")
    if api_key is None:
        logger.error("Environment variable SOLARANYWHERE_API_KEY not set")
        exit(2)
   
    # specific args
    days = int(args["--days"])

    if args["--start_date"]:
        start_date = datetime.datetime.strptime(args["--start_date"], '%Y-%m-%d')
    else: 
        start_date = None

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    with engine.connect() as con:
        rs = con.execute('select id, lat, lng from private.weather_tiles')
        locations = [idx for idx in rs]
        logger.debug("Retrieved data for %s locations!", len(locations))


    for loc in locations:
        logger.debug("Data for location with id=%s and coordinates (%s, %s)", loc[0], loc[1], loc[2])
        # write data to db
        try:
            today_local = datetime.date.today()

            last_date = None
            if sqlalchemy.inspect(engine).has_table("weather_tile_measurement", schema="private"):
                with engine.connect() as con:
                    rs = con.execute('select MAX("date") from private.weather_tile_measurement WHERE tile_id=%s' % loc[0])
                    last_date = [idx[0] for idx in rs][0]
                    logger.debug("Latest timestamp in data: %s.", last_date)
 
            if last_date is None:
                last_date = today_local - datetime.timedelta(days=days)
            
            yesterday = today_local - pd.Timedelta(days=1)
            if last_date >= yesterday:
                logger.info("Last available data from %s. No need to update!", last_date)
            else:
                if last_date is None and start_date is None:
                    start = today_local - datetime.timedelta(days=days)+datetime.timedelta(days=1)
                elif start_date is None and last_date:
                    start = last_date.date()
                else: 
                    start = start_date

                logger.info("Inserting data from %s to %s.", start, yesterday)
                weather_data  = get_weather(loc[1], loc[2], api_key, start=start, end=yesterday+datetime.timedelta(days=1))
                weather_data["tile_id"] = loc[0]
                weather_data.to_sql("weather_tile_measurement", engine, if_exists="append", schema="private", index=False, method='multi')
                
                logger.info(f"Updating materialized views...")
                with engine.connect() as con:
                    con.execute('REFRESH MATERIALIZED VIEW private.weather_solaranywhere_14d_agg')
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
