import datetime
from login.models import SessionId

def daily_update():
    SessionId.objects.all().delete()