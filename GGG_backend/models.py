from pyexpat import model
from re import M
from tkinter import CASCADE
from django.db import models

# Create your models here.


class Passenger(models.Model):
    name = models.CharField(unique=True, max_length=500)
    status = models.CharField(max_length=100, default='0', blank=True)
    order_id = models.BigIntegerField(default=-1, blank=True)
    position = models.IntegerField(default=0, blank=True)


class Driver(models.Model):
    name = models.CharField(unique=True, max_length=500)
    status = models.CharField(max_length=100, default='0', blank=True)
    order_id = models.BigIntegerField(default=-1, blank=True)
    position = models.IntegerField(default=0, blank=True)


class SessionId(models.Model):
    sessId = models.CharField(max_length=500)  # 加密后的sessionID
    username = models.CharField(unique=True, max_length=500)  # openID
    job = models.CharField(max_length=100)


class Order(models.Model):
    passenger = models.ForeignKey(
        Passenger, on_delete=models.CASCADE)
    driver = models.CharField(max_length=500)
    departure = models.IntegerField(default=0, blank=True)
    destination = models.IntegerField(default=0, blank=True)
    status = models.CharField(max_length=10, default='0', blank=True)

class Poi(models.Model):
	lat = models.FloatField(default=0, blank=True)
	lon = models.FloatField(default=0, blank=True)