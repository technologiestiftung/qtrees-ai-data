-- We put things inside the basic_auth schema to hide
-- them from public view. Certain public procs/views will
-- refer to helpers and tables inside.
create schema if not exists basic_auth;

create table if not exists
basic_auth.users (
  email    text primary key check ( email ~* '^.+@.+\..+$' ),
  pass     text not null check (length(pass) < 512),
  role     name not null check (length(role) < 512)
);

-- We would like the role to be a foreign key to actual database roles,
-- however PostgreSQL does not support these constraints against the
-- pg_roles table. We’ll use a trigger to manually enforce it.

create or replace function
basic_auth.check_role_exists() returns trigger as $$
begin
  if not exists (select 1 from pg_roles as r where r.rolname = new.role) then
    raise foreign_key_violation using message =
      'unknown database role: ' || new.role;
    return null;
  end if;
  return new;
end
$$ language plpgsql;

drop trigger if exists ensure_user_role_exists on basic_auth.users;
create constraint trigger ensure_user_role_exists
  after insert or update on basic_auth.users
  for each row
  execute procedure basic_auth.check_role_exists();

-- Next we’ll use the pgcrypto extension and a trigger to keep
-- passwords safe in the users table.

create extension if not exists pgcrypto;

create or replace function
basic_auth.encrypt_pass() returns trigger as $$
begin
  if tg_op = 'INSERT' or new.pass <> old.pass then
    new.pass = crypt(new.pass, gen_salt('bf'));
  end if;
  return new;
end
$$ language plpgsql;

drop trigger if exists encrypt_pass on basic_auth.users;
create trigger encrypt_pass
  before insert or update on basic_auth.users
  for each row
  execute procedure basic_auth.encrypt_pass();

-- With the table in place we can make a helper to check a password
-- against the encrypted column. It returns the database role for
-- a user if the email and password are correct.

create or replace function
basic_auth.user_role(email text, pass text) returns name
  language plpgsql
  as $$
begin
  return (
  select role from basic_auth.users
   where users.email = user_role.email
     and users.pass = crypt(user_role.pass, users.pass)
  );
end;
$$;create or replace function
basic_auth.user_role(email text, pass text) returns name
  language plpgsql
  as $$
begin
  return (
  select role from basic_auth.users
   where users.email = user_role.email
     and users.pass = crypt(user_role.pass, users.pass)
  );
end;
$$;

-- Public User Interface
-- In the previous section we created an internal table to store
-- user information. Here we create a login function which takes
-- an email address and password and returns JWT if the credentials
-- match a user in the internal table.

-- add type
CREATE TYPE basic_auth.jwt_token AS (
  token text
);

CREATE TYPE jwt_token AS (
  token text
);

-- run this once
-- ALTER DATABASE qtrees SET "app.jwt_secret" TO '${JWT_SECRET}';
-- doesn't work with with RDS - settimng it individually

-- jwt_test added (ng)
--CREATE or replace FUNCTION basic_auth.jwt_test() RETURNS basic_auth.jwt_token AS $$
--  SELECT sign(
--    row_to_json(r), '${JWT_SECRET}'
--  ) AS token
--  FROM (
--    SELECT
--      'my_role'::text as role,
--      extract(epoch from now())::integer + 300 AS exp
--  ) r;
--$$ LANGUAGE sql;

-- login should be on your exposed schema
create or replace function
api.login(email text, pass text) returns basic_auth.jwt_token as $$
declare
  _role name;
  result basic_auth.jwt_token;
begin
  -- check email and password
  select basic_auth.user_role(email, pass) into _role;
  if _role is null then
    raise invalid_password using message = 'invalid user or password';
  end if;

  select sign(
      row_to_json(r), '${JWT_SECRET}'
    ) as token
    from (
      select _role as role, login.email as email,
         extract(epoch from now())::integer + 60*60 as exp
    ) r
    into result;
  return result;
end;
$$ language plpgsql security definer;

-- the names "anon" and "authenticator" are configurable and not
-- sacred, we simply choose them for clarity
-- create role anon noinherit;
-- create role authenticator noinherit;
-- grant web_anon to authenticator;

grant execute on function api.login(text,text) to web_anon;
grant execute on function api.login(text,text) to authenticator;


-- create user - should be done manually?
-- insert into basic_auth.users (email, pass, role) values ('nico@blablub.com', 'qweasd', 'ai_user');