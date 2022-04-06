ENV DJANGO_DB_NAME=default
ENV DJANGO_SU_NAME=admin
ENV DJANGO_SU_EMAIL=admin@my.company
ENV DJANGO_SU_PASSWORD=adminpass

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

RUN python -c "import django; django.setup(); \
   from django.contrib.auth.management.commands.createsuperuser import get_user_model; \
   get_user_model()._default_manager.db_manager('$DJANGO_DB_NAME').create_superuser( \
   username='$DJANGO_SU_NAME', \
   email='$DJANGO_SU_EMAIL', \
   password='$DJANGO_SU_PASSWORD')"
daphne secoder.asgi:application -b 0.0.0.0 -p  $BIND
