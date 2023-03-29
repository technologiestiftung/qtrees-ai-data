#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_nowcast_inference.py [--config_file=CONFIG_FILE] [--db_qtrees=DB_QTREES] [--batch_size=BATCH_SIZE]
  script_nowcast_inference.py (-h | --help)
Options:
  --config_file=CONFIG_FILE           Directory for config file [default: models/model.yml]
  --db_qtrees=DB_QTREES               Database name [default:]
  --batch_size=BATCH_SiZE                      Batch size [default: 100000]
"""
import pandas as pd
from sqlalchemy import create_engine
import sys
from docopt import docopt, DocoptExit
import pickle
from qtrees.helper import get_logger, init_db_args
import datetime

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

    # TODO put into some config where also the model is configured (YAML? Database?)
    FEATURES = ["shading_winter", "shading_spring", "shading_summer", "shading_fall", "tree_standalter", "weather_rainfall_mm_14d_sum", "weather_temp_avg_c_14d_avg", "sensor_group_median"]
    
    with engine.connect() as con:
        rs = con.execute('select max(date) FROM private.weather_solaranywhere_14d_agg')
        result = [r[0] for r in rs][0]
        if result:
            last_weather_date = result
            logger.debug("Last weather data from: %s.", last_weather_date)
        else:
            logger.error("There is not weather data available for the model. Please insert weather data into the database.")
            return

        rs = con.execute('select max(timestamp) FROM private.sensor_measurements_agg')
        result = [r[0] for r in rs][0]
        if result:
            last_sensor_date = datetime.datetime.strptime(result, "%Y-%m-%d").date()
            logger.debug("Last sensor data from: %s.", last_sensor_date)
        else:
            logger.error("There is not sensor data available for the model. Please insert sensor data into the database.")
            return

        yesterday = datetime.date.today()-pd.Timedelta("1D")
        if (last_weather_date < yesterday) or (last_sensor_date < yesterday):
            nowcast_date = min(last_sensor_date, last_weather_date)
            logger.info("No up-to-date data. Creating nowcast based on data from: %s.", nowcast_date)
        else:
            nowcast_date = yesterday
            logger.info("Creating nowcast for yesterday: %s.", nowcast_date)

    logger.info("Start prediction for each depth.")
    for type_id in [1, 2, 3]:
        model = pickle.load(open(f'./models/simplemodel/model_{type_id}.m', 'rb'))
        for input_chunk in pd.read_sql("SELECT * FROM nowcast_input(%s, %s)", engine, params=(nowcast_date, type_id), chunksize=batch_size):
            X = input_chunk[FEATURES+["tree_id"]].set_index("tree_id").dropna()

            # TODO read model config from yaml?
            y_hat = pd.DataFrame(model.predict(X), index=X.index).reset_index()
            y_hat.columns = ["tree_id", "value"]
            y_hat["type_id"] = type_id
            y_hat["timestamp"] = yesterday
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
