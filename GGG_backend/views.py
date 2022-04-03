from unicodedata import name
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
from GGG_backend.models import Driver, Passenger, SessionId, Order, Poi, Settings
import secoder.settings
import random
import string
import hashlib
import logging
logger = logging.getLogger('django')
passenger_unmatched = []  # 待匹配乘客池子
driver_unmatched = []  # 待匹配司机池子
passenger_matched = []  # 已匹配乘客池子
driver_matched = []  # 已匹配司机池子
# openi


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
            orderid = user.myorder_id
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
                    array.append(model_to_dict(
                        poi, fields=['id', 'name', 'latitude', 'longitude']))
                return JsonResponse({'errcode': 0, 'pois': array})
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)

# 司乘匹配 传入openid和job 返回0:匹配成功 -1:需要等待 -2:参数错误


def match(openid, job):
    try:
        if job == "passenger":
            if len(driver_unmatched) > 0:
                user = Passenger.objects.get(name=openid)
                order = user.myorder
                # order.mydriver = driver_unmatched[0]
                order.match_time = time.time()
                # order.status = 1
                Driver.objects.get(name=driver_unmatched[0]).myorder = order
                driver_matched.append(driver_unmatched.pop(0))
                passenger_matched.append(passenger_unmatched.pop(0))
                return 0
            else:
                return -1
        if job == "driver":
            if len(passenger_unmatched) > 0:
                user = Driver.objects.get(name=openid)
                order = Passenger.objects.get(
                    name=passenger_unmatched[0]).myorder
                # order.mydriver = user.name
                order.match_time = time.time()
                user.myorder = order
                # order.status = 1
                driver_matched.append(driver_unmatched.pop(0))
                passenger_matched.append(passenger_unmatched.pop(0))
                return 0
            else:
                return -1
        else:
            return -2
    except Exception as e:
        logger.warning(e)
        return -2

# 检查id对应订单是否超时
# 轮询时调用


def check_time(order_id):
    curtime = time.time()
    order = Order.objects.get(id=order_id)
    if curtime - order.match_time > 30:
        return False
    else:
        return True

# 乘客、司机取消订单（或司机超时）


def cancel_order(openid, job):
    cancel_user, influenced_user, order = None
    if job == "passenger":
        cancel_user = Passenger.objects.get(name=openid)
        order = Order.objects.get(id=cancel_user.myorder_id)
        influenced_user = Driver.objects.get(id=order.mydriver)
    elif job == "driver":
        cancel_user = Driver.objects.get(name=openid)
        order = Order.objects.get(id=cancel_user.myorder_id)
        influenced_user = Passenger.objects.get(id=order.mypassenger)


