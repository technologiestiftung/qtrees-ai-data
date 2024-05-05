![Qtrees](data/img/QtreesDefault.jpg)

# qtrees - data and AI backend

This repository is related to **Quantified Trees** – a project funded by the Federal Ministry for the Environment, Nature Conservation and Nuclear Safety of Germany

The main goal (in short) is to compute daily sensor nowcasts and forecast for all street trees in Berlin. For more information on the project or if you want to reach out to us for general inquiries about the project, see the projects' [landing page](https://qtrees.ai/). 

The structure of this repository is as follows:
```
qtrees-ai-data/
├── qtrees/             Python packages for data retrieval and computing sensor now- and forecasts
├── scripts/            Python and shell scripts for regular tasks and initials setup 
├── data/               Placeholder for downloaded and processed data
├── test/               Unit and integration tests
└── infrastucture/
    ├── database/       SQL database setup
    ├── scheduling/     Crontabs for scheduling of regular tasks
    └── terraform/      Terraform files for provision of required infrastructure
        └── ansible/    Ansible files for providing data and starting services on ec2
```

The following chapters are organized as follows:, 
1. Use of **Terraform** to provide infrastructure on **AWS**
2. Use **Ansible** to setup services on **AWS** EC2
3. Run a **local** setup (**without AWS**)
4. **Everyday use**
5. **Open issues** and **additional resources**



## 1. Provision of infrastructure with terraform

The aim of the setup is to create a:
- a **postGIS** database as an AWS RDS-service
- **postgREST**-Server as a RESTful wrapper around the DB.

In the following, we assume that we are using two AWS environments:
- `dev`-environment with `set_variables.dev.sh`
- `prod`-environment with `set_variables.prod.sh`

**Note: in the current qtrees setup, these files are shared in 1password.**

The set_variables-Skript sets all environment variables needed for using
- `terraform` for creating the infrastructure
- `ansible` for setting up the ec2-instance

**Note: skip chapter (1), if infrastructure already exists.**


