#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_store_trees_in_db.py [--shadow_index_file=SHADOW_INDEX_FILE] [--shadow_index_file_interpolated=SHADOW_INDEX_FILE] [--db_qtrees=DB_QTREES]
  script_store_trees_in_db.py (-h | --help)
Options:
  --shadow_index_file=SHADOW_INDEX_FILE           Directory for data [default: data/shading/berlin_shadow_index.csv]
  --shadow_index_file_interpolated=SHADOW_INDEX_FILE_INTERPOLATED     Directory for data [default: data/shading/berlin_shadow_index_interpolated.csv]
  --db_qtrees=DB_QTREES                           Database name [default:]
"""
from sqlalchemy import create_engine, inspect
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
from qtrees.shading_index import get_sunindex_df
import os.path
import pandas as pd
import sys

logger = get_logger(__name__)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    shadow_index_file = args["--shadow_index_file"]
    if not os.path.exists(shadow_index_file):
        logger.warning("Shadow index file '%s' does not exist", shadow_index_file)
        exit(128)

    shadow_index_file_interpolated = args["--shadow_index_file_interpolated"]
    if not os.path.exists(shadow_index_file_interpolated):
        logger.warning("Shadow index file '%s' does not exist", shadow_index_file_interpolated)
        exit(128)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    logger.debug("Prepare shading index")
    sunindex_df = get_sunindex_df(shadow_index_file).reset_index().rename(columns={"index": "tree_id", "autumn": "fall"})
    interpolated_sunindex_df = pd.read_csv(shadow_index_file_interpolated, index_col=0)
    interpolated_sunindex_df.columns = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    interpolated_sunindex_df = interpolated_sunindex_df.reset_index()

    with engine.connect() as con:
        result = con.execute('select id from public.trees')
        trees = [t[0] for t in list(result.fetchall())]

    sunindex_df = sunindex_df[sunindex_df.tree_id.isin(trees)]
    interpolated_sunindex_df = interpolated_sunindex_df[interpolated_sunindex_df.tree_id.isin(trees)]
    
    logger.info("Writing into db")
    try:
        if inspect(engine).has_table("shading", schema="public"):
            with engine.connect() as con:
                con.execute('TRUNCATE TABLE public.shading CASCADE')
                con.execute('TRUNCATE TABLE public.shading_monthly CASCADE')

        sunindex_df = sunindex_df.drop_duplicates(subset=['tree_id'], keep='first')
        interpolated_sunindex_df = interpolated_sunindex_df.drop_duplicates(subset=['tree_id'], keep='first')
        #sunindex_df.to_sql("shading", engine, if_exists="append", schema="public", index=False)
        
        interpolated_sunindex_df.to_sql("shading_monthly", engine, if_exists="append", schema="public", index=False)
        logger.info(f"Now, new %s shading entries in database.", len(sunindex_df))
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
