#!/usr/bin/env python3
"""
Create Dummy Nowcast and Forecast in DB.
Usage:
  script_store_soil_in_db.py [--db_qtrees=DB_QTREES]
  script_store_soil_in_db.py (-h | --help)
Options:
  --db_qtrees=DB_QTREES                        Database name [default:]
"""
import os
from sqlalchemy import create_engine
import sqlalchemy
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
import sys
import pandas as pd
from datetime import datetime

import random

logger = get_logger(__name__)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    with engine.connect() as con:
        result = con.execute(
            "SELECT id FROM public.trees WHERE Street_tree = True and ((Bezirk = 'Mitte') OR (Bezirk = 'Neukölln'))")
        qtree_trees = [t[0] for t in list(result.fetchall())]
        con.execute("TRUNCATE public.forecast")

    logger.info(f"Creating forecasts for {len(qtree_trees)} trees")

    for tree in qtree_trees:
        for type_id in [1, 2, 3, 4]:
            with engine.connect() as con:
                rs = con.execute(
                    f"SELECT timestamp, value FROM public.nowcast n1 WHERE timestamp = (SELECT MAX(timestamp) FROM "
                    f"public.nowcast n2 WHERE n1.tree_id = n2.tree_id) AND n1.type_id = '{type_id}' "
                    f"AND n1.tree_id = '{tree}'")
                result = [t for t in list(rs.fetchall())]
                if result:
                    timestamp = result[0][0]
                    value = result[0][1]
                    for day in pd.date_range(start=timestamp, end=datetime.today()):
                        value += random.gauss(1, 0.5)
                        date_str = day.strftime("%m/%d/%Y")
                        con.execute(
                            f"INSERT INTO public.nowcast(tree_id, type_id, timestamp, value, created_at, "
                            f"model_id) VALUES ('{tree}', {type_id}, '{date_str}', {value}, '{date_str}', "
                            f"'Dummymodel');")
                else:
                    value = random.gauss(60, 10)
                    date_str = datetime.today().strftime("%m/%d/%Y")
                    con.execute(
                        f"INSERT INTO public.nowcast(tree_id, type_id, timestamp, value, created_at, model_id) "
                        f"VALUES ('{tree}', {type_id}, '{date_str}', {value}, '{date_str}', 'Dummymodel');")

                # and forecast
                for day in pd.date_range(start=datetime.today() + pd.Timedelta("1d"),
                                         end=datetime.today() + pd.Timedelta("15d")):
                    value += random.gauss(1, 0.5)
                    date_str = day.normalize().strftime("%m/%d/%Y")
                    con.execute(
                        f"INSERT INTO public.forecast(tree_id, type_id, timestamp, value, created_at, "
                        f"model_id) VALUES ('{tree}', {type_id}, '{date_str}', {value}, '{date_str}', 'Dummymodel');")

    # delete old entries on rolling basis
    with engine.connect() as con:
        con.execute("delete from public.nowcast where timestamp < now() - interval '2 days'")
        con.execute("REFRESH MATERIALIZED VIEW public.vector_tiles;")


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