def passenger_order(request):
    if (request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            origin = reqjson['origin']
            dest = reqjson['dest']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        sessionId = SessionId.objects.get(sessId=sess)
        passengername = sessionId.username
        passenger = Passenger.objects.get(name=passengername)
        errcode = 0
        if not passenger or sessionId.job == 'driver':
            errcode = -10
            return JsonResponse({'errcode': errcode})
        if passenger.status != 0:
            errcode = -1
            return JsonResponse({'errcode': errcode})
        passenger.status = 1
        order = Order.objects.create(mypassenger=passengername, departure=origin, dest_name=dest.name,
                                     dest_lat=dest.latitude, dest_lon=dest.longitude)
        passenger.order = order
        order_id = order.id
        passenger_unmatched.append(passenger)
        return JsonResponse({'errcode': errcode, 'order': order_id})

    elif(request.method == 'GET'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            order_id = reqjson['order']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        sessionId = SessionId.objects.get(sessId=sess)
        passengername = sessionId.username
        passenegr = Passenger.objects.get(name=passengername)
        order = Order.objects.get(id=order_id)
        errcode = -10
        if not passenger:
            return JsonResponse({'errcode': errcode})
        if passenger.status == 0:
            errcode = 0
            return JsonResponse({'errcode': errcode})
        # 司乘匹配 传入openid和job 返回0:匹配成功 -1:需要等待 -2:参数错误
        match_response = match(passengername, 'passenger')
        if match_response == -2:
            return JsonResponse({'errcode': errcode})
        errcode = passenger.status
        return JsonResponse({'errcode': errcode})

        '''poi = Poi.objects.get(id=order.departure)  # ??此处id真的能这么用吗 我不知道
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
        driver = order.mydriver
        driver = driver[0:5]
        return JsonResponse({'errcode': errcode, 'info': driver, 'path': route})'''


def get_order_info(request):
    try:
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        order_id = reqjson['order']
    except Exception as e:
        return HttpResponse("error:{}".format(e), status=405)
    sessionId = SessionId.objects.get(sessId=sess)
    passengername = sessionId.username
    order = Order.objects.get(id=order_id)
    passenger = Passenger.objects.get(name=passengername)
    errcode = 0
    if not order or not passenger:
        errcode = -1
        return JsonResponse({'errcode': errcode})
    drivername = order.mydriver
    driver_info = drivername[0:5]
    passenger_info = passengername[0:5]
    poi = Poi.objects.get(id=order.departure)  # ??此处id真的能这么用吗 我不知道
    response = requests.get('https://restapi.amap.com/v5/direction/driving?key='+secoder.settings.GOD_KEY +
                            '&origin="'+poi.lon+','+poi.lat+'"&destination="'+order.dest_lon+','+order.dest_lat+'"&show_fields=polyline')
    distance = (jsonpath(response, '$.route.paths[0].distance'))
    polylines = (jsonpath(response, '$.route.paths[0].steps[*].polyline'))
    strs = []  # ['lon,lat']
    for polyline in polylines:
        strs.extend(polyline.split(';'))
    path = []
    for str in strs:
        temp = str.split(',')
        path.append({int(temp[0]), int(temp[1])})  # [{lon,lat}]
    money = distance*Settings.price_per_meter
    order.money = money
    return JsonResponse({'errcode': errcode, 'driver_info': driver_info, 'passenger_info': passenger_info, 'path': path, 'money': money})


def get_order_money(request):
    try:
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        order_id = reqjson['order']
    except Exception as e:
        return HttpResponse("error:{}".format(e), status=405)
    sessionId = SessionId.objects.get(sessId=sess)
    passengername = sessionId.username
    order = Order.objects.get(id=order_id)
    passenger = Passenger.objects.get(name=passengername)
    return


def passenger_pay(request):

    return


def driver_order(request):
    if (request.method == 'POST'):  # POST方法，对应的是司机准备接单的环节
        try:
            reqjson = json.loads(request.body)
            sessionId = reqjson['sess']
            origin = reqjson['origin']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.get(sessId=sessionId)  # 找到对应user
        errcode = -1
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode})
        driver = Driver.objects.get(name=user.username)  # 找到对应的司机
        if driver.status == 0:  # 0代表没有订单
            errcode = 0
            driver.status = 1
            driver_unmatched.append(driver.name)
            driver.position = int(origin)
        return JsonResponse({'errcode': errcode})
    if (request.method == 'GET'):
        try:
            sessionId = request.get('sess')
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.get(sessId=sessionId)  # 找到对应user
        orderid = 0
        destination = {}
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode, 'order': orderid, 'destination': destination})
        driver = Driver.objects.get(name=user.username)  # 找到对应的司机
        if driver.status == 1:  # 司机闲着就给他匹配
            matching = match(sessionId)
            if matching == 0:  # 如果匹配上了
                driver.status = 2
            else:
                driver.myorder_id = -1  # 没匹配上的话，打上一个不存在的订单标号
        if driver.status != 0 and driver.status != 1:  # 状态不是0或者1表明有订单，要么是unactive要么是在待匹配池子里
            errcode = 0
            orderid = driver.myorder_id
            order = Order.objects.get(id=orderid)
            destination = {'name': order.dest_name,
                           'latitude': order.dest_lat, 'longitude': order.dest_lon}
        errcode = driver.status
        return JsonResponse({'errcode': errcode, 'order': orderid, 'destination': destination})


def driver_get_order(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            errcode = 0
            user = SessionId.objects.get(sessId=sess)
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -2, 'info': "", 'path': [], 'time': 0})
            driver = Driver.objects.get(name=user.username)
            if not driver or not driver.myorder:
                return JsonResponse({'errcode': -2, 'info': "", 'path': [], 'time': 0})
            orderid = reqjson['order']
            order = Order.objects.get(id=orderid)
            begin_time = order.match_time
            end_time = time.time()
            if end_time - begin_time > 30:
                errcode = -1
                # 取消当前司机状态，与下一司机匹配
                driver.status = 0
                passengerId = driver.myorder.mypassenger
                match(passengerId, "passenger")
            info = order.passenger.name[0:5]
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
