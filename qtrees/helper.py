import logging
import os



_db_lookup_env = {
    "qtrees": {"db": "DB_QTREES", "passwd": "POSTGRES_PASSWD"},
    "gdk": {"db": "DB_GDK", "passwd": "GDK_PASSWD"},
}


def init_db_args(db, db_type, logger):
    db_conf = _db_lookup_env.get(db_type)
    if db_conf is None:
        logger.error("No config found for %s. Available: %s", db_type, _db_lookup_env.keys())
        exit(2)

    db = db or os.getenv(db_conf["db"])
    passwd = os.getenv(db_conf["passwd"])

    if passwd is None:
        logger.error("Environment variable %s not set", db_conf["passwd"])
        exit(2)
    if db is None:
        logger.error("Environment variable %s not set", db_conf["db"])
        exit(2)
    return db, passwd


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
