from pyexpat import model
from re import M
from django.db import models
from GGG_backend.models import Driver, Passenger, SessionId, Order, Poi

# Create your models here.


class Passenger(models.Model):
    name = models.CharField(unique=True, max_length=500) #openid
    status = models.CharField(max_length=100, default='0', blank=True)#0 空闲 1有订单 2 接到
    order = models.ForeignKey(Order, null=True, on_delete=models.SET_NULL)
    position = models.IntegerField(default=0, blank=True) #poi编号


class Driver(models.Model):
    name = models.CharField(unique=True, max_length=500) #openid
    status = models.CharField(max_length=100, default='0', blank=True)
    order = models.ForeignKey(Order, null=True, on_delete=models.CASCADE)
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
    dest_name=models.CharField(max_length=50, default='0', blank=True)
    status=models.CharField(max_length=10, default='0', blank=True) # 0订单发起，正在等待司机接单 1司乘匹配完成 2订单结束


class Poi(models.Model):
    lat=models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    lon=models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
