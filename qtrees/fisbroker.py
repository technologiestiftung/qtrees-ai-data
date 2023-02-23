import requests
import geopandas as gpd
import pandas as pd
from requests import Request
from owslib.wfs import WebFeatureService
import os
from datetime import datetime
from helper import get_logger

logger = get_logger(__name__)


def _prepare_tree_data(gdf, street_tree):
    gdf = gdf.to_crs(4326)

    gdf['street_tree'] = street_tree
    gdf['baumscheibe'] = ""

    gdf['lat'] = gdf.geometry.y
    gdf['lng'] = gdf.geometry.x
    # geopandas.to_file has problems with datetime
    date = pd.to_datetime(datetime.now().date().strftime('%Y-%m-%d'))
    gdf['created_at'] = date
    gdf['updated_at'] = date
    gdf = gdf.rename(columns={"baumid": "id"})
    gdf = gdf.drop('gml_id', axis=1)
    gdf.drop_duplicates(subset=['id'], keep='first')

    return gdf


def store_trees_batchwise_to_db(trees_file, street_tree, engine, lu_ids=None, n_batch_size=100000):
    """
    load tree file, process data, remove duplicates and stored it into a db - all batchwise

    Parameters
    ----------
    trees_file: str
        filename for tree file
    street_tree: bool
        defines if data contains street trees (or anlagen trees)
    engine: db engine object
    lu_ids: set | None
        existing tree ids
    n_batch_size: int
        number of trees which processed at once

    Returns
    -------
        set, with tree ids so far
    """
    n_start = 0
    n_round = 0
    lu_ids = lu_ids or set()
    while True:
        n_end = n_start + n_batch_size
        gdf = gpd.read_file(trees_file, rows=slice(n_start, n_end))
        n_rows = len(gdf)
        # prepare data and remove patch-internal duplicates
        gdf = _prepare_tree_data(gdf, street_tree=street_tree)
        duplicates = lu_ids.intersection(gdf["id"])
        n_duplicates = len(duplicates) + n_rows - len(gdf)
        if n_duplicates > 0:
            logger.warning("Found duplicates: %s", list(duplicates))
        gdf = gdf[~gdf["id"].isin(duplicates)]
        lu_ids.update(gdf["id"])

        n_round += 1
        logger.info("Writing into db - batch %s (%s)", n_round, len(gdf))
        n_start = n_end

        try:
            gdf.to_postgis("trees", engine, if_exists="append", schema="public")
        except Exception as e:
            logger.error("Cannot write to db: %s", e)
            exit(121)

        # running out of data
        if len(gdf) < n_batch_size - n_duplicates:
            break

    return lu_ids


def download_tree_file(dir_data, type, use_cached=True):
    """
    download and store raw tree data

    Parameters
    ----------
    dir_data: str
        cache dir
    type: str
        defines tree dataset - currently 'wfs_baumbestand' or 'wfs_baumbestand_an'
    use_cached: bool
        defines if cached data is used or data should be downloaded again

    Returns
    -------
        str, filename for raw tree data

    """
    trees_file = os.path.join(dir_data, f"{type}.xml")
    if os.path.exists(trees_file) and use_cached:
        return trees_file

    logger.info("Downloading '%s' data", type)
    params = dict(service="WFS", version="2.0.0", request='GetFeature', typeNames=f"fis:s_{type}",
                  srsName="EPSG:25833")
    url = f"http://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_{type}"

    r = requests.get(url, params=params)
    with open(trees_file, 'wb') as f:
        f.write(r.content)
    return trees_file


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
        trees_gdf = trees_gdf.rename(columns={"baumid": "id"})
        trees_gdf = trees_gdf.drop('gml_id', axis=1)

        logger.debug("Saving trees geo data frames to %s.", trees_file)
        trees_gdf.to_file(trees_file, driver='GeoJSON')

    trees_gdf['created_at'] = pd.to_datetime(trees_gdf['created_at'])
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
