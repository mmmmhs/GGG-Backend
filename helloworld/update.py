import datetime
from helloworld.models import SessionId

def daily_update():
    SessionId.objects.all().delete()