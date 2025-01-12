#!/bin/sh
while ! nc -z $ELASTIC_HOST $ELASTIC_PORT; do
      sleep 2
      echo "Waiting for Elasticsearch"
done

while ! nc -z $REDIS_HOST $REDIS_PORT; do
      sleep 2
      echo "Waiting for Redis"
done

echo "All services are up and running"

python src/main.py
