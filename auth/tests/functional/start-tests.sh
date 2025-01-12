#!/bin/sh

while ! nc -z $PSQL_HOST $PSQL_PORT; do
      sleep 2
      echo "Waiting for Postgres"
done

while ! nc -z $REDIS_HOST $REDIS_PORT; do
      sleep 2
      echo "Waiting for Redis"
done

while ! nc -z $API_HOST $API_PORT; do
      sleep 2
      echo "Waiting for API"
done

echo "All services are up and running"

pip install -r /app/tests/functional/requirements.txt

pytest /app/tests/functional/src
