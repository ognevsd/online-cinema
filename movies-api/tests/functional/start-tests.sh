#!/bin/sh

while ! nc -z $ELASTIC_HOST $ELASTIC_PORT; do
      sleep 2
      echo "Waiting for Elasticsearch"
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
