-- make a role to use for anonymous web requests
create role web_anon nologin;

grant usage on schema api to web_anon;
grant select on api.trees to web_anon;
grant select on api.soil to web_anon;
grant select on api.radolan to web_anon;
grant select on api.forecast to web_anon;
grant select on api.nowcast to web_anon;
grant select on api.shading to web_anon;
grant select on api.forecast_types to web_anon;
grant select on api.weather to web_anon;
grant select on api.weather_stations to web_anon;
grant select on api.issue_types to web_anon;
grant select on api.issues to web_anon;

-- create a dedicated role for connecting to the database, instead of using postgres
create role authenticator noinherit login password '${AUTH_PASSWD}';
grant web_anon to authenticator;


-- make roles for changing date
create role ai_user nologin;
grant ai_user to authenticator;

grant usage on schema api to ai_user;
grant all on api.trees to ai_user;
grant all on api.soil to ai_user;
grant all on api.radolan to ai_user;
grant all on api.forecast to ai_user;
grant all on api.nowcast to ai_user;
grant all on api.shading to ai_user;
grant all on api.sensor_types to ai_user;
grant all on api.weather to ai_user;
grant all on api.weather_stations to ai_user;
grant select on api.issue_types to ai_user;
grant select on api.issues to ai_user;


create role ui_user nologin;
grant ui_user to authenticator;

grant usage on schema api to ui_user;
grant select on api.trees to ui_user;
grant select on api.soil to ui_user;
grant select on api.radolan to ui_user;
grant select on api.forecast to ui_user;
grant select on api.nowcast to ui_user;
grant select on api.shading to ui_user;
grant select on api.sensor_types to ui_user;
grant select on api.weather to ui_user;
grant select on api.weather_stations to ui_user;
grant all on api.issue_types to ui_user;
grant all on api.issues to ui_user;