Local requirements are:
- [terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
- [ansible-playbook](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)

### 1.1 Place config files
For (1password-)shared config files
- Place the shared `set_variables.dev.sh` and `set_variables.prod.sh` in your local `infrastructure/terraform`-directory.
- Place a (1password)-shared `id_rsa_qtrees` into your local `~/.ssh`-directory.

Or, if creating from scratch, 
- Create a new public-private keypair (used to establish a connection between Ansible and EC2 instance) by ```
ssh-keygen -t rsa```. 
- Insert your credentials into 
`infrastucture/terraform/set_variables.sh` and adjust variables.


### 1.2 Terraform file
The main `terraform`-file is 
`infrastructure/terraform/main.tf`

It contains the component
```
backend "s3" {
    bucket = "qtrees-terraform"
    key    = "tfstate"
    region = "eu-central-1"
}
```
which makes terraform store the state in a s3-bucket.
Adjust this part if using a different s3 bucket or remove this part, if you want to store the state locally.

In the following, we are using the terminal and are running all commands from the `terraform` directory.
Therefore, go from the project root directory to the terraform directory :
```
cd infrastructre/terraform
```
### 1.3 Possible adjustments
**Subnets**

Currently, we are using only a single `public_subnet`.

You can add the following line
```
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
```
to get an additional private subnet and assign e.g. the RDS-instance to it.

**Elastic IPs**

Currently, we using a static IPs for dev- and prod-environment by using
```
# re-use existing elastic ip (if set)
data "aws_eip" "qtrees" {
  public_ip = "${var.ELASTIC_IP_EC2}"
}
```

If you want to use dynamic IPs, use the following lines instead:
```
resource "aws_eip" "qtrees" {
  instance = aws_instance.qtrees.id

  tags = {
    Name = "${var.project_name}-iac-${var.qtrees_version}"
  }
}
```

Then,
- To receive the public IPv4 DNS run
```terraform output -raw dns_name```
- for ec2-adress
```terraform output -raw eip_public_dns```



### 1.4 Running it for the first time

If using it for the first time, create workspace for `dev` and `prod` first:
```
terraform workspace new dev
terraform init 
```
Adjust for `prod` accordantly.

**Note: in the current qtrees setup: dev is called staging and prod is called production**

You can list and switch workspaces by
```
terraform workspace list
terraform workspace select staging
```

### 1.5 Run it (again)

To set up the dev-environment, 
- run `terraform workspace select dev` to select the proper workspace
- run ``set_variables.dev.sh`` to set up the accordant environment file (here: dev-environment).


Run
```
terraform plan
```
If okay, run
```
terraform apply [-auto-approve]
```
and follow the instructions to apply the `main.tf` script.

### 1.6 Destroy

To rollback provisioned services if not needed anymore, run
```
terraform destroy
```



## 2. Software setup with ansible

### 2.1 Prepare environment on local machine

**Set environment variables**

If you want to deploy on **DEV**, set accordant variables by running in a **local** terminal: 
```
. infrastructure/set_variables_private.dev.sh
```

Or, for **PROD**, run 
```
. infrastructure/set_variables_private.prod.sh
```

Note: Make sure that the correct branch is defined by `GIT_BRANCH` within the script.


**Host-file**

After a fresh terraform run, the file
```
infrastructure/terraform/ansible/hosts
``` 
is automatically generated.

If not available, place the file manually with the following lines:
```
[qtrees_server:vars]
ansible_ssh_private_key_file=~/.ssh/id_rsa_qtrees
[qtrees_server]
<ip-adress>
```
The placeholder `<ip-adress>` has to be set to the ip-adresse of the
**DEV**- or **PROD**-machine.





### 2.2 Run playbook
There are two playbooks available. Run
- `playbooks/setup-ubuntu.yml` after a fresh terraform run
- `playbooks/update-ubuntu.yml` if you want to update the database and the code base only.

In the following, we are using the `setup-ubuntu.yml`. Adjust the commands accordantly, if using the update-playbook.


Run
```
ANSIBLE_STDOUT_CALLBACK=yaml ansible-playbook -vv -i ansible/hosts ansible/playbooks/setup-ubuntu.yml
```
in your local terminal from the `infrastructure`-directory and make yourself a coffee.

Check
```
infrastructure/ansible/playbooks/setup-ubuntu.yml
```
for the entire deployment procedure.
And adjust setup if needed.

Note:
- Use `-v` to `-vvv` options to receive additional debug information.
- Set `ANSIBLE_STDOUT_CALLBACK=yaml` to get human-readable output.

### 2.3 SSH into provisioned EC2 machine:
Run
```
ssh -i ~/.ssh/id_rsa_qtrees ubuntu@$TF_VAR_ELASTIC_IP_EC2
```
You can also set the IP directly instead of using `TF_VAR_ELASTIC_IP_EC2`.


Before, you need to
- source the proper environment file
- properly place `id_rsa_qtrees`



## 3. Run it locally

The main aim of the setup is to run:
- a postGIS DB as a docker service
- a postgREST docker as a RESTfull wrapper around the DB

Additionally, you might run a
- swagger-ui docker to inspect postgREST
- pgAdmin docker for database administration

Everything is a pre-defined, ready-to-use docker image :)

**Note: Local setup is helpful for debugging but not used for deployment.**

For local setup, you need the files:
1. `set_environment.local.sh`
2. `docker-compose.local.yml`

**Note: Instead of using a RDS database, the local setup run a postgres-db as a local docker service.**

### 3.1 Requirements

Install requirements:
- install `psql`
  - `brew install libpq`
  - probably, you have to run `brew link --force libpq` as well
