#!/usr/bin/env python3
"""
Create shading index.
Usage:
  script_shading_index.py [--data_path=DATA_PATH]
  script_shading_index.py (-h | --help)
Options:
  --data_path=DATA_PATH                    Data path [default:./data]
"""

from astral import LocationInfo
from astral.sun import sun
import datetime
import rioxarray
import os
import pandas as pd
import json
from pyproj import CRS, Transformer
import sys
from docopt import docopt, DocoptExit

from qtrees.helper import get_logger
from qtrees.fisbroker import get_trees

logger = get_logger(__name__)

# This selected dates correspond to 80, 172, 266, 355 days of the year
selected_dates = {
    "80": datetime.date(2022, 3, 21),
    "172": datetime.date(2022, 6, 21),
    "266": datetime.date(2022, 9, 23),
    "355": datetime.date(2022, 12, 21),
}
city = LocationInfo(
    name="Berlin",
    region="Germany",
    timezone="Europe/Berlin",
    latitude=52.5200,
    longitude=13.4050,
)


# calculate theoretical sunhours of the 4 selected days of solstices & equinoxes
def calc_theoretical_daylight(dates, city):
    total_sun_seconds = {}
    for season, date in dates.items():
        s = sun(city.observer, date=date, tzinfo=city.timezone)
        for key in ["sunrise", "sunset"]:
            logger.info(f"{key:10s}: {s[key]}")
        sun_hours = s["sunset"] - s["sunrise"]
        logger.info("Daylight hours on the selected day{sun_hours}")
        sun_seconds = sun_hours.total_seconds()
        logger.info(f"Total seconds of daylight on the selected day {sun_seconds}")
        total_sun_seconds[season] = sun_seconds
    return total_sun_seconds


def calculate_sun_index(
    seasons_theoretical_daylight, sun_hours_map_directory, tree_json
):
    # transform tree coordinates to the crs of sun hours map
    out_proj = CRS("EPSG:25833")
    in_proj = CRS("EPSG:4326")
    transformer = Transformer.from_crs(
        crs_from=in_proj, crs_to=out_proj, always_xy=True
    )
    actual_sun_hours = {}
    """ goes through the trees & calculates the sun&shadow index per tree for
        every season based on the ratio of actual sun hours obtained from sun
        map divided by theoretical daylight calculated based on sunrise and
        sunset hours of the selected representative dates for seasons
    """
    for season, theoretical_daylight in seasons_theoretical_daylight.items():
        seasonal_values = {}
        # TODO: what happens if the file does not exist?
        # season must be in the file name
        for filename in os.listdir(sun_hours_map_directory):
            f = os.path.join(sun_hours_map_directory, filename)
            if os.path.isfile(f) and season in filename:
                qgis_sun_hours_map = rioxarray.open_rasterio(f)
                logger.info(f"calculating {season}...")
                for tree in list(tree_json.items()):
                    baum_id = tree[0]
                    lat, lon = tree[1]
                    lon, lat = transformer.transform(lon, lat)
                    tree_marked = qgis_sun_hours_map.sel(
                        x=[lon], y=[lat], method="nearest"
                    )
                    tree_actual_sun_hours = float(tree_marked.values)
                    shading_index = tree_actual_sun_hours * 3600 / theoretical_daylight
                    seasonal_values[baum_id] = round(shading_index, 2)
        actual_sun_hours[season] = seasonal_values
        with open("temp_shading.json", "w") as fp:
            json.dump(actual_sun_hours, fp)
    return actual_sun_hours


def get_sunindex_df(
    shadow_index_file,
    trees_file=None,
    qgis_sun_hours_folder="data/berlin_maps_filtered",
):
    # TODO: the shadow index file may exist but it may not be complete. How to check it?
    if not os.path.isfile(shadow_index_file):
        logger.warning("%s not found", shadow_index_file)
        # create json with id as key and coordinates as value
        trees_df = get_trees(trees_file)
        simplified_df = trees_df[["id", "geometry"]]
        logger.info("simplified_df: %s", simplified_df)
        trees_dict = {}
        for baumid, coordinate in simplified_df.itertuples(index=False):
            trees_dict[baumid] = (coordinate.y, coordinate.x)
        seasons_theoretical_daylight = calc_theoretical_daylight(selected_dates, city)
        logger.info(
            f"seasons_theoretical_daylight: {seasons_theoretical_daylight} qgis_sun_hours_folder: {qgis_sun_hours_folder}"
        )
        sun_index = calculate_sun_index(
            seasons_theoretical_daylight, qgis_sun_hours_folder, trees_dict
        )
        sun_index_df = pd.DataFrame(sun_index)
        shadow_index_df = (1.0 - sun_index_df).round(2)
        shadow_index_df.to_csv(shadow_index_file)

    else:
        logger.warning("The shading index file %s already exist", shadow_index_file)


if __name__ == "__main__":
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    data_root_path = args["--data_path"]
    qgis_sun_hours_folder = os.path.join(data_root_path, "berlin_maps_filtered")
    target_directory = os.path.join(data_root_path, "shadow_index")
    os.makedirs(target_directory, exist_ok=True)
    trees_file = os.path.join(target_directory, "all_trees_gdf.geojson")
    shadow_index_file = os.path.join(target_directory, "berlin_shadow_box_22_03.csv")
    get_sunindex_df(
        shadow_index_file=shadow_index_file,
        trees_file=trees_file,
        qgis_sun_hours_folder=qgis_sun_hours_folder,
    )
