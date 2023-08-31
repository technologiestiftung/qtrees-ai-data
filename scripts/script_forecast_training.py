#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_forecast_training.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES]
  script_forecast_training.py (-h | --help)
Options:
  --config_file=CONFIG_FILE           Directory for config file [default: models/model.yml]
  --db_qtrees=DB_QTREES               Database name [default:]
"""
import pandas as pd
from sqlalchemy import create_engine
import sys
from docopt import docopt, DocoptExit
from sklearn.ensemble import RandomForestRegressor
import pickle
from qtrees.helper import get_logger, init_db_args
import os
from qtrees.constants import FORECAST_FEATURES

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
        train_data = pd.read_sql('select * from private.forecast_training_data', con)
    train_data = train_data.dropna()

    # TODO put into some config where also the model is configured (YAML?)
    
    if not os.path.exists('./models/simplemodel_forecast/'):
        os.makedirs('./models/simplemodel_forecast/')

    logger.info("Start model training for each depth.")
    for type in [1, 2, 3]:
        X = train_data.loc[train_data.type_id == type, FORECAST_FEATURES]
        y = train_data.loc[train_data.type_id == type, "target"]
        model = RandomForestRegressor()
        model.fit(X, y)

        # TODO read path from config
        pickle.dump(model, open(f'./models/simplemodel_forecast/model_{type}.m', 'wb'))
    logger.info("Trained all models.")


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
