# as this run only locally, we don't care much about proper tokens and password.
export GIS_PASSWD="gisgisgis"
export AUTH_PASSWD="authauthauth" # needed?

# Postgres/qtrees server credentials 
export POSTGRES_PASSWD="postgrespostgres"
export DB_QTREES="localhost"  # TODO: Should this be called db_qtrees and not server? 
export JWT_SECRET="secret_with_at_least_thirtytwo_chars"
export CMD_GIS_ADMIN="ALTER ROLE gis_admin SUPERUSER;" # local use

# User credentials 
export DB_ADMIN_PASSWD="adminadminadmin"
export DB_USER_PASSWD="useruseruser"
export UI_USER_PASSWD="uiuiuiuiui"
export GDK_PASSWD=
export DB_GDK=
export QTREES_VERSION="local"
export SOLARANYWHERE_API_KEY='' # needs to be single quote to escape the api keys dollar sign

# Path golang-migrations
export MIGRATIONS="migrations"
export PGRST_DB_URI="postgresql://postgres:${POSTGRES_PASSWD}@${DB_QTREES}:5432/qtrees?sslmode=disable" 