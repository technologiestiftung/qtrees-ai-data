CREATE EXTENSION postgis;
CREATE EXTENSION fuzzystrmatch;
CREATE EXTENSION postgis_tiger_geocoder;
CREATE EXTENSION postgis_topology;
CREATE EXTENSION tablefunc;

ALTER SCHEMA tiger OWNER TO gis_admin;
ALTER SCHEMA tiger_data OWNER TO gis_admin;
ALTER SCHEMA topology OWNER TO gis_admin;

CREATE SCHEMA IF NOT EXISTS private;
GRANT ALL ON SCHEMA private TO postgres;

CREATE SCHEMA IF NOT EXISTS basic_auth;

CREATE TYPE basic_auth.jwt_token AS (
  token text
);