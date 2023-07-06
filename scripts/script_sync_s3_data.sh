# example call: QTREES_BACKUP_DIR=/home/ubuntu/qtrees-ai-data/data/db . /home/ubuntu/qtrees-ai-data/scripts/script_sync_s3_data.sh
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

  # sync backups with s3 - delete on s3 if not locally available
  aws s3 sync $data_dir s3://qtrees-data/data/db/$QTREES_VERSION --delete

else
  echo "Error: Variable QTREES_VERSION is not set"
fi