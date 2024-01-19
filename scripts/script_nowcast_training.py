#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_nowcast_training.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES] [--model_name]
  script_nowcast_training.py (-h | --help)
Options:
  --config_file=CONFIG_FILE           Directory for config file [default: models/model.yml]
  --db_qtrees=DB_QTREES               Database name [default:]
  --model_name                        Decided which trained model to use
"""
import pandas as pd
from sqlalchemy import create_engine
import sys
from docopt import docopt, DocoptExit
from sklearn.ensemble import RandomForestRegressor
import pickle
from qtrees.helper import get_logger, init_db_args
import os
from qtrees.constants import NOWCAST_FEATURES, HYPER_PARAMETERS_NC, PATH_TO_MODELS, MODEL_PREFIX, MODEL_TYPE
from qtrees.data_processor import PreprocessorNowcast, DataLoader

logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )
    if args["--model_name"] is not None:
        prefix = args["--model_name"]
    else:
        prefix = MODEL_PREFIX
    enc = DataLoader(engine, logger) #Downloads data
    logger.info("Generate nowcast training data")
    train_data = enc.download_training_data(forecast=False)
    train_data = train_data[NOWCAST_FEATURES + ["type_id", "site_id", "tree_id", "timestamp", "value"]]
    logger.info("Transforming nowcast training data")
    prep_nowcast = PreprocessorNowcast()
    prep_nowcast.fit(train_data)
    logger.info("Transform nowcast training data")
    train_data = prep_nowcast.transform_train(train_data)
    train_data = train_data.drop(columns="site_id")
    train_data = train_data.dropna()
    logger.info(train_data.shape)

    path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["nowcast"], "")
    if not os.path.exists(path):
        os.makedirs(path)
    prep_path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["preprocessor"], "")
    if not os.path.exists(prep_path):
        os.makedirs(prep_path)

    logger.info("Start model training for each depth.")
    for type_id in [1, 2, 3]:
        X = train_data.loc[train_data.type_id == type_id, NOWCAST_FEATURES]
        y = train_data.loc[train_data.type_id == type_id, "target"]
        model = RandomForestRegressor(**HYPER_PARAMETERS_NC)
        model.fit(X, y)
        pickle.dump(model, open(path + prefix + f'model_{type_id}.m', 'wb'))
    pickle.dump(prep_nowcast, open(prep_path + f"{MODEL_TYPE['preprocessor']}_{MODEL_TYPE['nowcast']}.pkl", 'wb'))
    logger.info("Trained all models.")

if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