- install `docker`
  - follow instructions [here](https://docs.docker.com/desktop/mac/install/)
- install `docker-compose`
  - `brew install docker-compose`
- install `Golang-Migrate` 
  - `brew install golang-migrate` 
  
Check config files:
- Adjust `set_environment.local.sh` or place shared file (from 1password).
  
  
### 3.2 Start `docker` containers for database
From the project root directory, execute the following steps in the **same shell**, since the scripts depend on environment variables.
```
cd infrastructure/database
source set_environment.local.sh
docker-compose -f docker-compose.local.yml up -d
```

Note:
- Running `docker container ls`, you should see now two running containers:
  - `postgrest` at port `3000`
  - `postgis` at port `5432`
- The database is not yet configured, so you cannot interact with it yet
- Ignore the error messages of postgREST as it cannot connect to the db before configuration

### 3.3 Configure database
Run:
```
source set_environment.local.sh
source init_db.sh
migrate -database postgresql://postgres:${POSTGRES_PASSWD}@${DB_QTREES}:5432/qtrees?sslmode=disable -path migrations up
docker-compose -f docker-compose.local.yml restart
```

Note:
- `docker-compose restart` is needed to make changes visible
- you should now be able to access the database hosted in the `docker` container with:
    - `PGPASSWORD=${POSTGRES_PASSWD} psql -p 5432 -h localhost -U postgres`
    - type `\q` to exit the `psql` interactive shell
- in your browser, you should see some `swagger` output generated by `PostgREST` when accessing the address `localhost:3000`

### 3.4 Start `swagger` and `pgadmin`
Run:
```
source set_environment.local.sh
docker-compose -f docker-compose.tools.yml up -d
```

Note:
- Running `docker container ls`, you should see now four running containers:
  - `postgrest` at port `3000`
  - `postgis` at port `5432`
  - `swagger-ui` at port `8080`
  - `pgadmin4` at port `5050`
- Access `swagger-ui` via browser at address `localhost:8080`
  - on top of the `swagger-ui` landing page, change address to `localhost:3000` and click "Explore"
  - you should be able to issue REST requests to the database
  - the database does not yet contain any data at the beginning
- Access `pgadmin` via browser at address `localhost:5050`
  - login with user `admin@admin.com`
  - password is `root`

### 3.5. Fill the local db with data
- Make sure the database is running and configured as described above
- Activate conda environment with `conda activate qtrees`. See also chapter **Mini-conda** above.
- Go to project root directory and run `export PYTHONPATH=$(PWD)` to make module `qtrees` available.
- Run Python scripts accordant to `infrastructure/terraform/ansible/playbooks/setup-ubuntu.yml`
    - step `fill database (static data)`
    - step `fill database (dynamic data)`
- Optional:
    - Load private data into db (extra repo)
    - Run training
    - Run inference
- Restart docker to make changes available to other services via `docker-compose -f docker-compose.local.yml restart`

**Note:**
- **Setup might take up to a few hours!**
- **The ansible playbook `infrastructure/terraform/ansible/playbooks/setup-ubuntu.yml` is the current single point of truth 
w.r.t filling the database with content.**
- **You might also consider the step `s3 sync` in the playbook as a first step to get shared data.**

#### 3.6 Golang Migrate - Database change management

Info: https://github.com/golang-migrate/migrate

Golang migrate is used to take care and track of database changes. The current migrations steps can be found in folder `infrastructure/database/migrations`. In the database, there is a table called `schema_migrations`, which tells which database version we currently have.


This version corresponds to the first number of the migration .sql files. For example, `000002_230301_setup_users.up` is would be database version 2, created 1st of March. 

To add a change to the database structure, go to the `infrastructure/database` folder and run: 
- `source set_environment.local.sh`
- `migrate create -ext sql -dir migrations -seq XXXXXX_informative_name_of_migration`

where XXXXXX is the current date on the form YYMMDD. This will create two files in the `infrastructure/database/migrations` folder, one "up.sql" file, and one "down.sql" file. Implement the change in the "up" file and reverse it in the "down" file. 

To implement the change, run: (If you work on AWS, you have to remove the `?sslmode=disable` to connect to the database)
- `migrate -database postgresql://postgres:${POSTGRES_PASSWD}@${DB_QTREES}:5432/qtrees?sslmode=disable -path migrations up 1`


To reverse the step run: 
- `migrate -database postgresql://postgres:${POSTGRES_PASSWD}@${DB_QTREES}:5432/qtrees?sslmode=disable -path migrations down 1`

**In case of Dirty Database**


Dirty database means that something went wrong with either the 'up' or 'down' migration calls, and this needs to be fixed manually. When fixed, you can let migrate know from which db version to start anew from, with the command: 

`migrate -path migrate -database postgresql://postgres:${POSTGRES_PASSWD}@${DB_QTREES}:5432/qtrees?sslmode=disable force 4` (starting anew from version 4)

When your new up and down migration files work without bugs on the local machine, you can push them to Github as usual. The changes will be implemented with the `playbooks/update-ubuntu.yml` call, which implemented all the migrations starting from the current db version.

For more information on how to use Golang Migrate see: 


https://github.com/golang-migrate/migrate/blob/master/database/postgres/TUTORIAL.md


## 4. Everyday use


### 4.1 Database backups
Instead of loading data into the db from scratch, you can also dump data into a file and restore from file.
- Run `. scripts/script_backup_db_data.sh` to dump data into a file. The DB structure is not part of the backup.
- Run `. scripts/script_restore_db_data.sh` to restore data from that file.

By default, the data is stored into `data/db/<qtrees_version>`. If you run it locally, `qtrees_version` is set as `local`.

If you want to store it somewhere else, just provide the destination folder, e.g.
```
. scripts/script_backup_db_data.sh data/foo
```

Note:
- The postfix `<qtrees_version>` is automatically appended to the data directory.
- If you get the message `pg_dump: error: aborting because of server version mismatch`, deactivating the conda env might be a quick fix.

### 4.2 Clean up database

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

For **local** setup, there is also a simpler way:
- shut down docker container
- delete local directories `pgadmin` and `pgdata`
- start docker container again.

### 4.3 Insights and administration
There are 2 tools for insights / administration:
- swagger-ui: visualizes `swagger.json` generated by postgREST-API.
- pgadmin: allows to visualize and adapt db

You can run them for remote use via:
`docker-compose -f docker-compose.tools.yml up -d`

### 4.4 Get data in Python
To connect to the database, run the following lines in Python:

```
from sqlalchemy import create_engine  
from geopandas import GeoDataFrame
import geopandas

db_connection_url = "postgresql://postgres:<your_password>@<host_db>:5432/qtrees"
con = create_engine(db_connection_url)  

sql = "SELECT * FROM api.soil"
soil_gdf = geopandas.GeoDataFrame.from_postgis(sql, con, geom_col="geometry") 
```
You have of course to adapt the parameter `<your_password>` and `<host_db>`. 

### 4.5 Write data from Python
One can also write data into the database, like:
```
db_connection_url = "postgresql://postgres:<your_password>@<host_db>:5432/qtrees"
engine = create_engine(db_connection_url)
soil_gdf.to_postgis("soil", engine, if_exists="append", schema="api")
```
assuming that `soil_gdf` is a geopandas dataframe.

### 4.6 Use postgREST 

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
  "email": "ai@qtrees.ai",
  "exp": 1655049037
}
```

If you add new tables,
also think of adding / updating permissions to user roles.
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

### 4.7 PostgRest user management

To add a postgREST user, connect to db and run:
```
insert into basic_auth.users (email, pass, role) values ('ai@qtrees.ai', 'qweasd', 'ai_user');
```
Of course, adapt `email`, `pass` and `role` as needed
Currently, we have 2 roles: `ai_user` and `ui_user`.

## 5. Open issues and additional resources

### Shading Calculation
1) Compute solar exposure maps with using `scripts/script_qgis_solar_exposure_maps.py`. This script needs to be run in the Python Console of QGIS. The necessary elevation map tiles could be downloaded from Berlin Open Data Portal. 
2) Smoothen the calculated solar exposure maps with `scripts/script_map_filtering.py`. This script applies a box filter to the given files. The default kernel size is 5.
3) Calculate shading indices with the script `scripts/script_shading_index.py`. This script takes as input the solar exposure maps and tree dataset and calculates 4 seasonal shading indices for each tree in the dataset.
4) Comparison as well as calculation of different interpolation methods between seasonal values could be done with `notebooks/shadow_index.ipynb` in order to obtain 12 monthly values for each tree.


### jwt_secret in db config
In the documentation, the `jwt_secret` is set via:
`ALTER DATABASE qtrees SET "app.jwt_secret" TO 'veryveryveryverysafesafesafesafe';`

That doesn't work on RDS.

### rds_superuser
RDS uses `rds_superuser` instead of `superuser`.
Therefore, the installation of postgis differs a bit:

`GRANT rds_superuser TO gis_admin;` vs `ALTER ROLE gis_admin SUPERUSER;`

### Additional resources

The postgis-setup is inspired from https://postgis.net/install/.

The setup of postgREST is based on:
- https://postgrest.org/en/stable/auth.html
- https://postgrest.org/en/stable/tutorials/tut1.html

The setup of JWT in postgres is taken from:
 https://github.com/michelp/pgjwt.


### Mini-conda
We use mini-conda for providing the needed Python packages.
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
Install packages from `requirements.yaml` individually.