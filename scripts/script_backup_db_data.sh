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
  filename=$data_dir"/$now.dump"

  echo "Deleting dumps older than 7 days"
  find $data_dir -name "*.dump" -mindepth 1 -mtime +7 -delete

  echo "Dumping db data into \"$filename\""
  PGPASSWORD=${POSTGRES_PASSWD} pg_dump --host $DB_QTREES --port 5432 --username postgres --format custom --file $filename -n public -n private --exclude-table public.spatial_ref_sys --data-only qtrees
else
  echo "Error: Variable QTREES_VERSION is not set"
fi