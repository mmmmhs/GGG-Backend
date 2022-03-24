from re import M
from tkinter import CASCADE
from django.db import models

# Create your models here.


class Passenger(models.Model):
    name = models.CharField(unique=True, max_length=500)
    status = models.CharField(max_length=100, default='0', blank=True)
    positionX = models.FloatField(default=0, blank=True)
    positionY = models.FloatField(default=0, blank=True)


class Driver(models.Model):
    name = models.CharField(unique=True, max_length=500)
    status = models.CharField(max_length=100, default='0', blank=True)
    positionX = models.FloatField(default=0, blank=True)
    positionY = models.FloatField(default=0, blank=True)


class SessionId(models.Model):
    sessId = models.CharField(max_length=500)  # 加密后的sessionID
    username = models.CharField(unique=True, max_length=500)  # openID
    job = models.CharField(max_length=100)


class Order(models.Model):
    passenger = models.ForeignKey(
        Passenger, on_delete=models.CASCADE)
    drivername = models.CharField(max_length=500)
    departureX = models.FloatField(default=0, blank=True)
    departureY = models.FloatField(default=0, blank=True)
    destinationX = models.FloatField(default=0, blank=True)
    destinationY = models.FloatField(default=0, blank=True)
    status = models.CharField(max_length=10, default='0', blank=True)
