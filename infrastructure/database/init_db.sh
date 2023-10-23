
RED='\033[0;31m'
NC='\033[0m'


sleep 3 
PGPASSWORD=${POSTGRES_PASSWD} psql --host=$DB_QTREES --port=5432 \
    --username=postgres -a -f sql_scripts/01_init_dbs.sql \
    -v GIS_PASSWD=${GIS_PASSWD}  -v DB_USER_PASSWD=${DB_USER_PASSWD} \
    -v AUTH_PASSWD=${AUTH_PASSWD} -v DB_ADMIN_PASSWD=${DB_ADMIN_PASSWD} \
    -v CMD_GIS_ADMIN="${CMD_GIS_ADMIN}"
echo -e "${RED}############ Load GIS extension and grant user privileges ${NC}" 
sleep 3 
PGPASSWORD=${GIS_PASSWD} psql --host=$DB_QTREES --port=5432 \
    --username=gis_admin --dbname=lab_gis -a -f sql_scripts/02_load_gis_extension.sql
echo "${RED}############ Setting up qtrees user management ${NC}" 
sleep 3 
PGPASSWORD=${POSTGRES_PASSWD} psql --host=$DB_QTREES --port=5432 \
    --username=postgres --dbname=qtrees -a -f sql_scripts/03_user_management.sql \
    -v UI_USER_PASSWD=${UI_USER_PASSWD}
echo "${RED}############ Adding JWT support ${NC}"
sleep 3
PGPASSWORD=${POSTGRES_PASSWD} psql --host=$DB_QTREES --port=5432 \
    --username=postgres --dbname=qtrees -a -f sql_scripts/04_add_jwt.sql
echo "${RED}############ Run golang migrations ${NC}"
