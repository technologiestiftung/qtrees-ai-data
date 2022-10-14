import requests
import geopandas as gpd
import pandas as pd
from requests import Request
from owslib.wfs import WebFeatureService
import os
from datetime import datetime
from qtrees.helper import get_logger

logger = get_logger(__name__)


def get_trees(trees_file):
    if os.path.isdir(trees_file):
        logger.warning("%s is not a valid file.", trees_file)
        return None

    if not os.path.exists(os.path.dirname(trees_file)):
        os.makedirs(os.path.dirname(trees_file))

    if os.path.exists(trees_file):
        trees_gdf = gpd.read_file(trees_file, driver='GeoJSON')
        logger.debug("Reading trees geo data frames from %s.", trees_file)
    else:
        params = dict(service="WFS", version="2.0.0", request='GetFeature', typeNames="fis:s_wfs_baumbestand_an",
                      srsName="EPSG:25833")
        url = "http://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_wfs_baumbestand_an"
        q = requests.Request('GET', url, params=params).prepare().url
        trees_gdf_an = gpd.read_file(q).to_crs(4326)
        trees_gdf_an["street_tree"] = False

        params = dict(service="WFS", version="2.0.0", request='GetFeature', typeNames="fis:s_wfs_baumbestand",
                      srsName="EPSG:25833")
        url = "http://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_wfs_baumbestand"
        q = requests.Request('GET', url, params=params).prepare().url
        trees_gdf_street = gpd.read_file(q).to_crs(4326)
        trees_gdf_street["street_tree"] = True

        trees_gdf = pd.concat([trees_gdf_street, trees_gdf_an])

        trees_gdf['lat'] = trees_gdf.geometry.y
        trees_gdf['lng'] = trees_gdf.geometry.x
        # geopandas.to_file has problems with datetime
        date = datetime.now().date().strftime('%Y-%m-%d')
        trees_gdf['created_at'] = date
        trees_gdf['updated_at'] = date

        logger.debug("Saving trees geo data frames to %s.", trees_file)
        trees_gdf.to_file(trees_file, driver='GeoJSON')

    trees_gdf['created_at'] = pd.to_datetime(trees_gdf['created_at'] )
    trees_gdf['updated_at'] = pd.to_datetime(trees_gdf['updated_at'])
    return trees_gdf


# request wfs
def get_gdf(url, crs, geojson_file):
    if not os.path.isfile(geojson_file):
        logger.debug("Gdf doesn't exist, making a wfs request.")
        wfs = WebFeatureService(url=url)
        layer = list(wfs.contents)[-1]
        params = dict(service="wfs", version="2.0.0", request='GetFeature', TYPENAMES=layer, crs=crs)
        q = Request('GET', url, params=params).prepare().url
        gdf = gpd.read_file(q).set_crs(epsg=25833)
        gdf = gdf.to_crs(4326)
        logger.debug("Saving geojson...")
        gdf.to_file(geojson_file, driver='GeoJSON')
    logger.debug("Reading geojson file...")
    gdf = gpd.read_file(geojson_file, driver='GeoJSON')
    return gdf
