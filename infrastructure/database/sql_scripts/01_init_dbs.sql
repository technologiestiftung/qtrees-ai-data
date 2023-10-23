
-- Create gis_admin role 
CREATE ROLE gis_admin LOGIN PASSWORD :'GIS_PASSWD';

:CMD_GIS_ADMIN 

--GRANT rds_superuser TO gis_admin;
--ALTER ROLE gis_admin SUPERUSER;

-- Create databases 
CREATE DATABASE lab_gis;
GRANT ALL PRIVILEGES ON DATABASE lab_gis TO gis_admin;

-- Drop and recreate qtrees if database exists 
DROP DATABASE IF EXISTS qtrees; 
CREATE DATABASE qtrees OWNER postgres; 

-- Create users anonymous user, authenticator, ai user and ui user 
CREATE ROLE web_anon nologin; 
CREATE ROLE authenticator noinherit LOGIN PASSWORD :'AUTH_PASSWD';
CREATE ROLE ai_user nologin;
CREATE ROLE ui_user nologin;

CREATE USER qtrees_admin WITH PASSWORD :'DB_ADMIN_PASSWD';
CREATE USER qtrees_user WITH PASSWORD :'DB_USER_PASSWD';