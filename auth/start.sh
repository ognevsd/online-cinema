#!/bin/sh
while ! nc -z $PSQL_HOST $PSQL_PORT; do
      sleep 2
      echo "Waiting for Postgres"
done

while ! nc -z $REDIS_HOST $REDIS_PORT; do
      sleep 2
      echo "Waiting for Redis"
done

echo "All services are up and running"

python src/main.py
# while true
# do
#     sleep 5
# done
