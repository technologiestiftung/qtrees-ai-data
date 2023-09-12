
-- Create gis_admin role 
CREATE ROLE gis_admin LOGIN PASSWORD :'GIS_PASSWD';
:CMD_GIS_ADMIN 

-- Create databases 
CREATE DATABASE lab_gis;
GRANT ALL PRIVILEGES ON DATABASE lab_gis TO gis_admin;
CREATE DATABASE qtrees OWNER postgres; 

ALTER ROLE gis_admin SUPERUSER;

-- Create users anonymous user, authenticator, ai user and ui user 
CREATE ROLE web_anon nologin; 
CREATE ROLE authenticator noinherit LOGIN PASSWORD :'AUTH_PASSWD';
CREATE ROLE ai_user nologin;
CREATE ROLE ui_user nologin;

CREATE USER qtrees_admin WITH PASSWORD :'DB_ADMIN_PASSWD';
CREATE USER qtrees_user WITH PASSWORD :'DB_USER_PASSWD';