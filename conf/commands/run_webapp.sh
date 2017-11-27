#!/bin/sh

# wait for PSQL server to start
sleep 10

# migrate db, so we have the latest db schema
python manage.py migrate --noinput

# start development server on public ip interface, on port 8000
python manage.py collectstatic --noinput

# python manage.py runserver 0.0.0.0:8000
gunicorn wsgi:application -w 2 -b :8000