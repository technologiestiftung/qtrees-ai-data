#!/usr/bin/env python3
"""
Integrate csv file of baumscheiben radius into trees db.
Usage:
  script_store_baumscheiben_in_db.py [--data_directory=DATA_DIRECTORY] [--db_qtrees=DB_QTREES] [--yes=True]
  script_store_baumscheiben_in_db.py (-h | --help)
Options:
  --data_directory=DATA_DIRECTORY              Directory for data [default: data/trees]
  --db_qtrees=DB_QTREES                        Database name [default:]
  --yes=True                                   Run without inputs
"""

import sys
import sqlalchemy
from sqlalchemy import create_engine
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
import os.path
import pandas as pd

logger = get_logger(__name__, log_level="INFO")


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    logger.debug("Init db args")
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)
    data_directory = args["--data_directory"]
    yes = args["--yes"]
    logger.debug("Create db engine")
    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    logger.debug("Check if data already exists")
    if sqlalchemy.inspect(engine).has_table("trees", schema="public"):
        with engine.connect() as con:
            rs = con.execute('select COUNT(baumscheibe) from public.trees')
            count = [idx[0] for idx in rs][0]

        if count > 0:
            logger.warning("Already %s baumscheiben in database.", count)
            if yes == False:
                cont = input ('Continue? (y/n)')
                if cont == "n":
                    return

    logger.debug("Read csv file from path")
    baumscheiben_file = os.path.join(data_directory, "baumscheiben.csv")
    bs_df = pd.read_csv(baumscheiben_file)
    bs_df = bs_df.rename(columns = {"Baumscheibe_in_m²":"baumscheibe"})
    bs_df = bs_df[["BaumID","baumscheibe"]].dropna()

    query = """UPDATE public.trees 
        SET baumscheibe = %(baumscheibe)s
        WHERE id = %(id)s"""
    with engine.connect() as con:
        con.exec_driver_sql(query,[{"id":bs_df.iloc[i,0],"baumscheibe":bs_df.iloc[i,1]} for i in range(bs_df.shape[0])])
        rs = con.execute('SELECT COUNT(baumscheibe) from public.trees')
        count = [idx[0] for idx in rs][0]
    logger.info(f"Now, %s baumscheiben in database.", count)


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
