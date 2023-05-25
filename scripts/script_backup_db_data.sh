if [ -n "$QTREES_VERSION" ]; then

  if [ -n "$QTREES_BACKUP_DIR" ]; then
    # given dir as variable
    data_dir=$QTREES_BACKUP_DIR"/"$QTREES_VERSION
  else
    # default dir
    data_dir="data/db/"$QTREES_VERSION
  fi
  # create dir in case of need
  mkdir -p $data_dir
  now=$(date +"%m_%d_%Y")
  filename=$data_dir"/$now.dump"

  echo "Deleting dumps older than 7 days"
  find $data_dir -mindepth 1 -name "*.dump" -mtime +7 -delete

  echo "Dumping db data into \"$filename\""
  PGPASSWORD=${POSTGRES_PASSWD} pg_dump --host $DB_QTREES --port 5432 --username postgres --format custom --file $filename -n public -n private --exclude-table public.spatial_ref_sys qtrees
else
  echo "Error: Variable QTREES_VERSION is not set"
fi