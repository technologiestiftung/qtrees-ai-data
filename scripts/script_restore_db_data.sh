if [ -n "$QTREES_VERSION" ]; then
  if [ -n "$QTREES_BACKUP_DIR" ]; then
    # given dir as variable
    data_dir=$QTREES_BACKUP_DIR"/"$QTREES_VERSION
  else
    # default dir
    data_dir="data/db/"$QTREES_VERSION
  fi

  files=$(ls -t $data_dir/*.dump 2>/dev/null)
  if [ -z "$files" ]; then
    # no dump file found
    echo "Error: No suitable file found in $data_dir"
  else
    # get newest dump-file
    filename=$(ls -t $data_dir/*.dump | head -1)
    # dump data before truncating
    filename_safe="$data_dir/safe.dump"
    echo "safe dump"
    PGPASSWORD=${POSTGRES_PASSWD} pg_dump --host $DB_QTREES --port 5432 --username postgres --format custom --file filename_safe -n public -n private --exclude-table public.spatial_ref_sys --data-only qtrees
    echo "Truncating data in DB"
    PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -d qtrees -c "SELECT * from private.truncate_tables()"
    echo "Loading data into DB from \"$filename\""
    PGPASSWORD=${POSTGRES_PASSWD} pg_restore --host $DB_QTREES --port 5432 --username postgres --dbname=qtrees --clean < $filename
  fi
else
  echo "Error: Variable QTREES_VERSION is not set"
fi
