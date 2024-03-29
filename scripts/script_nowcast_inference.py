#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_nowcast_inference.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES] [--batch_size=BATCH_SIZE] [--model_prefix=MODEL_PREFIX]
  script_nowcast_inference.py (-h | --help)
Options:
  --config_file=CONFIG_FILE           Directory for config file [default: models/model.yml]
  --db_qtrees=DB_QTREES               Database name [default:]
  --batch_size=BATCH_SiZE             Batch size [default: 100000]
  --model_name                        Decided which trained model to use
"""
import sys
import os
import datetime
import pytz
import pickle
from docopt import docopt, DocoptExit
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

from qtrees.helper import get_logger, init_db_args
from qtrees.forecast_util import check_last_data
from qtrees.constants import NOWCAST_FEATURES, PATH_TO_MODELS, MODEL_TYPE, MODEL_PREFIX
from qtrees.data_processor import DataLoader

logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    batch_size = int(args["--batch_size"])
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)
    if args["--model_name"] is not None:
        prefix = args["--model_name"]
    else:
        prefix = MODEL_PREFIX
    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )
    num_trees = pd.read_sql("SELECT COUNT(*) FROM public.trees WHERE street_tree = true", con=engine.connect()).iloc[0, 0]
    nowcast_date = pd.read_sql("SELECT MAX(date) FROM public.weather", con=engine.connect()).astype('datetime64[ns, UTC]').iloc[0, 0]
    loader = DataLoader(engine, logger)
    prep_path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["preprocessor"], f"{MODEL_TYPE['preprocessor']}_{MODEL_TYPE['nowcast']}.pkl")
    preprocessor = pickle.load(open(prep_path, 'rb'))
    # TODO something smarter here?
    with engine.connect() as con:
        con.execute("TRUNCATE public.nowcast")

    logger.info("Start prediction for each depth.")
    created_at = datetime.datetime.now(pytz.timezone('UTC'))
    for type_id in [1, 2, 3]:
        model_path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["nowcast"], prefix + f"model_{type_id}.m")
        model = pickle.load(open(model_path, 'rb'))
        for batch_number in range(int(np.ceil(num_trees/batch_size))):
            input_chunk = loader.download_nowcast_inference_data(date=nowcast_date, batch_size=batch_size, batch_num=batch_number)
            input_chunk = preprocessor.transform_inference(input_chunk)
            X = input_chunk[NOWCAST_FEATURES].reset_index(level=1, drop=True)  #Drop date index (this is only one value anyway)
            X = X.dropna()
            # TODO read model config from yaml?
            # TODO filter valid targets
            if X.shape[0] == 0:
                continue
            y_hat = pd.DataFrame(model.predict(X), index=X.index).reset_index()
            y_hat.columns = ["tree_id", "value"]
            y_hat["type_id"] = type_id
            y_hat["timestamp"] = nowcast_date
            y_hat["created_at"] = created_at
            y_hat["model_id"] = "Random Forest (full)"
            # TODO id from file?
            try:
                y_hat.to_sql("nowcast", engine, if_exists="append", schema="public", index=False, method=None)
            except Exception as e:
                logger.error(f"Nowcast failed for chunk. Trying to continue for next chunk. Error: %s", e)

    logger.info("Made all predictions all models.")

    logger.info("Calculating Mean Prediction.")
    with engine.connect() as con:
        con.execute("INSERT INTO public.nowcast SELECT nextval('nowcast_id_seq'), tree_id, 4 as type_id, timestamp, avg(value), created_at, model_id " + \
                    "FROM public.nowcast " + \
                    "WHERE created_at = %(created)s GROUP BY tree_id, timestamp, created_at, model_id;", created=created_at)
        
    logger.info("Updating materialized views.")
    with engine.connect() as con:
        con.execute('REFRESH MATERIALIZED VIEW public.expert_dashboard')
        con.execute("REFRESH MATERIALIZED VIEW public.vector_tiles;")
    logger.info("Updated materialized view public.expert_dashboard.")

if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
