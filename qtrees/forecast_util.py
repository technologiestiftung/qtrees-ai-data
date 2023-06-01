from qtrees.helper import get_logger
import datetime
import pytz
import pandas as pd

logger = get_logger(__name__)


def _check_datetime(value):
    if isinstance(value, str):
        output = pytz.timezone("CET").localize(datetime.datetime.strptime(value, "%Y-%m-%d")).date()
    elif isinstance(value, datetime.datetime):
        output = value.date()
    elif isinstance(value, datetime.date):  
        output = value
    else:
        logger.error("Result is neither str nor datetime, but of type %s.", type(value))
        output = None
    return output

def check_last_data(engine):
    with engine.connect() as con:
        rs = con.execute('select max(date) FROM private.weather_solaranywhere_14d_agg')
        result = [r[0] for r in rs][0]
        if result:
            last_weather_date = _check_datetime(result)
            logger.debug("Last weather data from: %s.", last_weather_date)
        else:
            logger.error("There is not weather data available for the model. "
                         "Please insert weather data into the database.")
            return

        rs = con.execute('select max(timestamp) FROM private.sensor_measurements_agg')
        result = [r[0] for r in rs][0]
        if result:
            last_sensor_date = _check_datetime(result)
            logger.debug("Last sensor data from: %s.", last_sensor_date)
        else:
            logger.error("There is not sensor data available for the model. "
                         "Please insert sensor data into the database.")
            return

    yesterday = datetime.date.today()-pd.Timedelta("1D")
    if (last_weather_date < yesterday) or (last_sensor_date < yesterday):
        nowcast_date = min(last_sensor_date, last_weather_date)
        logger.info("No up-to-date data. Creating nowcast based on data from: %s.", nowcast_date)
    else:
        nowcast_date = yesterday
        logger.info("Creating nowcast for yesterday: %s.", nowcast_date)

    return nowcast_date