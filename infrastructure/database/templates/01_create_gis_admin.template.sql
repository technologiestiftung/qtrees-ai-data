CREATE ROLE gis_admin LOGIN PASSWORD '${GIS_PASSWD}';
${CMD_GIS_ADMIN}
-- todo: get this to work
--IF ${USE_RDS} THEN
--    GRANT rds_superuser TO gis_admin;
--ELSE
--    ALTER ROLE gis_admin SUPERUSER;
--END IF;

CREATE DATABASE lab_gis;
GRANT ALL PRIVILEGES ON DATABASE lab_gis TO gis_admin;

CREATE DATABASE qtrees OWNER postgres;


