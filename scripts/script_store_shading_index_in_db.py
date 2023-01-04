#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_store_trees_in_db.py [--shadow_index_file=SHADOW_INDEX_FILE] [--db_qtrees=DB_QTREES]
  script_store_trees_in_db.py (-h | --help)
Options:
  --shadow_index_file=SHADOW_INDEX_FILE           Directory for data [default: data/shading/berlin_shadow_index.csv]
  --db_qtrees=DB_QTREES                           Database name [default:]
"""
from sqlalchemy import create_engine, inspect
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
from qtrees.shading_index import get_sunindex_df
import pandas as pd
import sys

logger = get_logger(__name__)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(args, logger)

    shadow_index_file = args["--shadow_index_file"]

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    logger.debug("Prepare shading index")
    sunindex_df = get_sunindex_df(shadow_index_file)

    with engine.connect() as con:
        result = con.execute('select id from api.trees')
        trees = [t[0] for t in list(result.fetchall())]

    sunindex_df_long = pd.melt(sunindex_df, ignore_index=False, value_vars=["spring", "summer", "autumn", "winter"],
                               value_name="index", var_name="month") \
        .replace({"month": {"spring": 3, "summer": 6, "autumn": 9, "winter": 12, }}) \
        .reset_index().rename(columns={"level_0": "tree_id"})

    sunindex_df_long = sunindex_df_long[sunindex_df_long.tree_id.isin(trees)]
    
    logger.info("Writing into db")
    try:
        if inspect(engine).has_table("shading", schema="public"):
            with engine.connect() as con:
                result = con.execute('TRUNCATE TABLE api.shading CASCADE')

        sunindex_df_long.to_sql("shading", engine, if_exists="append", schema="api", index=False)

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
