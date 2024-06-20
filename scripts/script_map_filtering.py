#!/usr/bin/env python3
"""
Create filtered maps from the sun hour maps.
Usage:
  script_map_filtering.py [--data_path=DATA_PATH] [--kernel_size=KERNEL_SIZE] [--filter_method=FILTER_METHOD]
  script_map_filtering.py (-h | --help)
Options:
  --data_path=DATA_PATH                    Data path [default: ../data]
  --kernel_size=KERNEL_SIZE                Kernel size of filter [default: 5]
  --filter_method=FILTER_METHOD            Method for filtering [default: box]
"""
import os
import numpy as np
import rioxarray
import cv2  # todo: add pip install opencv-python to requirement?
import sys
from docopt import docopt, DocoptExit

from qtrees.helper import get_logger


logger = get_logger(__name__)


def create_box_filter_maps(maps_directory, kernel_size):
    if not os.path.exists(target_filepath):
        logger.info("creating target directory")
        os.makedirs(target_filepath, exist_ok=True)

    for filename in os.listdir(maps_directory):
        logger.info(f"processing map: {filename}")

        if os.path.isfile(os.path.join(maps_directory, filename)) and filename.endswith(
            "merged.tiff"
        ):
            f_path = os.path.join(sun_hour_map_folder, filename)
            apply_box_filter(
                kernel_size=kernel_size,
                map_name=filename,
                filepath=f_path,
                target_filepath=target_filepath,
            )


def create_gaussian_filter_maps(maps_directory, kernel_size):
    logger.info(target_filepath)
    if not os.path.exists(target_filepath):
        logger.info("creating target directory")
        os.makedirs(target_filepath, exist_ok=True)

    for filename in os.listdir(maps_directory):
        if os.path.isfile(os.path.join(maps_directory, filename)) and filename.endswith(
            "merged.tiff"
        ):
            f_path = os.path.join(sun_hour_map_folder, filename)
            apply_gaussian_filter(
                kernel_size=kernel_size,
                map_name=filename,
                filepath=f_path,
                target_filepath=target_filepath,
            )


def apply_box_filter(kernel_size, map_name, filepath, target_filepath):
    map = rioxarray.open_rasterio(filepath)
    logger.info(f"processing map: {map_name}")
    kernel_div = kernel_size * kernel_size
    kernel = np.ones((kernel_size, kernel_size), np.float32) / kernel_div
    map_np = map[0].to_numpy()

    # apply the box filtering
    dst = cv2.filter2D(map_np, -1, kernel)

    map[0] = dst
    map_name = "box_k" + str(kernel_size) + "_" + map_name
    map.rio.to_raster(os.path.join(target_filepath, map_name))


def apply_gaussian_filter(kernel_size, map_name, filepath, target_filepath):
    map = rioxarray.open_rasterio(filepath)
    print(f"processing map: {map_name}")
    map_np = map[0].to_numpy()

    dst = cv2.GaussianBlur(map_np, (kernel_size, kernel_size), 0)

    map[0] = dst
    map_name = "gaussian_k" + str(kernel_size) + "_" + map_name
    map.rio.to_raster(os.path.join(target_filepath, map_name))


if __name__ == "__main__":
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    data_path = args["--data_path"]
    sun_hour_map_folder = os.path.join(data_path, "sun_hour_maps")
    target_filepath = os.path.join(data_path, "berlin_maps_filtered")
    kernel_size = int(args["--kernel_size"])

    if args["--filter_method"] == "box":
        create_box_filter_maps(sun_hour_map_folder, kernel_size)
    elif args["--filter_method"] == "gaussian":
        create_gaussian_filter_maps(sun_hour_map_folder, kernel_size)
    else:
        logger.error("Invalid filter method. Please use either box or gaussian.")
        sys.exit(1)
