import geopandas as gpd
import pandas as pd
import io
import requests
import gzip
import wradlib as wrl
from shapely.geometry import Polygon
import datetime
from zipfile import ZipFile
from requests.exceptions import RequestException
import pytz

def get_radolan_data(nowcast_date=None, aggregation="hourly", mask=None, xmin=0, xmax=900, ymin=0, ymax=900):
    """Gets the RADOLAN (Radar-Online-Aneichung) data of DWD

    Parameters
    ----------
    nowcast_date : datetime.datetime, optional
        The date to use. DWD radoland data is always stored at minute 50. Hence the last observation before
        nowcast_date will be used (default is None, gets current time)

    aggregation : str, optional
        "hourly" if getting the forecast of the hour that ended ath nowcast_time. "daily" if getting the forecast for
        the full day that ends at nowcast_time.

    mask : gpd.Geodataframe, optional
        If a mask is provided all only the radolan grid within the mask is returned. (default is None, no mask)

    xmin, xmax, ymin, ymax : int, optional
        indices within the 900x900 grid to only take a subset and save computation

    Returns
    -------
    grid_gdf
        a geodataframe with the grid cells of RADOLAN as geometry and rainfall data per grid as data

    meta_data
        a dictionary containing meta data from the RADOLAN forecast

    Raises
    ------
    ValueError
        if wrong aggregation is passed.
    RequestException
        If Radolan request went wrong
    """
    if nowcast_date is None:
        nowcast_date = datetime.datetime.now(tz=pytz.timezone("UTC"))

    if nowcast_date.minute >= 50:
        normalized_date = nowcast_date - datetime.timedelta(minutes=nowcast_date.minute - 50)
    else:
        normalized_date = nowcast_date - datetime.timedelta(minutes=nowcast_date.minute + 50)

    if aggregation == "hourly":
        url = f"https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/recent/bin/" \
              f"raa01-rw_10000-{normalized_date:%y%m%d%H%M}-dwd---bin.gz"
    elif aggregation == "daily":
        url = f"https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/radolan/recent/bin/" \
              f"raa01-sf_10000-{normalized_date:%y%m%d%H%M}-dwd---bin.gz"
    else:
        raise ValueError("aggregation must be hourly or daily")

    resp = requests.get(url)
    if not resp.ok:
        return

    radolan_file = gzip.open(io.BytesIO(resp.content), "rb")
    radolan_data, meta_data = wrl.io.read_radolan_composite(radolan_file)

    radolan_grid = wrl.georef.get_radolan_grid(900, 900, wgs84=True)

    grid_values, grid_geo = [], []

    for x in range(xmin, xmax - 1):
        for y in range(ymin, ymax - 1):
            grid_coords = list()
            grid_coords.append(radolan_grid[x, y, :])
            grid_coords.append(radolan_grid[x, y + 1, :])
            grid_coords.append(radolan_grid[x + 1, y + 1, :])
            grid_coords.append(radolan_grid[x + 1, y, :])
            grid_coords.append(radolan_grid[x, y, :])
            grid_geo.append(Polygon(grid_coords))
            grid_values.append(radolan_data[x, y])

    grid_gdf = gpd.GeoDataFrame(
        pd.DataFrame(grid_values, columns=["rainfall_mm"]), geometry=grid_geo, crs="EPSG:4326"
    )

    if mask is None:
        return grid_gdf, meta_data
    else:
        return gpd.sjoin(grid_gdf, mask), meta_data


def get_weather_stations(station_ids, measurement):
    """ Gets the weatherstations TODO
    """
    url_stations = f"https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/" \
                   f"{measurement}/KL_Tageswerte_Beschreibung_Stationen.txt"
    stations = pd.read_fwf(url_stations, encoding="ISO-8859-1", skiprows=2, header=None,
                           names=["Stations_id", "von_datum", "bis_datum", "Stationshoehe", "geoBreite",
                                  "geoLaenge", "Stationsname", "Bundesland"]
                           )

    return stations[stations.Stations_id.isin(station_ids)]


def get_observations(station, measurement):
    """ Gets dwd observations for a weatherstation. TODO
    """
    if measurement == "historical":
        url = f"https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/" \
              f"{measurement}/tageswerte_KL_{station.stations_id.values[0]:05d}_" \
              f"{station.von_datum.values[0]}_{station.bis_datum.values[0]}_hist.zip"
    else:
        url = f"https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/" \
              f"{measurement}/tageswerte_KL_{station.stations_id.values[0]:05d}_akt.zip"

    response_kl = requests.get(url)
    if not response_kl.ok:
        raise requests.exceptions.RequestException(f"Could not download {url}")

    zipdata = ZipFile(io.BytesIO(response_kl.content))
    txtfile = zipdata.open(zipdata.infolist()[len(zipdata.infolist()) - 1])
    # -999 is considered error/missing data as per documentation available here:
    # https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/recent/BESCHREIBUNG_obsgermany_climate_daily_kl_recent_de.pdf
    weather = pd.read_csv(txtfile, sep=";", skipinitialspace=True, na_values="-999")
    weather.columns = [x.lower() for x in weather.columns]
    weather["mess_datum"] = pd.to_datetime(weather["mess_datum"], format='%Y%m%d')
    return weather
