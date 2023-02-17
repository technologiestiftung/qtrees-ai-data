![Qtrees](data/img/QtreesDefault.jpg)

# qtrees - data and AI backend

This repository is related to **Quantified Trees** – a project funded by the Federal Ministry for the Environment, Nature Conservation and Nuclear Safety of Germany

## Requirements
You need two things on the mac:
1. Install docker-desktop:
https://docs.docker.com/desktop/mac/install/
1. psql: `brew install libpq`. Propably, you have to run `brew link --force libpq` as well.

## Remote setup

The aim of the setup is to run:
- a postGIS DB as a AWS RDS-service
- postgREST as a RESTful wrapper around the DB.

We assume, that 
- the postgres-db is already installed as a RDS-service and available
via `<db-qtrees.rds>`.
- a EC2-machine is provided and available via the static ip `<ec2>`.

Please exchange the placeholder `<*>` accordantly.

Check, if connecting to database work by running:
```
PGPASSWORD=<your_postgres_password> psql --host=<db-qtrees.rds> --port=5432 --username=postgis --dbname=postgis
```

### Connect to EC2
For the setup, connect to ec2 via `ssh -i "qtrees_aws_birds.pem" ubuntu@<ec2>`.

The accordant PEM-file is stored in qtrees-1password-vault and must be locally stored in `~/.aws`.

Ensure that 2 files are available on the ec2-machine:
1. `docker-compose.yml` to run postgREST
1. `set_environment.sh` to set up environment variables.

You can either check them out via git (see Setup git) and adapt the required files.
Or copy the required files from remote.

### Docker
First, install docker on the ec2 machine by following the instructions in:
https://docs.docker.com/engine/install/ubuntu/

Second, install docker-compose:
`sudo apt install docker-compose`

Allow user to run docker:
https://docs.docker.com/engine/install/linux-postinstall/

### Git
Using git, you have to access to qtrees-repo.

**Note: git setup is not necessary to run postgREST on the ec2**
- create ssh key locally: `ssh-keygen -t rsa -b 4096 -C "ubuntu@<ec2>"`
- add public key as deploy key to github
- checkout code

### Mini-conda
We use mini-conda for providing the needed python packages.
To install conda, follow these steps
- Download conda via: `wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh`
- Run installation via: `sh Miniconda3-py39_4.12.0-Linux-x86_64.sh`
- Remove download: `rm Miniconda3-py39_4.12.0-Linux-x86_64.sh`
- To use conda, re-login or run `source .bashrc`


Create environment via `conda env create --file=requirements.yaml`

If conda is slow, try this:
```
conda update -n base conda
conda install -n base conda-libmamba-solver
conda config --set experimental_solver libmamba
```

Alternatively, try to set `conda config --set channel_priority false`.
Run `conda update --all --yes` to update packages.

**If conda is stucked, install the conda environment manually by creating empty env.**

Therefore, create environment `conda create -n qtrees python==3.10.6`.
Install packes from `requirements.yaml` individually.


### Database structure
You can setup the database structure from your local machine - as long as the database is opened to the public.

Therefore:
1. Adapt variables in `set_environment.sh`.
2. Run `source set_environment.sh`
2. Run `source create_sql_files.sh` to create sql files with set environment variables.
3. Run script `source setup_database.sh` to setup postgis and init db.
Check for error message.

For running it on RDS, you need to ensure this line in `set_environment.sh`
```
export CMD_GIS_ADMIN="GRANT rds_superuser TO gis_admin;" # with rds
```

You can try to login to the new `qtrees` database by:
```
PGPASSWORD="${POSTGRES_PASSWD}" psql --host=$DB_QTREES --port=5432 --username=postgres --dbname=qtrees
```

**Note: On the existing ec2-machine, there is already a `set_environment.sh` with all variables set. You can use it as a blueprint.**

The postgis-setup is inspired from https://postgis.net/install/.

The setup of postgREST is based on:
- https://postgrest.org/en/stable/auth.html
- https://postgrest.org/en/stable/tutorials/tut1.html

The setup of JWT in postgres is taken from:
 https://github.com/michelp/pgjwt.

### Get intial data into database
First, run `source set_environment.sh`.

In the same shell run:
- activate conda environment with `conda activate qtrees`. See also chapter **Mini-conda**.
- go to project root directory and run `export PYTHONPATH=$(PWD)` to make module `qtrees` available.
- run `python scripts/script_store_trees_in_db.py` to get tree data into db (once)
- run `python scripts/script_store_soil_in_db.py` to get soil data into db (once)
- run `python scripts/script_store_wheather_observations.py` to store latest data from weather stations
- run `python scripts/script_store_radolan_in_db.py` to store latest radolan data
- run `python scripts/script_store_shading_index_in_db.py` to store the shading index
- run `python script/script_store_gdk_watering_in_db.py` to store GdK watering data

