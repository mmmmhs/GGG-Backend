import datetime
from GGG_backend.models import SessionId

def daily_update():
    SessionId.objects.all().delete()