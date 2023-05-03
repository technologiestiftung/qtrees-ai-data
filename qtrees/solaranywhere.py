import requests
import pandas as pd
import time
import json

VARIABLE_MAP = {
    'GlobalHorizontalIrradiance_WattsPerMeterSquared': 'ghi',
    'DirectNormalIrradiance_WattsPerMeterSquared': 'dni',
    'DiffuseHorizontalIrradiance_WattsPerMeterSquared': 'dhi',
    'AmbientTemperature_DegreesC': 'temp',
    'WindSpeed_MetersPerSecond': 'wind',
    "LiquidPrecipitation_KilogramsPerMeterSquared": 'rainfall_mm'
}

URL = 'https://service.solaranywhere.com/api/v2'

def get_weather(latitude, longitude, api_key, start=None, end=None, hindcast=False, max_response_time=300):
    header = {'content-type': "application/json; charset=utf-8",
               'X-Api-Key': api_key,
               'Accept': "application/json"}

    payload = {
        "Sites": [{
            "Latitude": latitude,
            "Longitude": longitude
        }],
        "Options": {
            "OutputFields": ['StartTime'] + list(VARIABLE_MAP.keys()),
            "SummaryOutputFields": [],
            "SpatialResolution_Degrees": 0.1, # as per our license
            "TimeResolution_Minutes": 60, # as per our license
            "WeatherDataSource": 'SolarAnywhereLatest' if not hindcast else "SolarAnywhereHindcast", 
            "MissingDataHandling": "FillAverage",
        }
    }

    if (start is not None) or (end is not None):
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        print(start, end)
        if start.tz is None:
            start = start.tz_localize('CET')
        if end.tz is None:
            end = end.tz_localize('CET')
        end += pd.Timedelta("1D")
        payload['Options']["StartTime"] = start.isoformat()
        payload['Options']["EndTime"] = end.isoformat()
        print(start.isoformat(), end.isoformat())

    payload = json.dumps(payload)
    request = requests.post(URL+'/WeatherData', data=payload, headers=header)
    if request.ok is False:
        raise ValueError(request.json()['Message'])
    weather_request_id = request.json()["WeatherRequestId"]

    # Second request, to get the data async
    start_time = time.time()  
    while True:
        results = requests.get(URL + '/WeatherDataResult/' + weather_request_id, headers=header)
        results_json = results.json()
        if results_json.get('Status') == 'Done':
            if results_json['WeatherDataResults'][0]['Status'] == 'Failure':
                raise RuntimeError(results_json['WeatherDataResults'][0]['ErrorMessages'][0]['Message'])
            break
        elif (time.time()-start_time) > max_response_time:
            raise TimeoutError('Time exceeded the `max_response_time`.')
        time.sleep(5)  # Sleep for 5 seconds before each data retrieval attempt


    data = pd.DataFrame(results_json['WeatherDataResults'][0]['WeatherDataPeriods']['WeatherDataPeriods'])
    data.index = pd.to_datetime(data['StartTime'])
    data.index = data.index.tz_convert("CET")
    data = data.drop(["StartTime"], axis=1).rename(columns=VARIABLE_MAP)

    print(data)

 
    daily_frames = []
    daily_frames.append(data.groupby(data.index.date).max().rename(columns={"ghi": "ghi_max_wm2", "dni": "dni_max_wm2", "dhi": "dhi_max_wm2", "temp": "temp_max_c", "wind": "wind_max_ms"}))
    daily_frames.append(data[["ghi", "dni", "dhi", "rainfall_mm"]].groupby(data.index.date).sum().rename(columns={"ghi": "ghi_sum_whm2", "dni": "dni_sum_whm2", "dhi": "dhi_sum_whm2"}))
    daily_frames.append(data[["temp", "wind"]].groupby(data.index.date).mean().rename(columns={"temp": "temp_avg_c", "wind": "wind_avg_ms"}))
    data_daily = pd.concat(daily_frames, axis=1).reset_index().rename(columns={"index": "date"})
    return data_daily