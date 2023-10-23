#!/bin/sh

set -e

if [ $DEV != "true" ]; then
    python manage.py wait_for_db
    python manage.py collectstatic --noinput
    python manage.py makemigrations
    python manage.py migrate

    uwsgi --socket :9090 --workers 4 --master --enable-threads --module app.wsgi
fi