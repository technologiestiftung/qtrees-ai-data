#!/usr/bin/env python3
"""
Download tree data and store into db.
Usage:
  script_store_soil_in_db.py [--data_directory=DATA_DIRECTORY] [--db_qtrees=DB_QTREES]
  script_store_soil_in_db.py (-h | --help)
Options:
  --data_directory=DATA_DIRECTORY              Directory for data [default: data/trees]
  --db_qtrees=DB_QTREES                        Database name [default:]
"""
import os.path
import os
from datetime import datetime
from sqlalchemy import create_engine
import sqlalchemy
from docopt import docopt, DocoptExit
from qtrees.helper import get_logger, init_db_args
import sys
from qtrees.fisbroker import get_gdf

logger = get_logger(__name__)


def main():
    logger.info("Args: %s", sys.argv[1:])
    # Parse arguments
    args = docopt(__doc__)
    db_qtrees, postgres_passwd = init_db_args(args, logger)

    data_directory = args["--data_directory"]

    engine = create_engine(
        f"postgresql://postgres:{postgres_passwd}@{db_qtrees}:5432/qtrees"
    )

    do_update = True
    if sqlalchemy.inspect(engine).has_table("soil", schema="api"):
        with engine.connect() as con:
            rs = con.execute('select COUNT(*) from api.soil')
            count = [idx[0] for idx in rs][0]
        if count > 0:
            logger.warning("Already %s soil entries in database. Skipping...", count)
            do_update = False

    if do_update:
        # create data directory if it doesn't exist
        if not os.path.isdir(data_directory):
            os.makedirs(data_directory)
            logger.debug(f"Creating '{data_directory}' directory to save geodataframes.")

        # Bodengesellschaften und Bodenarten 2015 Beschreibung
        # https://fbinter.stadt-berlin.de/fb_daten/beschreibung/umweltatlas/datenformatbeschreibung
        #  /Datenformatbeschreibung_bodengesellschaften_und_bodenarten2015.pdf
        s_boden_wfs1_2015_url = 'https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_boden_wfs1_2015'
        crs = "EPSG:25833"
        soil_gdf_file = os.path.join(data_directory, "soil_gdf.geojson")
        soil_gdf = get_gdf(s_boden_wfs1_2015_url, crs, soil_gdf_file)

        date = datetime.now().date()
        soil_gdf['created_at'] = date
        soil_gdf['updated_at'] = date

        logger.info("Writing into db")
        try:
            soil_gdf.to_postgis("soil", engine, if_exists="append", schema="api")
            with engine.connect() as con:
                rs = con.execute('select COUNT(*) from api.soil')
                count = [idx[0] for idx in rs][0]
            logger.info(f"Now, %s soil entries in database.", count)
        except Exception as e:
            logger.error("Cannot write to db:", e)
            exit(121)


if __name__ == "__main__":
    try:
        main()
    except DocoptExit as e:
        logger.error("Incorrect command line parameter %s", e)
        exit(72)
    finally:
        pass
