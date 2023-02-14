if [ -n "$QTREES_VERSION" ]; then
  if [ $# -eq 0 ]; then
    # default dir
    data_dir="data/db/"$QTREES_VERSION
  else
    # custom dir as first parameter
    data_dir=$1"/"$QTREES_VERSION
  fi
  files=$(ls -t $data_dir/*.sql 2>/dev/null)
  if [ -z "$files" ]; then
    # no dump file found
    echo "Error: No suitable file found in $data_dir"
  else
    # get newest dump-file
    filename=$(ls -t $data_dir/*.sql | head -1)
    echo "Truncating data in DB"
    PGPASSWORD=${POSTGRES_PASSWD} psql --host $DB_QTREES -U postgres -d qtrees -c 'TRUNCATE TABLE public.issues, public.issue_types, public.weather, public.radolan'
    echo "Loading data into DB from \"$filename\""
    PGPASSWORD=${POSTGRES_PASSWD} pg_restore --host $DB_QTREES --port 5432 --username postgres $filename --data-only --dbname=qtrees
  fi
else
  echo "Error: Variable QTREES_VERSION is not set"
fi