import os
from qgis import processing
import glob
import rasterio
from rasterio.merge import merge

"""
This script computes sun hour maps based on elevation tile files. It first calculates 
the slope and aspect of the terrain with 'run_slope_aspect_processing' and then generates sun 
hour maps for selected dates through 'insoltime_calc'. 
To merge all computed maps into one big merged file for each date, use the 'merge_sunhour_maps' function.

This script is designed to be run in the Python console of QGIS and is not intended to be 
used as a standalone script.
"""
#  replace the data path
data_path = "~/Projects/qtrees-ai-data/data/data_single_tile/"
elevation_maps_folder = os.path.join(data_path, "elevation_maps_berlin")
slope_aspect_folder = os.path.join(data_path, "slope_aspect")
sun_hour_map_folder = os.path.join(data_path, "sun_hour_maps")
selected_dates = [1, 31, 61, 91, 121, 151, 181, 211, 241, 271, 301, 331]


def run_slope_aspect_processing(elevation_map, slope_path, aspect_path):
    processing.run("grass7:r.slope.aspect",
                   {'elevation': elevation_map,
                    'format': 0,
                    'precision': 0,
                    '-a': True,
                    '-e': True,
                    '-n': False,
                    'zscale': 1,
                    'min_slope': 0,
                    'slope': slope_path,
                    'aspect': aspect_path,
                    'pcurvature': 'TEMPORARY_OUTPUT',
                    'tcurvature': 'TEMPORARY_OUTPUT',
                    'dx': 'TEMPORARY_OUTPUT',
                    'dy': 'TEMPORARY_OUTPUT',
                    'dxx': 'TEMPORARY_OUTPUT',
                    'dyy': 'TEMPORARY_OUTPUT',
                    'dxy': 'TEMPORARY_OUTPUT',
                    'GRASS_REGION_PARAMETER': None,
                    'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                    'GRASS_RASTER_FORMAT_OPT': '',
                    'GRASS_RASTER_FORMAT_META': ''})


def insoltime_calc(elevation_map, slope_path, aspect_path, sunhours_file_path, day):
    processing.run("grass7:r.sun.insoltime",
                   {'elevation': elevation_map,
                    'aspect': aspect_path,
                    'aspect_value': 270,
                    'slope': slope_path,
                    'slope_value': 0,
                    'linke': None,
                    'albedo': None,
                    'albedo_value': 0.2,
                    'lat': None,
                    'long': None,
                    'coeff_bh': None,
                    'coeff_dh': None,
                    'horizon_basemap': None,
                    'horizon_step': None,
                    'day': day,
                    'step': 0.5,
                    'declination': None,
                    'distance_step': 1,
                    'npartitions': 1,
                    'civil_time': None,
                    '-p': False,
                    '-m': False,
                    'insol_time': sunhours_file_path,
                    'beam_rad': 'TEMPORARY_OUTPUT',
                    'diff_rad': 'TEMPORARY_OUTPUT',
                    'refl_rad': 'TEMPORARY_OUTPUT',
                    'glob_rad': 'TEMPORARY_OUTPUT',
                    'GRASS_REGION_PARAMETER': None,
                    'GRASS_REGION_CELLSIZE_PARAMETER': 0,
                    'GRASS_RASTER_FORMAT_OPT': '',
                    'GRASS_RASTER_FORMAT_META': ''})


def merge_sunhour_maps(sunhours_folder, target_file):
    for subdir in os.listdir(sunhours_folder):
        sunhour_maps_subdir = os.path.join(sunhours_folder, subdir)
        tiff_files = [os.path.join(sunhour_maps_subdir, f) for f in os.listdir(sunhour_maps_subdir) if
                      f.endswith('.tiff')]
        target_file = os.path.join(sunhours_folder, subdir + '_merged.tiff')

        # Initialize an empty list to hold the data arrays
        src_files_to_mosaic = []

        # Loop through all the GeoTIFF files and add them to the list
        for tiff_file in tiff_files:
            src = rasterio.open(tiff_file)
            src_files_to_mosaic.append(src)

        # Merge all the individual GeoTIFF files into a single mosaic
        mosaic, out_trans = merge(src_files_to_mosaic)

        # Update the metadata for the mosaic file
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "compress": "None"
        })
        with rasterio.open(target_file, "w", **out_meta) as dest:
            dest.write(mosaic)


def process_all_tiles(tiles_folder, slope_aspect_folder, selected_dates):
    for file_path in glob.glob(os.path.join(tiles_folder, '*.tiff')):
        file_name = os.path.basename(file_path)
        os.makedirs(slope_aspect_folder, exist_ok=True)
        slope_path = os.path.join(slope_aspect_folder, 'slope_' + file_name)
        aspect_path = os.path.join(slope_aspect_folder, 'aspect_' + file_name)
        if not (os.path.exists(slope_path) and os.path.exists(aspect_path)):
            run_slope_aspect_processing(elevation_map=file_path, slope_path=slope_path, aspect_path=aspect_path)

        for day in selected_dates:
            sunhours_folder = os.path.join(sun_hour_map_folder, str(day))
            os.makedirs(sunhours_folder, exist_ok=True)
            sunhours_file_path = os.path.join(sunhours_folder, str(day) + file_name)
            if not os.path.exists(sunhours_file_path):
                insoltime_calc(elevation_map=file_path, slope_path=slope_path, aspect_path=aspect_path,
                               sunhours_file_path=sunhours_file_path, day=day)


process_all_tiles(tiles_folder=elevation_maps_folder, slope_aspect_folder=slope_aspect_folder,
                  selected_dates=selected_dates)
merge_sunhour_maps(sun_hour_map_folder, target_file=None)
