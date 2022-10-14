WHITELIST="\${GIS_PASSWD} \${AUTH_PASSWD} \${JWT_SECRET} \${POSTGRES_PASSWD} \${DB_QTREES} \${CMD_GIS_ADMIN}"

if [ -z "${JWT_SECRET}" ]; then
  echo -e "\033[0;31mERROR: at least one required environment variable is empty. Please adjust script set_environment.sh! \033[0m"
else
  if [ ${#JWT_SECRET} -lt 32 ]; then
    echo -e "\033[0;31mERROR: size of JWT_SECRET must be greater equal 32. Current size is ${#JWT_SECRET}. \033[0m"
  else
    echo "Creating database SQL files"
    echo "Database is: $DB_QTREES"
    for filename in templates/*.template.sql; do
      echo "$(basename "$filename" .template.sql).sql"
      envsubst "$WHITELIST" < $filename > "$(basename "$filename" .template.sql).sql"
    done
  fi
fi