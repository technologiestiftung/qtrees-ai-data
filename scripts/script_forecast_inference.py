#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_forecast_inference.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES] [--batch_size=BATCH_SIZE]
  script_forecast_inference.py (-h | --help)
Options:
  --config_file=CONFIG_FILE           Directory for config file [default: models/model.yml]
  --db_qtrees=DB_QTREES               Database name [default:]
  --batch_size=BATCH_SiZE                      Batch size [default: 100000]
"""
import sys
import os
import pickle
import datetime
import pytz
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from docopt import docopt, DocoptExit

from qtrees.helper import get_logger, init_db_args
from qtrees.constants import FORECAST_FEATURES, PREPROCESSING_HYPERPARAMS, MODEL_PREFIX, MODEL_TYPE, PATH_TO_MODELS
from qtrees.data_processor import DataLoader


logger = get_logger(__name__)

def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    batch_size = int(args["--batch_size"])
    db_qtrees, postgres_passwd = init_db_args(db=args["--db_qtrees"], db_type="qtrees", logger=logger)

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )
    last_date = pd.read_sql("SELECT MAX(date) FROM private.weather_tile_measurement", con=engine.connect()).astype('datetime64[ns, UTC]').iloc[0, 0]
    num_trees = pd.read_sql("SELECT COUNT(*) FROM public.trees WHERE street_tree = true", con=engine.connect()).iloc[0, 0]
    # TODO something smarter here?
    with engine.connect() as con:
        con.execute("TRUNCATE public.forecast")

    created_at = datetime.datetime.now(pytz.timezone('UTC'))
    weather_cols = [x for x in ["wind_avg_ms", "wind_max_ms", "temp_avg_c", "temp_max_c", "rainfall_mm", "ghi_sum_whm2"] if x in FORECAST_FEATURES]
    loader = DataLoader(engine, logger)
    model_path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["forecast"], "")
    prep_path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["preprocessor"], "")
    aux_path = aux_path = os.path.join(PATH_TO_MODELS, MODEL_TYPE["auxiliary"], "")

    preprocessor = pickle.load(open(prep_path + f"{MODEL_TYPE['preprocessor']}_{MODEL_TYPE['forecast']}.pkl", 'rb'))

    logger.info("Start prediction for each depth")
    for batch_number in range(int(np.ceil(num_trees/batch_size))):
        input_chunk = loader.download_forecast_inference_data(date=last_date, batch_size=batch_size, batch_num=batch_number)
        input_chunk = preprocessor.transform_inference(input_chunk)
        base_X = input_chunk.reset_index(level=1, drop=True)  # Drop date index (this is only one value anyway)
        base_X = base_X[[x for x in base_X.columns if x in FORECAST_FEATURES]]
        base_X = base_X.dropna()
        for type_id in [1, 2, 3]:
            aux_model = pickle.load(open(aux_path + MODEL_PREFIX + f"model_{type_id}.m", 'rb'))
            model = pickle.load(open(model_path + MODEL_PREFIX + f"model_{type_id}.m", 'rb'))
            # generate autoregressive features for the last 3 days
            if base_X.shape[0] == 0:
                continue
            autoreg_features = None
            for i in range(PREPROCESSING_HYPERPARAMS["autoreg_lag"]):
                X = base_X.copy()
                hist_date = last_date - pd.Timedelta(days=i)
                current_weather = pd.read_sql("SELECT * FROM private.weather_tile_measurement WHERE date = %s AND tile_id = %s ORDER BY date DESC", 
                                              engine, params=(hist_date, PREPROCESSING_HYPERPARAMS['tile_id']))
                current_weather = current_weather[weather_cols]
                for col in weather_cols:
                    X.loc[:, col] = current_weather.loc[:, col].values[0]
                if autoreg_features is None:
                    autoreg_features = pd.DataFrame(aux_model.predict(X), index=X.index)
                    autoreg_features.columns = [f"shift_{i+1}"]
                else:
                    autoreg_features.loc[:, f"shift_{i+1}"] = aux_model.predict(X)

            logger.info(f"Inference for depth {type_id}, batch {batch_number+1}/{int(np.ceil(num_trees/batch_size))}.")
            for h in range(1, PREPROCESSING_HYPERPARAMS["fc_horizon"]+1):
                forecast_date = last_date + pd.Timedelta(days=h)
                current_weather = pd.read_sql("SELECT * FROM private.weather_tile_forecast WHERE date = %s AND tile_id = %s ORDER BY date, created_at DESC", 
                                              engine, params=(forecast_date, PREPROCESSING_HYPERPARAMS['tile_id']))
                current_weather = current_weather[weather_cols]
                X = base_X.copy()
                X = X.merge(autoreg_features, how="left", left_index=True, right_index=True)
                for col in weather_cols:
                    X.loc[:, col] = current_weather.loc[:, col].values[0]
                X = X[FORECAST_FEATURES + ["shift_1", "shift_2", "shift_3"]]
                y_hat = pd.DataFrame(model.predict(X), index=X.index).reset_index()
                y_hat.columns = ["tree_id", "value"]
                y_hat["type_id"] = type_id
                y_hat["timestamp"] = forecast_date
                y_hat["created_at"] = created_at
                y_hat["model_id"] = "Random Forest (full)" # TODO id from file?
                temp = pd.DataFrame({"shift_1": y_hat.set_index("tree_id")["value"], "shift_2": autoreg_features["shift_1"], "shift_3": autoreg_features["shift_2"]}, index=y_hat["tree_id"])
                autoreg_features = temp
                try:
                    y_hat.to_sql("forecast", engine, if_exists="append", schema="public", index=False, method=None)
                except:
                    logger.error("Forecast failed for chunk. Trying to continue for next chunk.")

    logger.info("Made all predictions all models.")

    logger.info("Calculating Mean Prediction.")
    with engine.connect() as con:
        con.execute("INSERT INTO public.forecast SELECT nextval('forecast_id_seq'), tree_id, 4 as type_id, timestamp, avg(value), created_at, model_id " +
                    "FROM public.forecast " +
                    "WHERE created_at = %(created)s GROUP BY tree_id, timestamp, created_at, model_id;", created=created_at)

    with engine.connect() as con:
        con.execute('REFRESH MATERIALIZED VIEW public.expert_dashboard')
        con.execute('REFRESH MATERIALIZED VIEW public.expert_dashboard_large')
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
