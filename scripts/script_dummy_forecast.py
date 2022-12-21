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
    db_qtrees, postgres_passwd = init_db_args(args, logger)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    with engine.connect() as con:
        result = con.execute("SELECT id FROM api.trees WHERE Street_tree = True and ((Bezirk = 'Mitte') OR (Bezirk = 'Neukölln'))")
        qtree_trees = [t[0] for t in list(result.fetchall())]

    logger.info(f"Creating forecasts for {len(qtree_trees)} trees")

    for tree in qtree_trees:
        for type_id in [1,2,3]:
            with engine.connect() as con:
                rs = con.execute(f"SELECT timestamp, value FROM api.nowcast n1 WHERE timestamp = (SELECT MAX(timestamp) FROM api.nowcast n2 WHERE n1.tree_id = n2.tree_id) AND n1.forecast_type_id = '{type_id}' AND n1.tree_id = '{tree}'")
                result = [t for t in list(rs.fetchall())]
                if result:
                    timestamp = result[0][0]
                    value = result[0][1]
                    for day in pd.date_range(start=timestamp,end=datetime.today()):
                        value += random.gauss(1, 0.5)
                        date_str = day.strftime("%m/%d/%Y")
                        rs = con.execute(f"INSERT INTO api.nowcast(tree_id, forecast_type_id, timestamp, value, created_at, model_id) VALUES ('{tree}', {type_id}, '{date_str}', {value}, '{date_str}', 'Dummymodel');")
                else:
                    value = random.gauss(60, 10)
                    date_str = datetime.today().strftime("%m/%d/%Y")
                    rs = con.execute(f"INSERT INTO api.nowcast(tree_id, forecast_type_id, timestamp, value, created_at, model_id) VALUES ('{tree}', {type_id}, '{date_str}', {value}, '{date_str}', 'Dummymodel');")
                
                # and forecast
                for day in pd.date_range(start=datetime.today()+pd.Timedelta("1d"),end=datetime.today()+pd.Timedelta("15d")):
                    value += random.gauss(1, 0.5)
                    date_str = day.normalize().strftime("%m/%d/%Y")
                    rs = con.execute(f"INSERT INTO api.forecast(tree_id, forecast_type_id, timestamp, value, created_at, model_id) VALUES ('{tree}', {type_id}, '{date_str}', {value}, '{date_str}', 'Dummymodel');")

    # delete old entries on rolling basis
    with engine.connect() as con:
        con.execute("delete from api.nowcast where timestamp < now() - interval '14 days'")
        con.execute("delete from api.forecast where timestamp < now() - interval '14 days'")


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
