#!/bin/sh

while ! nc -z $PSQL_HOST $PSQL_PORT; do
      sleep 5
      echo "Waiting for Postgres"
done

while ! nc -z $ELASTICSEARCH_HOST $ELASTICSEARCH_PORT; do
      sleep 5
      echo "Waiting for Elasticsearch"
done

while ! nc -z $REDIS_HOST $REDIS_PORT; do
      sleep 5
      echo "Waiting for Redis"
done

echo "All services are up and running"

python main.py
