# as this run only locally, we don't care much about proper tokens and password.
export GIS_PASSWD="gisgisgis"
export AUTH_PASSWD="authauthauth" # needed?
export JWT_SECRET="secret_with_at_least_thirtytwo_chars"
export POSTGRES_PASSWD="postgrespostgres"
export DB_QTREES="localhost"
export CMD_GIS_ADMIN="ALTER ROLE gis_admin SUPERUSER;" # local use