**Note: Die RDS-Instanz ist gerade sehr klein was Ressourcen angeht (aber dafür günstig).
Deswegen kann das Schreiben in die DB recht lange dauern.
Z.B. das Bäume schreiben kann schon mal 30-45 Minuten dauern.**

Do want to get new data into the db?

It is really simple, if the data is provided in `geopandas`:
- Just write to the db (see chapter "Write data from python")
- connect to db and check via `\d api.<table>`, how the generated table looks like.
- add new table definition to `infrastructure/database/03_setup_table.template.sql`

### Database backups
Instead of loading data into the db from scratch, you can also dump data into a file and restore from file.
- Run `. scripts/script_backup_db_data.sh` to dump data into a file. The DB structure is not part of the backup.
- Run `. scripts/script_restore_db_data.sh` to restore data from that file.

By default, the data is stored into `data/db/<qtrees_version>`. If you run it locally, `qtrees_version` is set as `local`.

If you want to store somewhere else, just provide the destination folder, e.g.
```
. scripts/script_backup_db_data.sh data/foo
```

Note:
- The postfix `<qtrees_version>` is automatically appended to the data directory.
- If you get the message `pg_dump: error: aborting because of server version mismatch`, deactivating the conda env might be a quick fix.

### Clean up database
Just getting rid of the data but not the structure is quite simple.
Run:
```
PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -d qtrees -c "SELECT * from private.truncate_tables()"
```

You want to start from scratch?

You can drop all qtrees databases and roles via:
```
PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -c "DROP DATABASE qtrees WITH (FORCE);" -c "DROP DATABASE lab_gis;" -c "DROP ROLE gis_admin, ui_user, ai_user, authenticator, web_anon;"
```

### Run postgREST
First, run `source set_environment.sh` again.

Run `docker-compose -f docker-compose.yml up -d` to start the postgREST service.

### Insights and administration
There are 2 tools for insights / administration:
- swagger-ui: visualizes `swagger.json` generated by postgREST-API.
- pgadmin: allows to visualize and adapt db

You can run them for remote use via:
`docker-compose -f docker-compose.tools.yml up -d`

Running the local version, the tools are already provided and don't have to be started separatly.

**Note: For local use, you have to provide pgAdmin with `host.docker.internal` instead of `localhost`.**

## Local setup

The aim of the setup is to run:
- a postGIS DB as a docker service
- a postgREST docker as a RESTfull wrapper around the DB
- swagger-ui docker to inspect postgREST
- pgAdmin docker for database administration

The corresponding local infrastructure will look like this:

