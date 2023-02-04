-- make a role to use for anonymous web requests
create role web_anon nologin;

grant usage on schema public to web_anon;
grant select on public.trees to web_anon;
grant select on public.soil to web_anon;
grant select on public.radolan to web_anon;
grant select on public.radolan_ to web_anon;
grant select on public.radolan_tiles to web_anon;
grant select on public.forecast to web_anon;
grant select on public.nowcast to web_anon;
grant select on public.shading to web_anon;
grant select on public.sensor_types to web_anon;
grant select on public.weather to web_anon;
grant select on public.weather_stations to web_anon;
grant select on public.issue_types to web_anon;
grant select on public.issues to web_anon;

-- create a dedicated role for connecting to the database, instead of using postgres
create role authenticator noinherit login password '${AUTH_PASSWD}';
grant web_anon to authenticator;


-- make roles for changing date
create role ai_user nologin;
grant ai_user to authenticator;

grant usage on schema public to ai_user;
grant all on public.trees to ai_user;
grant all on public.soil to ai_user;
grant all on public.radolan to ai_user;
grant all on public.radolan_ to ai_user;
grant all on public.radolan_tiles to ai_user;
grant all on public.forecast to ai_user;
grant all on public.nowcast to ai_user;
grant all on public.shading to ai_user;
grant all on public.sensor_types to ai_user;
grant all on public.weather to ai_user;
grant all on public.weather_stations to ai_user;
grant select on public.issue_types to ai_user;
grant select on public.issues to ai_user;
grant usage, select on all sequences in schema public to ai_user;


create role ui_user nologin;
grant ui_user to authenticator;

grant usage on schema public to ui_user;
grant select on public.trees to ui_user;
grant select on public.soil to ui_user;
grant select on public.radolan to ui_user;
grant select on public.radolan_ to ui_user;
grant select on public.radolan_tiles to ui_user;
grant select on public.forecast to ui_user;
grant select on public.nowcast to ui_user;
grant select on public.shading to ui_user;
grant select on public.sensor_types to ui_user;
grant select on public.weather to ui_user;
grant select on public.weather_stations to ui_user;
grant select on public.issue_types to ui_user;
grant all on public.issues to ui_user;
grant usage, select on all sequences in schema public to ui_user;