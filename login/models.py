from re import M
from django.db import models

# Create your models here.

class Passenger(models.Model):
    name = models.CharField(unique=True, max_length=500)

class Driver(models.Model):
    name = models.CharField(unique=True,max_length=500)

class SessionId(models.Model):
    sessId = models.CharField(unique=True, max_length=500) #加密后的sessionID
    key = models.CharField(max_length=500) #解密key
    username = models.CharField(unique=True, max_length=500) #openID
    job = models.CharField(max_length=100)