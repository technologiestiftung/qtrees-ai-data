if [ -n "$QTREES_VERSION" ]; then
  now=$(date +"%m_%d_%Y")
  if [ $# -eq 0 ]; then
    # default dir
    data_dir="data/db/"$QTREES_VERSION
  else
    # given dir as first parameter
    data_dir=$1"/"$QTREES_VERSION
  fi
  # create dir in case of need
  mkdir -p $data_dir
  filename=$data_dir"/dump_$now.sql"

  echo "Deleting dumps older than 7 days"
  find $data_dir -name "*.sql" -mindepth 1 -mtime +7 -delete

  echo "Dumping db data to \"$filename\""
  PGPASSWORD=${POSTGRES_PASSWD} pg_dump --host $DB_QTREES --port 5432 --username postgres --format custom --file $filename --table public.issues --table public.issue_types --table public.weather --table public.radolan --data-only qtrees
else
  echo "Error: Variable QTREES_VERSION is not set"
fi