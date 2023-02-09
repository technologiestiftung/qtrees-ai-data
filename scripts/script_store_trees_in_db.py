#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_store_trees_in_db.py [--data_directory=DATA_DIRECTORY] [--db_qtrees=DB_QTREES]
  script_store_trees_in_db.py (-h | --help)
Options:
  --data_directory=DATA_DIRECTORY              Directory for data [default: data/trees]
  --db_qtrees=DB_QTREES                        Database name [default:]
"""

import sys
import sqlalchemy
from sqlalchemy import create_engine
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
from qtrees.fisbroker import get_trees
import os.path

logger = get_logger(__name__)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    logger.debug("Init db args")
    db_qtrees, postgres_passwd = init_db_args(args, logger)

    data_directory = args["--data_directory"]
    logger.debug("Create db engine")
    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    do_update = True
    logger.debug("Check if data already exists")
    if sqlalchemy.inspect(engine).has_table("trees", schema="public"):
        with engine.connect() as con:
            rs = con.execute('select COUNT(id) from public.trees')
            count = [idx[0] for idx in rs][0]
        if count > 0:
            logger.warning("Already %s trees in database. Skipping...", count)
            do_update = False

    if do_update:
        logger.debug("Do update")
        data_file = os.path.join(data_directory, "trees_gdf_all.geojson")
        joined_trees = get_trees(data_file)
        joined_trees = joined_trees.drop_duplicates(subset=['id'], keep='first')
        joined_trees['baumscheibe'] = ""
        logger.info("Writing into db")
        try:
            joined_trees.to_postgis("trees", engine, if_exists="append", schema="public")
            with engine.connect() as con:
                rs = con.execute('select COUNT(id) from public.trees')
                count = [idx[0] for idx in rs][0]
            logger.info(f"Now, %s trees in database.", count)
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
