#!/bin/sh

set -e

python manage.py collectstatic --noinput --settings=nasjod.settings
python manage.py wait_for_db --settings=nasjod.settings
python manage.py migrate --settings=nasjod.settings

uwsgi --socket :9000 --workers 4 --master --enable-threads --module nasjod.wsgi
