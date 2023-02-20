#!/usr/bin/env python3
"""
Download solaranyhwere data and store into db.
Usage:
  script_store_solanywhere_weather_in_db.py [--db_qtrees=DB_QTREES] [--days=DAYS]
  script_store_solanywhere_weather_in_db.py (-h | --help)
Options:
  --db_qtrees=DB_QTREES                    Database name [default:]
  --days=DAYS                              Number of days to retrieve if no data in db [default: 14]
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
            now = datetime.date.today()

            last_date = None
            if sqlalchemy.inspect(engine).has_table("weather_tile_measurement", schema="private"):
                with engine.connect() as con:
                    rs = con.execute('select MAX("date") from private.weather_tile_measurement WHERE tile_id=%s' % loc[0])
                    last_date = [idx[0] for idx in rs][0]
                    logger.debug("Latest timestamp in data: %s.", last_date)
 
            if last_date is None:
                last_date = now - datetime.timedelta(days=days)
            
            yesterday = now - pd.Timedelta(days=1)
            if last_date >= yesterday:
                logger.info("Last available data from %s. No need to update!", last_date)
            else:
                logger.info("Inserting data from %s to %s.", last_date, yesterday)
                weather_data  = get_weather(loc[1], loc[2], api_key, start=last_date, end=yesterday)
                weather_data["tile_id"] = loc[0]
                weather_data.to_sql("weather_tile_measurement", engine, if_exists="append", schema="private", index=False)
                
                #logger.info(f"Updating materialized views...")
                #with engine.connect() as con:
                    # TODO add views if used. 
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
