from pyexpat import model
from re import M
from django.db import models

# Create your models here.


class Passenger(models.Model):
    name = models.CharField(unique=True, max_length=500) #openid
    status = models.CharField(max_length=100, default='0', blank=True)#0 空闲 1有订单 2 接到
    order_id = models.BigIntegerField(default=-1, blank=True)
    position = models.IntegerField(default=0, blank=True) #poi编号


class Driver(models.Model):
    name = models.CharField(unique=True, max_length=500) #openid
    status = models.CharField(max_length=100, default='0', blank=True)
    order_id = models.BigIntegerField(default=-1, blank=True)
    position = models.IntegerField(default=0, blank=True) 


class SessionId(models.Model):
    sessId=models.CharField(max_length=500)  # 加密后的sessionID
    username=models.CharField(unique=True, max_length=500)  # openID
    job=models.CharField(max_length=100)


class Order(models.Model):
    passenger=models.ForeignKey(
        Passenger, on_delete=models.CASCADE)
    driver=models.CharField(max_length=500) #openid
    departure=models.IntegerField(default=0, blank=True)
    dest_lat=models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    dest_lon=models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    match_time=models.FloatField(default=0, blank=True)
    status=models.CharField(max_length=10, default='0', blank=True) # 0进行中 1匹配好 2已完成


class Poi(models.Model):
    lat=models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    lon=models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
