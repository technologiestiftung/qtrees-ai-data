#!/usr/bin/env python3
"""
Download GdK watering data, aggregate and store into db.
Usage:
  script_store_gdk_watering_in_db.py [--db_qtrees=DB_QTREES] [--db_gdk=DB_GDK]
  script_store_gdk_watering_in_db.py (-h | --help)
Options:
  --db_qtrees=DB_QTREES                        Database name qtrees [default:]
  --db_gdk=DB_GDK                              Database name GdK [default:]
"""
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
import sys

logger = get_logger(__name__)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)

    # default start date (if not data is available)
    last_date = '2021-12-31'
    try:
        db_qtrees, passwd_qtrees = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)
        engine_qtrees = create_engine(
            f"postgresql://postgres:{passwd_qtrees}@{db_qtrees}:5432/qtrees"
        )

        if sqlalchemy.inspect(engine_qtrees).has_table("watering_gdk", schema="private"):
            with engine_qtrees.connect() as con:
                # re-compute aggregation of last 14 days as new data might be available
                con.execute("delete from private.watering_gdk"
                            " where private.watering_gdk.date >= cast(now() as date) - interval '14 days'")
                rs = con.execute('select MAX("date") from private.watering_gdk')
                cur_date = rs.first()[0]
                if cur_date is None:
                    logger.info(f"No data so far. Starting from: {last_date}")
                else:
                    last_date = cur_date
                    logger.debug("Latest date in data: %s. Continue from here.", last_date)

    except Exception as e:
        logger.error("Cannot access db: %s", e)
        exit(121)

    try:
        db_gdk, passwd_gdk = init_db_args(db=args["--db_gdk"], db_type="gdk", logger=logger)
        engine_gdk = create_engine(
            f"postgresql://qtrees_readonly:{passwd_gdk}@{db_gdk}:5432/postgres"
        )

        with engine_gdk.connect() as con:
            # get watering data from GdK
            pd_watering = pd.read_sql("SELECT trees.gmlid, trees_watered.amount, trees_watered.timestamp"
                                      " FROM"
                                      " trees"
                                      " JOIN trees_watered ON trees.id = trees_watered.tree_id"
                                      f" WHERE cast(trees_watered.timestamp as date) > '{last_date}';",
                                      con)
        if len(pd_watering) > 0:
            pd_watering.rename(columns={"gmlid": "tree_id", "timestamp": "date"}, inplace=True)
            # aggregate watering day- and tree-wise
            pd_agg = pd_watering.groupby([pd_watering.date.dt.date, pd_watering.tree_id]).sum(
                numeric_only=True).reset_index()
            # write aggregated data to qtrees db
            logger.info("Writing/updating %s new watering data", len(pd_watering))
            pd_agg.to_sql("watering_gdk", engine_qtrees, if_exists="append", schema="private", index=False)
        else:
            logger.info("No update available for watering data")
    except Exception as e:
        logger.error("Cannot access db: %s", e)
        exit(121)


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
