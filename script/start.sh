ENV  DJANGO_SUPERUSER_NAME =admin
ENV  DJANGO_SUPERUSER_EMAIL =admin@my.company
ENV  DJANGO_SUPERUSER_PASSWORD =adminpass

python manage.py makemigrations
if [ $? -ne 0 ]; then
rm -rf /opt/secoder/django_storage/*
python manage.py makemigrations
fi
python manage.py migrate
if [ $? -ne 0 ]; then
rm -rf /opt/secoder/django_storage/*
python manage.py makemigrations
python manage.py migrate

fi
python manage.py createsuperuser --noinput
daphne secoder.asgi:application -b 0.0.0.0 -p  $BIND
