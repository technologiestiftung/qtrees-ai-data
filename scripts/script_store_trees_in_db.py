#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_store_trees_in_db.py [--data_directory=DATA_DIRECTORY] [--db_qtrees=DB_QTREES] [--batch_size=BATCH_SIZE]
  script_store_trees_in_db.py (-h | --help)
Options:
  --data_directory=DATA_DIRECTORY              Directory for data [default: data/trees]
  --db_qtrees=DB_QTREES                        Database name [default:]
  --batch_size=BATCH_SiZE                      Batch size [default: 100000]
"""

import sys
import sqlalchemy
from sqlalchemy import create_engine
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
from qtrees.fisbroker import store_trees_batchwise_to_db, download_tree_file
import os.path
import pytz

logger = get_logger(__name__, log_level="INFO")


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    logger.debug("Init db args")
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    data_directory = args["--data_directory"]
    n_batch_size = int(args["--batch_size"])

    logger.debug("Create db engine")
    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    logger.debug("Check if data already exists")
    if sqlalchemy.inspect(engine).has_table("trees", schema="public"):
        with engine.connect() as con:
            rs = con.execute('select COUNT(id) from public.trees')
            count = [idx[0] for idx in rs][0]
        if count > 0:
            logger.warning("Already %s trees in database. Skipping...", count)
            return

    logger.debug("Do update")
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    # download tree files in case of need
    filename_street_trees = download_tree_file(
        dir_data=data_directory, type="wfs_baumbestand", use_cached=True)
    filename_anlage_trees = download_tree_file(
        dir_data=data_directory, type="wfs_baumbestand_an", use_cached=True)

    # process tree files batchwise
    lu_ids = store_trees_batchwise_to_db(
        trees_file=filename_street_trees, street_tree=True, engine=engine,
        n_batch_size=n_batch_size)
    store_trees_batchwise_to_db(
        trees_file=filename_anlage_trees, street_tree=False, engine=engine,
        n_batch_size=n_batch_size, lu_ids=lu_ids)

    with engine.connect() as con:
        rs = con.execute('select COUNT(id) from public.trees')
        count = [idx[0] for idx in rs][0]
    logger.info(f"Now, %s trees in database.", count)


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
