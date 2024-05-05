import os
import geopandas as gpd
import pandas as pd
import xarray as xr
import rioxarray as rxr
from pyproj import CRS, Transformer
from shapely.geometry import Point

selected_seasons = ['spring', 'summer', 'autumn', 'winter']
gdf_original_trees = gpd.read_file('data/all_trees_gdf.geojson')
df_shadow_filtered_index = pd.read_csv('data/berlin_shadow_box_220323.csv')
# df_shadow_original_index = pd.read_csv('data/berlin_shadow_index_test.csv')
target_filepath = "data/berlin_maps_validation_filtered"
vector_filtered_filepath = "data/vector_layer/all_trees_filtered_06042023.shp"
# vector_original_filepath = "data/vector_layer/all_trees_original.shp"
# not data, matching CRS and size
map_example_canvas = rxr.open_rasterio('data/berlin_sunhours_maps/summer_172_insoltime-003.tif')
target_map = xr.zeros_like(map_example_canvas)


def only_tree_map_creation(empty_map, new_shadow_index, season, flie_path):
    out_proj = CRS('EPSG:25833')
    in_proj = CRS('EPSG:4326')
    transformer = Transformer.from_crs(crs_from=in_proj,
                                       crs_to=out_proj,
                                       always_xy=True)
    # to be refactor using .apply()
    for index, tree in new_shadow_index.iterrows():
        lat, lon = tree['lat'], tree['lng']
        lon, lat = transformer.transform(lon, lat)
        marked_tree = empty_map.sel(x=lon, y=lat, method='nearest')
        x = float(marked_tree[0].coords['x'].values)
        y = float(marked_tree[0].coords['y'].values)
        empty_map[0].loc[dict(x=x, y=y)] = tree[season]

    empty_map.rio.to_raster(flie_path)


def gdf_shadow_index_creation(df_shadow_index, gdf_trees):
    df_shadow_index = df_shadow_index.rename(columns={"Unnamed: 0": "gml_id"})
    simple_trees_gdf = gdf_trees[["gml_id", "lat", "lng"]]
    shadow_index_gdf = df_shadow_index.set_index('gml_id').join(simple_trees_gdf.set_index('gml_id'))
    test_empty_coords(shadow_index_gdf)
    return shadow_index_gdf


def test_empty_coords(new_df):
    x = new_df['lat'].isnull().sum()
    y = new_df['lng'].isnull().sum()
    if (x or y):
        print('There are trees without coordinate values')
        print(f'empty values lat: {x} lng: {y}')


def create_raster_validation_seasons(empty_map,
                                     trees_gdf, shadow_index_df,
                                     target_filepath,
                                     selected_seasons):
    new_shadow_index = gdf_shadow_index_creation(shadow_index_df, trees_gdf)
    if not os.path.exists(target_filepath):
        os.mkdir(target_filepath)
    for season in selected_seasons:
        map_name = 'validation_' + season + '.tif'
        file_path = os.path.join(target_filepath, map_name)
        if not os.path.isfile(file_path):
            only_tree_map_creation(empty_map, new_shadow_index, season, file_path)
        else:
            print(f"The file {file_path} already exist")


# functions transform and create vector could be one
def create_vector_gdf(df):
    # yields a warning -> Shapely 2.0 change
    df['geometry'] = df.apply(lambda tree: Point(tree['lng'],
                                                 tree['lat']),
                              axis=1)
    df = df.drop(['lat', 'lng'], axis=1)
    new_gdf = gpd.GeoDataFrame(df, geometry='geometry')
    new_gdf = new_gdf.set_crs('epsg:25833')
    # replace the 50.000 coordinates of trees missing (?)
    new_gdf.loc[~new_gdf.is_valid, 'geometry'] = new_gdf.loc[~new_gdf.is_valid, 'geometry'].apply(lambda x: Point(0, 0))
    return new_gdf


def transform_target_CRS(df):
    # transform and store values in the df
    out_proj = CRS('EPSG:25833')
    in_proj = CRS('EPSG:4326')
    transformer = Transformer.from_crs(crs_from=in_proj,
                                       crs_to=out_proj,
                                       always_xy=True)

    # could benefit from using apply() method
    for index, tree in df.iterrows():
        lat, lon = tree['lat'], tree['lng']
        lon, lat = transformer.transform(lon, lat)
        tree['lat'], tree['lng'] = lat, lon
    return df


def merge_coord_df(df, gdf):
    df = df.rename(columns={"Unnamed: 0": "gml_id"})
    simple_gdf = gdf[["baumid", "lat", "lng"]]
    new_df = df.set_index('gml_id').join(simple_gdf.set_index('baumid'))
    return new_df


def create_vector_validation(df_shadow_index, gdf_trees, vector_filepath):
    # select fraction of the data
    # df_shadow_index = df_shadow_index.sample(frac = 0.25) 

    # merge coords in gdf into shadow index df
    df_shadow_index_vector = merge_coord_df(df_shadow_index, gdf_trees)

    # transform coords to target CRS 
    df_shadow_index_vector = transform_target_CRS(df_shadow_index_vector)

    # make it a gdf
    vector_gdf = create_vector_gdf(df_shadow_index_vector)

    # save to files
    vector_gdf.to_file(vector_filepath, driver='ESRI Shapefile')

# create_raster_validation_seasons(target_map, gdf_original_trees, df_shadow_index, target_filepath, selected_seasons)
# create_vector_validation(df_shadow_original_index, gdf_original_trees, vector_original_filepath)
# create_vector_validation(df_shadow_filtered_index, gdf_original_trees, vector_filtered_filepath)
