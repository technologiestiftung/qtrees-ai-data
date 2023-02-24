from qgis import processing
import os

data_path = "/Users/julianmoreno/Proyectos/Birds/qtrees-ai/qtrees/data"
hohenkarte_folder = os.path.join(data_path, "hohenkarte")
target_path = os.path.join(hohenkarte_folder, "processed")

def run_slope_aspect_processing(elevation_map, slope_path, aspect_path):

    processing.run("grass7:r.slope.aspect", 
                {'elevation':elevation_map,
                    'format':0,
                    'precision':0,
                    '-a':True,
                    '-e':False,
                    '-n':False,
                    'zscale':1,
                    'min_slope':0,
                    'slope': slope_path,
                    'aspect': aspect_path,
                    'pcurvature':'TEMPORARY_OUTPUT',
                    'tcurvature':'TEMPORARY_OUTPUT',
                    'dx':'TEMPORARY_OUTPUT',
                    'dy':'TEMPORARY_OUTPUT',
                    'dxx':'TEMPORARY_OUTPUT',
                    'dyy':'TEMPORARY_OUTPUT',
                    'dxy':'TEMPORARY_OUTPUT',
                    'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,
                    'GRASS_RASTER_FORMAT_OPT':'',
                    'GRASS_RASTER_FORMAT_META':''})

def process_all_tiles(tiles_folder, target_path):
    # this needs to check if is a .tiff file first
    for file in os.listdir(tiles_folder):
        slope_name = 'slope' + file
        aspect_name = 'aspect' + file
        slope_path = os.path.join(target_path, slope_name)
        aspect_path = os.path.join(target_path, aspect_name)
        run_slope_aspect_processing(elevetaion_map=file, 
                                    slope_path=slope_path, 
                                    aspect_path=aspect_path)

process_all_tiles(tiles_folder=hohenkarte_folder, target_path=target_path)

