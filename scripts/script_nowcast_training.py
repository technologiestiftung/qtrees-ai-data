#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_nowcast_training.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES]
  script_nowcast_training.py (-h | --help)
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
from qtrees.constants import NOWCAST_FEATURES, HYPER_PARAMETERS
from qtrees.data_processor import Preprocessor_Nowcast, Data_loader

logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    engine = create_engine(
        #f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
        f"postgresql://qtrees_user:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    enc = Data_loader(engine) #Downloads data
    logger.info("Generate nowcast training data")
    train_data = enc.download_nowcast_training_data()
    train_data = train_data[NOWCAST_FEATURES + ["type_id", "site_id", "tree_id", "timestamp", "value"]]
    prep_nowcast = Preprocessor_Nowcast()
    prep_nowcast.fit(train_data)
    logger.info("Transform nowcast training data")
    train_data = prep_nowcast.transform_train(train_data)
    train_data = train_data.drop(columns="site_id")
    train_data = train_data.dropna()

    if not os.path.exists('./models/fullmodel/'):
        os.makedirs('./models/fullmodel/')

    logger.info("Start model training for each depth.")
    for type in [1, 2, 3]:
        X = train_data.loc[train_data.type_id == type, NOWCAST_FEATURES]
        y = train_data.loc[train_data.type_id == type, "target"] # TODO filter valid
        model = RandomForestRegressor(**HYPER_PARAMETERS)
        model.fit(X, y)

        # TODO read path from config
        pickle.dump(model, open(f'./models/fullmodel/nowcast_model_{type}.m', 'wb'))
    pickle.dump(prep_nowcast, open('./models/fullmodel/preprocessor_nowcast.pkl', 'wb'))
    logger.info("Trained all models.")

if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
