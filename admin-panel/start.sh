#!/bin/sh
python manage.py collectstatic --noinput

while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
done 

python manage.py migrate

gunicorn --config gunicorn_config.py config.wsgi