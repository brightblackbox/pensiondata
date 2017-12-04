#!/bin/sh

# wait for PSQL server to start
sleep 10

# migrate db, so we have the latest db schema
python /usr/myapp/manage.py migrate --noinput

# start development server on public ip interface, on port 8000
python /usr/myapp/manage.py collectstatic --noinput

gunicorn wsgi:application -w 2 --bind 0.0.0.0:$PORT