from django.db import models

# Create your models here.


class Passenger(models.Model):
    name = models.CharField(
        primary_key=True, unique=True, max_length=500)  # openid
    status = models.CharField(
        max_length=100, default='0', blank=True)  # 0=unactive 1=匹配池 2=已匹配池 3=运客中 4=待支付
    myorder_id = models.IntegerField(default=-1)
    position = models.IntegerField(default=0, blank=True)  # poi编号


class Driver(models.Model):
    name = models.CharField(
        primary_key=True, unique=True, max_length=500)  # openid
    status = models.CharField(
        max_length=100, default='0', blank=True)  # 0=unactive 1=匹配池 2=已匹配池 3=运客中 4=待支付
    myorder_id = models.IntegerField(default=-1)
    position = models.IntegerField(default=0, blank=True)


class SessionId(models.Model):
    sessId = models.CharField(
        primary_key=True, max_length=500)  # 加密后的sessionID
    username = models.CharField(unique=True, max_length=500)  # openID
    job = models.CharField(max_length=100)


class Order(models.Model):
    mypassenger = models.CharField(max_length=500)  # openid
    mydriver = models.CharField(max_length=500)  # openid
    departure = models.IntegerField(default=0, blank=True)
    dest_lat = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=6)
    dest_lon = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=6)
    match_time = models.FloatField(default=0, blank=True)
    dest_name = models.CharField(max_length=50, default='0', blank=True)
    # 0订单发起，正在等待司机接单 1司乘匹配完成 2订单结束
    status = models.CharField(max_length=10, default='0', blank=True)
    money = models.IntegerField(default = 0)


class Poi(models.Model):
    name = models.CharField(max_length=100, default="")
    latitude = models.DecimalField(default=0, blank=True,
                              max_digits=10, decimal_places=6)
    longitude = models.DecimalField(default=0, blank=True,
                              max_digits=10, decimal_places=6)

class Settings(models.Model):
    price_per_meter = models.IntegerField(default = 1)