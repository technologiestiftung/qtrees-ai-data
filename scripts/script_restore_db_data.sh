if [ -n "$QTREES_VERSION" ]; then
  if [ -n "$QTREES_BACKUP_DIR" ]; then
    # given dir as variable
    data_dir=$QTREES_BACKUP_DIR"/"$QTREES_VERSION
  else
    # default dir
    data_dir="data/db/"$QTREES_VERSION
  fi

  files=$(ls -t $data_dir/*.psql 2>/dev/null)
  if [ -z "$files" ]; then
    # no dump file found
    echo "Error: No suitable file found in $data_dir"
  else
    # get newest dump-file
    filename=$(ls -t $data_dir/*.psql | head -1)
    # dump data before truncating
    filename_safe="$data_dir/safe.dump"
    PGPASSWORD=${POSTGRES_PASSWD} pg_dump --host $DB_QTREES --port 5432 --username postgres --format custom --file $filename_safe -n public -n private --exclude-table public.spatial_ref_sys --data-only qtrees
    # echo "Truncating data in DB"
    echo "Drop db ..."
    PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -c "DROP DATABASE qtrees WITH (FORCE);"
    echo "Initialize db ..." 
    PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -c "CREATE DATABASE qtrees OWNER postgres;"    
    PGPASSWORD=${POSTGRES_PASSWD} psql --host=$DB_QTREES --port=5432 --username=postgres --dbname=qtrees -a -f scripts/init_db_for_dump.sql
    echo "Loading data into DB from \"$filename\""
    {echo "SET session_replication_role = replica;"; gunzip < $filename; } | PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -d qtrees
  fi
else
  echo "Error: Variable QTREES_VERSION is not set"
fi