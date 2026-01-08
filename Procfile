web: gunicorn prmms.wsgi --log-file -
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
