from django.contrib import admin
from GGG_backend.models import Passenger, Driver, SessionId, Order
# Register your models here.

admin.site.register([Passenger, Driver, SessionId, Order])
