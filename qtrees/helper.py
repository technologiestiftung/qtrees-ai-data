import logging
import os


def init_db_args(args, logger):
    db_qtrees = args["--db_qtrees"]
    db_qtrees = db_qtrees or os.getenv("DB_QTREES")
    postgres_passwd = os.getenv("POSTGRES_PASSWD")

    if postgres_passwd is None:
        logger.error("Environment variable POSTGRES_PASSWD not set")
        exit(2)
    if db_qtrees is None:
        logger.error("Environment variable DB_QTREES not set")
        exit(2)
    return db_qtrees, postgres_passwd


def get_logger(name, log_level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False
    # return existing logger
    if logger.hasHandlers():
        return logger
    formatter = logging.Formatter('[%(asctime)s] %(levelname)8s --- %(message)s (%(filename)s:%(lineno)s)')
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(log_level)
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    return logger
