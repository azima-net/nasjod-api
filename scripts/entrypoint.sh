#!/bin/sh

set -e

python manage.py collectstatic --noinput --settings=app.settings
python manage.py wait_for_db --settings=app.settings
python manage.py migrate --settings=app.settings

uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi