export  DJANGO_SUPERUSER_NAME ="admin"
export  DJANGO_SUPERUSER_EMAIL ="admin@my.company"
export  DJANGO_SUPERUSER_PASSWORD ="adminpass"

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --noinput
daphne secoder.asgi:application -b 0.0.0.0 -p  $BIND
