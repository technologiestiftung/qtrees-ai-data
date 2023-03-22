import os
import numpy as np
import rioxarray
import cv2

# declare the origin and target folders, idealy different
data_path = "../data"
sun_hour_map_folder = os.path.join(data_path, "sun_hour_maps")
target_filepath = os.path.join(data_path, "berlin_maps_filtered")
kernel_size = 5

def create_box_filter_maps(maps_directory, kernel_size):
    os.makedirs(target_filepath, exist_ok=True)
    print('creted target directory')

    for filename in os.listdir(maps_directory):
         if not filename.startswith('.') and filename.endswith('merged.tiff'):
            f_path = os.path.join(sun_hour_map_folder, filename)
            apply_box_filter(kernel_size, filename, f_path)

def create_gaussian_filter_maps(maps_directory, kernel_size):
    if  not os.path.exists(target_filepath):
        print('creted target directory')
        os.mkdir(target_filepath)
        
    for filename in os.listdir(maps_directory):
        if not filename.startswith('.'):
            f_path = os.path.join(sun_hour_map_folder, filename)
            apply_gaussian_filter(kernel_size, filename, f_path)

def apply_box_filter(kernel_size, map_name, filepath):
    map = rioxarray.open_rasterio(filepath)
    print(f'processing map: {map_name}')
    kernel_div = kernel_size * kernel_size
    kernel = np.ones((kernel_size, kernel_size), np.float32)/ kernel_div
    map_np = map[0].to_numpy()

    # apply the box filtering
    dst = cv2.filter2D(map_np, -1, kernel)

    map[0] = dst
    map_name = 'box_k'+ str(kernel_size) + '_' + map_name
    map.rio.to_raster(os.path.join(target_filepath, map_name))

def apply_gaussian_filter(kernel_sz, map_name, filepath):
    map = rioxarray.open_rasterio(filepath)
    print(f'processing map: {map_name}')
    map_np = map[0].to_numpy()

    dst = cv2.GaussianBlur(map_np, (kernel_sz, kernel_sz), 0)

    map[0] = dst
    map_name = 'gaussian_k' + str(kernel_size) + '_' + map_name
    map.rio.to_raster(os.path.join(target_filepath, map_name))


# create_gaussian_filter_maps(sun_hour_map_folder)
create_box_filter_maps(sun_hour_map_folder, kernel_size)