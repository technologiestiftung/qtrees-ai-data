#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_nowcast_inference.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES]
  script_nowcast_inference.py (-h | --help)
Options:
  --config_file=CONFIG_FILE           Directory for config file [default: models/model.yml]
  --db_qtrees=DB_QTREES               Database name [default:]
"""
import pandas as pd
from sqlalchemy import create_engine
import sys
from docopt import docopt, DocoptExit
import pickle
from qtrees.helper import get_logger, init_db_args
import os
import datetime

logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    # TODO put into some config where also the model is configured (YAML? Database?)
    FEATURES = ["winter", "spring", "summer", "fall", "standalter", "rainfall_mm_14d_sum", "temp_avg_c_14d_avg", "median_value"]
    
    logger.info("Start prediction for each depth.")
    for type in [1, 2, 3]:
        # TODO make this a function in database that returns table (or at least prepared statement)
        q = f"""(SELECT trees.id, {type} as type_id, date(now()::date - interval '1 d') as yesterday,
            shading.spring, shading.summer, shading.fall, shading.winter, trees.gattung_deutsch, trees.standalter,
            (select rainfall_mm_14d_sum FROM private.weather_solaranywhere_14d_agg WHERE date = date(now()::date - interval '1 d')),
            (select temp_avg_c_14d_avg FROM private.weather_solaranywhere_14d_agg WHERE date = date(now()::date - interval '1 d')),
            (select median_value FROM private.sensor_measurements_agg WHERE (date(sensor_measurements_agg.timestamp) = date(now()::date - interval '1 d')) AND sensor_measurements_agg.type_id = {type})
            FROM (SELECT * FROM public.trees WHERE trees.street_tree = True) AS trees LEFT JOIN public.shading ON shading.tree_id = trees.id)"""

        with engine.connect() as con:
            test_data = pd.read_sql(q, con)
        
        X = test_data[FEATURES+["id"]].set_index("id").dropna()

        # TODO error when not data (e.g. weather or sensor data is missing)

        # TODO read model config from yaml?
        model = pickle.load(open(f'./models/simplemodel/model_{type}.m', 'rb'))
        y_hat = pd.DataFrame(model.predict(X), index=X.index).reset_index()
        y_hat.columns = ["tree_id", "value"]
        y_hat["type_id"] = 1
        y_hat["timestamp"] = datetime.date.today() - pd.Timedelta("1D")
        y_hat["created_at"] = datetime.datetime.now()
        y_hat["model_id"] = "Random Forest (simple)" # TODO id from file?
        y_hat.to_sql("nowcast", engine, if_exists="append", schema="public", index=False, method='multi')
       
    logger.info("Made all predictions all models.")
    
        

    


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
