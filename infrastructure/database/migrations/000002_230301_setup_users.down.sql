
/*
ALTER DEFAULT PRIVILEGES IN SCHEMA private
REVOKE SELECT ON TABLES to qtrees_user; 

ALTER DEFAULT PRIVILEGES IN SCHEMA public
REVOKE SELECT ON TABLES TO qtrees_user;

REVOKE SELECT ON ALL TABLES IN SCHEMA private TO qtrees_user;
REVOKE SELECT ON ALL TABLES IN SCHEMA public TO qtrees_user;

REVOKE USAGE ON SCHEMA private TO qtrees_user;
REVOKE USAGE ON SCHEMA public TO qtrees_user;

*/ 

REVOKE CONNECT ON DATABASE qtrees FROM qtrees_user;

/* 
ALTER DEFAULT PRIVILEGES IN SCHEMA private
REVOKE ALL ON TABLES TO qtrees_admin;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
REVOKE ALL ON TABLES TO qtrees_admin;

*/ 

REVOKE CONNECT ON DATABASE qtrees FROM qtrees_admin;

revoke execute on function public.login(text,text) FROM web_anon;
revoke execute on function public.login(text,text) FROM authenticator;

REVOKE all ON SCHEMA public FROM ui_user; 
REVOKE ui_user FROM authenticator; 
REVOKE all ON SCHEMA public FROM ai_user; 
REVOKE ai_user FROM authenticator;
REVOKE web_anon FROM authenticator;
REVOKE all ON SCHEMA public FROM web_anon;