[![](https://mermaid.ink/img/pako:eNp9U01P4zAQ_Ssjc0mlVo22IKFsFam0BQqs1KVFHNo9OPEktUjiYDuUFeK_rx0noZTdzcHyfL15z5N5I7FgSAKSSlruYD3bFmC-SRAETMRPKJ09PbLnR_blkT3xvHEUlillOS_GwygcRzIc83CPEVw9LCAREpZC6VTi6ufdeMhdguUS8pymCKw057BFMMFSSA1n_pnf6zU9YDAYwMVmKoqEp5Wkmovil4tdmFg4rUnUbWwX2HO9c0jGwxXgq8ZCmaKO4EH_Jukrg9PRN8vA9Zk5neo5OxA5vfu_wEzENANeKE0zU1f7WlEzJ6rFn39IuJ-v1v8kKlHpjuLI9_0D2GZCNdJqT9MU5WS5-BuUclFa8mFzHVS8gz33z7_CNjRr1jebpRQvnCFYrrAoNMqExtjM5MbOBK49r47yNmrxJ3GMSoEWYOfEIut74dThSHyujDzVPtF1jTN1xpXnPSiUcN8k2cpEihweMer1alq3nmcMuJTCtCzYB_dbGzaMuieq0xebtQGCzyQbCQvoCpwjzqhSM0zA_fyQ8CwLThgmfaWleMLgZBS398GeM70LTsvX76RPcpQ55cxs3puF2hK9wxy3JDBXU0-rTG_Jtng3qVXJqMY541pIEiQ0U9gntNJi9buISaBlhW3SjFOzyHmXhXXRD7fi9aa__wGC3EBQ)](https://mermaid.live/edit#pako:eNp9U01P4zAQ_Ssjc0mlVo22IKFsFam0BQqs1KVFHNo9OPEktUjiYDuUFeK_rx0noZTdzcHyfL15z5N5I7FgSAKSSlruYD3bFmC-SRAETMRPKJ09PbLnR_blkT3xvHEUlillOS_GwygcRzIc83CPEVw9LCAREpZC6VTi6ufdeMhdguUS8pymCKw057BFMMFSSA1n_pnf6zU9YDAYwMVmKoqEp5Wkmovil4tdmFg4rUnUbWwX2HO9c0jGwxXgq8ZCmaKO4EH_Jukrg9PRN8vA9Zk5neo5OxA5vfu_wEzENANeKE0zU1f7WlEzJ6rFn39IuJ-v1v8kKlHpjuLI9_0D2GZCNdJqT9MU5WS5-BuUclFa8mFzHVS8gz33z7_CNjRr1jebpRQvnCFYrrAoNMqExtjM5MbOBK49r47yNmrxJ3GMSoEWYOfEIut74dThSHyujDzVPtF1jTN1xpXnPSiUcN8k2cpEihweMer1alq3nmcMuJTCtCzYB_dbGzaMuieq0xebtQGCzyQbCQvoCpwjzqhSM0zA_fyQ8CwLThgmfaWleMLgZBS398GeM70LTsvX76RPcpQ55cxs3puF2hK9wxy3JDBXU0-rTG_Jtng3qVXJqMY541pIEiQ0U9gntNJi9buISaBlhW3SjFOzyHmXhXXRD7fi9aa__wGC3EBQ)

Everything is a pre-defined, ready-to-use docker image :)

This is helpful for debugging but not used for deployment.

For local setup, you need the files:
1. `set_environment.local.sh`
2. `docker-compose.local.yml`

**Note: Instead of using a RDS database, the local setup run a postgres-db as a local docker service.**

### Step-by-Step guide

From the project root directory, execute the following steps in the **same shell**, since the scripts depend on environment variables.

#### Install dependencies
- install `psql`
  - `brew install libpq`
  - propably, you have to run `brew link --force libpq` as well
- install `docker`
  - follow instructions [here](https://docs.docker.com/desktop/mac/install/)
- install `docker-compose`
  - `brew install docker-compose`

#### Start `docker` containers for database
- `cd infrastructure/database`
- `source set_environment.local.sh`
- `docker-compose -f docker-compose.local.yml up -d`
- `docker container ls`
- you should see now two running containers:
  - `postgrest` at port `3000`
  - `postgis` at port `5432`
- the database is not yet configured, so you cannot interact with it yet
- ignore the error message of postgREST as it cannot connect to the db before configuration

#### Configure database
- `source set_environment.local.sh`
- `source create_sql_files.sh`
- `source setup_database.sh`
- `docker-compose -f docker-compose.local.yml restart` to make changes visible
- read the database password from environment variables with this command:
- `echo $POSTGRES_PASSWD`
- you should now be able to access the database hosted in the `docker` container like so:
- `psql -p 5432 -h localhost -U postgres`
- use the password obtained above to log in
- type `\q` to exit the `psql` interactive shell
- in your browser, you should see some `swagger` output generated by `PostgREST` when accessing the address `localhost:3000`

#### Start `swagger` and `pgadmin`
- `source set_environment.local.sh`
- `docker-compose -f docker-compose.tools.yml up -d`
- `docker container ls`
- you should see now four running containers:
  - `postgrest` at port `3000`
  - `postgis` at port `5432`
  - `swagger-ui` at port `8080`
  - `pgadmin4` at port `5050`
- access `swagger` via browser at address `localhost:8080`
  - on top of the `swagger` landing page, change address to `localhost:3000` and click "Explore"
  - you should be able to issue REST requests to the database
  - the database does not yet contain any data
- access `pgadmin` via browser at address `localhost:5050`
  - login with user `admin@admin.com`
  - password is `root`

#### Fill the local db with data (**this might take up to a few hours**)
- make sure the database is running and configured as described above
- activate conda environment with `conda activate qtrees`. See also chapter **Mini-conda** above.
- go to project root directory and run `export PYTHONPATH=$(PWD)` to make module `qtrees` available.
- run `python scripts/script_store_trees_in_db.py` to get tree data into db (once)
- run `python scripts/script_store_soil_in_db.py` to get soil data into db (once)
- run `python scripts/script_store_wheather_observations.py` to store latest data from weather stations
- run `python scripts/script_store_radolan_in_db.py` to store latest radolan data
- run `python scripts/script_store_shading_index_in_db.py` to store the shading index
- run `python scripts/script_store_gdk_watering_in_db.py` to store the watering data of GdK
- restart docker to make changes available to other services via `docker-compose -f docker-compose.local.yml restart`


#### Resetting local db
If you are not happy with your database setup and want to delete the db:
- shut down docker container
- delete directories `pgadmin` and `pgdata`
- start docker container again.

For running it locally, ensure the following line in `set_environment.local.sh`:
```
export CMD_GIS_ADMIN="ALTER ROLE gis_admin SUPERUSER;" # local use
```


## Run

You can always run the services via: 
```
source set_environment.sh
docker-compose -f docker-compose.yml up -d
```

To turn it down, run:
`docker-compose -f docker-compose.yml down`

**Note: if you run it locally, you have of course to use `docker-compose.local.yml` and `set_environment.local.sh`.**

### Get data in python
To connect to the database, run the following lines in python:

```
from sqlalchemy import create_engine  
from geopandas import GeoDataFrame
import geopandas

db_connection_url = "postgresql://postgres:<your_password>@<host_db>:5432/qtrees"
con = create_engine(db_connection_url)  

sql = "SELECT * FROM api.soil"
soil_gdf = geopandas.GeoDataFrame.from_postgis(sql, con, geom_col="geometry") 
```
You have of course to adapt the parameter `<your_password>` and `host_db`. 

### Write data from python
One can also write data into the database, like:
```
db_connection_url = "postgresql://postgres:<your_password>@<host_db>:5432/qtrees"
engine = create_engine(db_connection_url)
soil_gdf.to_postgis("soil", engine, if_exists="append", schema="api")
```
assuming that `soil_gdf` is a geopandas dataframe.

### use postgREST 

(1) Login via
```
curl -X 'POST' \
  'http://<host_db>:3000/rpc/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "string",
  "pass": "string"
}'
```
and remember output as token.

**Currently, a token is not needed for reading data.**

(2) Set token: `export TOKEN=<your_token>`

(3) Get data via
```
curl -X 'GET' \
  'http://<host_db>:3000/weather_stations' \
  -H 'accept: application/json' \
  -H 'Range-Unit: items'
```

(4) Write data
For writing data, a token is needed in general.
You can provide a token like this:
```
curl -X 'POST'   'http://0.0.0.0:3000/trees'   -H 'accept: application/json'   -H 'Content-Type: application/json'   -d '{
  "gml_id": "string",
  "baumid": "string",
  [..]
}' -H "Authorization: Bearer $TOKEN" 
```


**Note: the provided JWT_SECRET is used to encrypt and validate the token.**

**Note: the size of JWT_SECRET must greater equal 32.**

You can test and validate the jwt token via:
https://jwt.io/

This is quite usefull for debugging.

JWT token consists of a header:
```
{
  "alg": "HS256",
  "typ": "JWT"
}
```
and a payload, e.g.
```
{
  "role": "ai_user",
  "email": "nico@birdsonmars.com",
  "exp": 1655049037
}
```

If you add new tables,
also think of adding/updating permissions to user roles.
For example:

```sql
grant usage on schema api to ai_user;
grant all on api.trees to ai_user;
grant all on api.radolan to ai_user;
grant all on api.forecast to ai_user;
grant all on api.nowcast to ai_user;
grant all on api.soil to ai_user;
grant all on api.weather to ai_user;
grant all on api.weather_stations to ai_user;
[...]
grant select on api.user_info to ai_user;
```

**Note: tables not exposed to anonymous user `web_anon` will not be visible in postgREST**

## User managment
### Create db user
Create "admin"-user
```sql
CREATE USER <user_name> WITH PASSWORD '<password>';
GRANT CONNECT ON DATABASE qtrees TO <user_name>;
GRANT USAGE ON SCHEMA api TO <user_name>;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA api TO <user_name>;
-- to grant access to the new table in the future automatically:
ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT, INSERT, UPDATE ON TABLES TO <user_name>;
```

Create "read-only yser"
```sql
CREATE USER <user_name> WITH PASSWORD '<password>';
GRANT CONNECT ON DATABASE qtrees TO <user_name>;
GRANT USAGE ON SCHEMA api TO <user_name>;
GRANT SELECT ON ALL TABLES IN SCHEMA api TO <user_name>;
-- to grant access to the new table in the future automatically:
ALTER DEFAULT PRIVILEGES IN SCHEMA api
GRANT SELECT ON TABLES TO <user_name>;
```

### Create postgREST user
To add a postgREST, connect to db and run:
```
insert into basic_auth.users (email, pass, role) values ('nico@birdsonmars.com', 'qweasd', 'ai_user');
```
Of course, adapt `email`, `pass` and `role` as needed
Currently, we have 2 roles: `ai_user` and `ui_user`.

## Open issues

### jwt_secret in db config
In documentation, the `jwt_secret` is set via:
`ALTER DATABASE qtrees SET "app.jwt_secret" TO 'veryveryveryverysafesafesafesafe';`

That doesn't work on RDS.

### rds_superuser
RDS uses `rds_superuser` instread of `superuser`.
Therefore, the installation of postgis differs a bit:

`GRANT rds_superuser TO gis_admin;` vs `ALTER ROLE gis_admin SUPERUSER;`

