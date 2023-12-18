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
from qtrees.constants import FORECAST_FEATURES, HYPER_PARAMETERS_FC, HYPER_PARAMETERS_NC
from qtrees.data_processor import DataLoader, PreprocessorForecast

logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    loader = DataLoader(engine, logger)
    train_fc = loader.download_training_data(forecast=True)
    preprocessor_forecast = PreprocessorForecast()
    preprocessor_forecast.fit(train_fc)
    logger.info("Transform forecast training data")
    train_data = preprocessor_forecast.transform_train(train_fc)
    train_data = train_data.drop(columns="site_id")
    train_data = train_data.dropna()
    # TODO put into some config where also the model is configured (YAML?)
    if not os.path.exists('./models/fullmodel_forecast/'):
        os.makedirs('./models/fullmodel_forecast/')
    pickle.dump(preprocessor_forecast, open('./models/fullmodel_forecast/preprocessor_forecast.pkl', 'wb'))

    logger.info("Start model training for each depth.")
    for type_id in [1, 2, 3]:
        X = train_data.loc[train_data.type_id == type_id, FORECAST_FEATURES + ["shift_1", "shift_2", "shift_3"]]
        y = train_data.loc[train_data.type_id == type_id, "target"]
        model = RandomForestRegressor(**HYPER_PARAMETERS_FC)
        model.fit(X, y)

        # TODO read path from config
        pickle.dump(model, open(f'./models/fullmodel_forecast/forecast_model_{type_id}.m', 'wb'))
    logger.info("Trained forecast models.")

    logger.info("Start model training for auxiliary nowcast model.")
    for type_id in [1, 2, 3]:
        X = train_data.loc[train_data.type_id == type_id, FORECAST_FEATURES]
        y = train_data.loc[train_data.type_id == type_id, "target"] # TODO filter valid
        model_nc = RandomForestRegressor(**HYPER_PARAMETERS_NC)
        model_nc.fit(X, y)
        # TODO read path from config
        pickle.dump(model_nc, open(f'./models/fullmodel_forecast/auxiliary_model_{type_id}.m', 'wb'))
    logger.info("Trained all models")
if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
