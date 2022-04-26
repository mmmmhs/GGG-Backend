import time
from django.db import models

# Create your models here.


class Passenger(models.Model):
    name = models.CharField(
        primary_key=True, unique=True, max_length=500)  # openid
    # 0=unactive 1=匹配池 2=已匹配池 3=正在接乘客的路上 4=接到乘客，正在送客 5=待支付
    status = models.IntegerField(default=0, blank=True)
    myorder_id = models.IntegerField(default=-1, blank=True)
    product = models.IntegerField(default=-1, blank=True) # 独乘产品id
    lat = models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    lon = models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    realname = models.CharField(default="", blank=True, max_length=10)
    phone = models.BigIntegerField(default=-1, blank=True)

class Driver(models.Model):
    name = models.CharField(
        primary_key=True, unique=True, max_length=500)  # openid
    # 0=unactive 1=匹配池 2=已匹配池 3=正在接乘客的路上 4=接到乘客，正在送客 5=待支付
    status = models.IntegerField(default=0, blank=True)
    myorder_id = models.IntegerField(default=-1)
    product = models.IntegerField(default=-1, blank=True) # 独乘产品id
    lat = models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    lon = models.DecimalField(default=0, blank=True, max_digits=10, decimal_places=6)
    score = models.FloatField(default=0, blank=True)
    scorenum = models.IntegerField(default=0, blank=True) # 打分次数
    realname = models.CharField(default="", blank=True, max_length=10)
    phone = models.BigIntegerField(default=-1, blank=True)
    carinfo = models.CharField(default="", blank=True, max_length=500)
    carcolor = models.CharField(default="", blank=True, max_length=100)
    carnum = models.CharField(default="", blank=True, max_length=100)


class SessionId(models.Model):
    sessId = models.CharField(
        primary_key=True, max_length=500)  # 加密后的sessionID
    username = models.CharField(unique=True, max_length=500)  # openID
    job = models.CharField(max_length=100)


class Order(models.Model):
    mypassenger = models.CharField(max_length=500)  # openid
    mydriver = models.CharField(max_length=500)  # openid
    origin_name = models.CharField(max_length=50, default='0', blank=True)
    origin_lat = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=6)
    origin_lon = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=6)
    dest_name = models.CharField(max_length=50, default='0', blank=True)
    dest_lat = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=6)
    dest_lon = models.DecimalField(
        default=0, blank=True, max_digits=10, decimal_places=6)
    match_time = models.FloatField(default=0, blank=True)
    start_time = models.FloatField(default=0)  # 发起订单时间戳
    end_time = models.FloatField(default=0, blank=True)
    product = models.IntegerField(default=0,blank=True)
    # 0订单发起，正在等待司机接单 1司乘匹配完成 2订单结束
    status = models.IntegerField(default=0, blank=True)
    money = models.IntegerField(default=0)


class Product(models.Model):
    name = models.CharField(max_length=100, default="")
    price_per_meter = models.FloatField(default=0.002)
    speed = models.FloatField(default=1.0)


class Setting(models.Model):
    products = models.CharField(max_length=1000, default='')

class Area(models.Model):
    name = models.CharField(max_length=100, default="")
    border = models.TextField()
    