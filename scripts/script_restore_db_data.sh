if [ -n "$QTREES_VERSION" ]; then
  echo "Input arguments:"
  for i in "$@"; do
    echo $i
  done
  if [ $# -eq 0 ]; then
    # default dir
    data_dir="data/db/"$QTREES_VERSION
  else
    # custom dir as first parameter
    data_dir=$1"/"$QTREES_VERSION
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
    PGPASSWORD=${POSTGRES_PASSWD} pg_dump --host $DB_QTREES --port 5432 --username postgres --format custom --file filename_safe -n public -n private --exclude-table public.spatial_ref_sys --data-only qtrees
    echo "Truncating data in DB"
    PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -d qtrees -c "SELECT * from private.truncate_tables()"
    echo "Loading data into DB from \"$filename\""
    PGPASSWORD=${POSTGRES_PASSWD} pg_restore --host $DB_QTREES --port 5432 --username postgres $filename --data-only --dbname=qtrees
  fi
else
  echo "Error: Variable QTREES_VERSION is not set"
fi