python manage.py makemigrations
python manage.py migrate
daphne secoder.asgi:application -b 0.0.0.0 -p  $BIND