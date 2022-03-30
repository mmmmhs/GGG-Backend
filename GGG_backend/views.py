from jsonpath import jsonpath
from ast import Return
from email.policy import default
import json
from logging import exception
from re import U
import time
from django.forms import ValidationError
from django.forms.models import model_to_dict
from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from GGG_backend.models import Driver, Passenger, SessionId, Order, Poi
import secoder.settings
import random
import string
import hashlib
import logging
logger = logging.getLogger('django')
passenger_for_order = []  # 待匹配乘客池子
driver_for_order = []  # 待匹配司机池子


def index(request):
    return HttpResponse("Hello world.")


def get_wx_response(code):
    response = requests.get("https://api.weixin.qq.com/sns/jscode2session?appid="+secoder.settings.APPID +
                            "&secret="+secoder.settings.APPSECRET+"&js_code="+code+"&grant_type=authorization_code")
    return response.json()


def get_3rd_session(session_key, openId, job):
    data = session_key+openId+job
    data += ''.join(random.sample(string.ascii_letters + string.digits, 8))
    encrypted_data = hashlib.new(
        'md5', bytes(data, encoding="utf8")).hexdigest()
    return encrypted_data


def login(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            code = reqjson['code']
            job = reqjson['job']
        except Exception as e:
            return JsonResponse({'errcode': 403, 'sess': "", 'order': 0})
        data = get_wx_response(code)
        try:
            openID = data['openid']
            sessionID = get_3rd_session(data['session_key'], openID, job)
            print(openID, job)
            try:
                errorcode = data['errcode']
            except Exception:
                errorcode = 0
            if errorcode != 0:
                return JsonResponse({'errcode': errorcode, 'sess': "", 'order': 0})
            if job == 'passenger':
                user = Passenger.objects.get(name=openID)
            elif job == 'driver':
                user = Driver.objects.get(name=openID)
            else:
                user = 0
            if not user:
                errorcode = -10
            SessionId.objects.update_or_create(username=openID, defaults={
                                               "sessId": sessionID, "job": job})
            orderid = -1
            if user.myorder:
                orderid = user.myorder.id
            res = JsonResponse(
                {'errcode': errorcode, 'sess': sessionID, 'order': orderid})
            return res
        except Exception as e:
            return JsonResponse({'errcode': 405, 'sess': "", 'order': 0})


def reg(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        try:
            user = SessionId.objects.get(sessId=sess)
            if(user.job == "passenger"):
                Passenger.objects.create(name=user.username)
            elif(user.job == "driver"):
                Driver.objects.create(name=user.username)
            return JsonResponse({'errcode': 1})
        except Exception as e:
            logger.warning(e)
            return JsonResponse({'errcode': -2})


def pois(request):
    if(request.method == 'GET'):
        try:
            sess = request.GET.get('sess')
            if not SessionId.objects.get(sessId=sess):
                return JsonResponse({'errcode': -2, 'pois': []})
            else:
                array = []
                res = Poi.objects.all()
                for poi in res:
                    array.append(model_to_dict(poi))
                return JsonResponse({'errcode': 0, 'pois': array})
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)


def match(sess):
    sessid = SessionId.objects.get(sessId=sessid)

def order(request):
    if (request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sessionId = reqjson['sess']
            origin = reqjson['origin']
            dest = reqjson['dest']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first() # 需改
        errcode = 0
        if not user or user.status != 1 or user.job == 'driver':
            errcode = -1
            return JsonResponse({'errcode': errcode})
        user.status = 1
        order = Order.objects.create(passenger=user, departure=origin, dest_name=dest.name,
                                     dest_lat=dest.latitude, dest_lon=dest.longitude) # 需改
        order_id = order.id
        return JsonResponse({'errcode': errcode, 'order': order_id})
    elif(request.method == 'GET'):
        try:
            reqjson = json.loads(request.body)
            sessionId = reqjson['sess']
            order_id = reqjson['order']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first() # 需改
        order = Order.objects.filter(passenger=user).first()
        errcode = -1
        if not user or order.status == 0 or user.status == 0:
            return JsonResponse({'errcode': errcode})
        driver = Driver.objects.get(name=order.driver)
        errcode = 0
        poi = Poi.objects.get(id=order.departure)  # ??此处id真的能这么用吗 我不知道
        response = requests.get('https://restapi.amap.com/v5/direction/driving?key='+secoder.settings.GOD_KEY +
                                '&origin="'+poi.lon+','+poi.lat+'"&destination="'+order.dest_lon+','+order.dest_lat+'"&show_fields=polyline')
        distance = (jsonpath(response, '$.route.paths[0].distance'))
        polylines = (jsonpath(response, '$.route.paths[0].steps[*].polyline'))
        strs = []  # ['lon,lat']
        for polyline in polylines:
            strs.extend(polyline.split(';'))
        route = []
        for str in strs:
            temp = str.split(',')
            route.append({int(temp[0]), int(temp[1])})  # [{lon,lat}]
        driver = driver[0:5]
        return JsonResponse({'errcode': errcode, 'info': driver, 'path': route})


def preorder(request):
    if (request.method == 'POST'):  # POST方法，对应的是司机准备接单的环节
        try:
            reqjson = json.loads(request.body)
            sessionId = reqjson['sess']
            origin = reqjson['origin']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first()  # 找到对应user # 需改
        errcode = -1
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode})
        if user.status == 0:  # 0代表没有订单
            errcode = 0
            driver = Driver.objects.get(name=user.username) # 找到对应的司机
            driver.position = int(origin)
        return JsonResponse({'errcode': errcode})
    if (request.method == 'GET'):
        try:
            sessionId = request.get('sess')
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first() # 需改
        errcode = -1
        orderid = 0
        destination = {}
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode})
        # 这里将来用来做司乘匹配
        if user.status != 1:
            errcode = 0
            driver = Driver.objects.get(name=user.username)
            order = driver.myorder
            orderid = order.id
            destination = {'name': order.dest_name,
                           'latitude': order.dest_lat, 'longitude': order.dest_lon}
        return JsonResponse({'errcode': errcode, 'order': orderid, 'destination': destination})


def getorder(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            errcode = 0
            user = SessionId.objects.get(sessId=sess)
            if not user or user.job == 'passenger':
                errcode = -2
            orderid = reqjson['order']
            order = Order.objects.get(id=orderid)
            begin_time = order.match_time
            end_time = time.time()
            if end_time - begin_time > 5:
                errcode = -1
                # 取消当前司机状态，与下一司机匹配
            info = order.passenger.name[0:5]
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
