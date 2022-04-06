from jsonpath_ng import jsonpath, parse
import json
from logging import exception
import time
from django.forms.models import model_to_dict
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from GGG_backend.models import Driver, Passenger, SessionId, Order, Poi, Setting
import secoder.settings
import random
import string
import hashlib
import logging
logger = logging.getLogger('django')
formatter = logging.Formatter('%(name)s - %(lineno)d - %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)

passenger_unmatched = []  # 待匹配乘客池子
driver_unmatched = []  # 待匹配司机池子
passenger_matched = []  # 已匹配乘客池子
driver_matched = []  # 已匹配司机池子
# openid


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
            logger.error(e, exc_info = True)
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
                user = Passenger.objects.filter(name=openID).first()
            elif job == 'driver':
                user = Driver.objects.filter(name=openID).first()
            else:
                user = None
            tmp = SessionId.objects.filter(
                username=openID).update(sessId=sessionID, job=job)
            if tmp == 0:
                SessionId.objects.create(
                    username=openID, sessId=sessionID, job=job)
            if not user:
                return JsonResponse({'errcode': -10, 'sess': sessionID, 'order': 0})
            orderid = user.myorder_id
            res = JsonResponse(
                {'errcode': errorcode, 'sess': sessionID, 'order': orderid})
            return res
        except Exception as e:
            logger.error(e, exc_info = True)
            return JsonResponse({'errcode': 405, 'sess': "", 'order': 0})


def reg(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        try:
            user = SessionId.objects.filter(sessId=sess).first()
            if(user.job == "passenger"):
                Passenger.objects.create(name=user.username)
            elif(user.job == "driver"):
                Driver.objects.create(name=user.username)
            return JsonResponse({'errcode': 1})
        except Exception as e:
            logger.error(e, exc_info = True)
            return JsonResponse({'errcode': -2})


def pois(request):
    if(request.method == 'GET'):
        try:
            sess = request.GET['sess']
            if not SessionId.objects.filter(sessId=sess).first():
                return JsonResponse({'errcode': -2, 'pois': []})
            else:
                poi_str = Setting.objects.filter(id=1).first().pois
                poi_list = poi_str.split(',')
                array = []
                for i in poi_list:
                    array.append(model_to_dict(
                        Poi.objects.filter(id=i).first(), fields=['id', 'name', 'latitude', 'longitude']))
                return JsonResponse({'errcode': 0, 'pois': array})
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)

# 司乘匹配 传入openid和job 返回0:匹配成功 -1:需要等待 -2:参数错误
# 修改order.status mydriver


def match(openid, job):
    try:
        if job == "passenger":
            if len(driver_unmatched) > 0:
                user = Passenger.objects.filter(name=openid).first()
                order = Order.objects.filter(id=user.myorder_id).first()
                if not order:
                    return -2
                order.mydriver = driver_unmatched[0]
                order.match_time = time.time()
                order.status = 1
                driver = Driver.objects.filter(
                    name=driver_unmatched[0]).first()
                driver.myorder_id = order.id
                driver_matched.append(driver_unmatched.pop(0))
                passenger_matched.append(passenger_unmatched.pop(0))
                driver.status = 2
                user.status = 2
                driver.save()
                order.save()
                return 0
            else:
                return -1
        elif job == "driver":
            if len(passenger_unmatched) > 0:
                user = Driver.objects.filter(name=openid).first()
                passenger = Passenger.objects.filter(
                    name=passenger_unmatched[0]).first()
                order_id = passenger.myorder_id
                order = Order.objects.filter(id=order_id).first()
                order.mydriver = user.name
                order.match_time = time.time()
                user.myorder_id = order.id
                order.status = 1
                user.status = 2
                passenger.status = 2
                driver_matched.append(driver_unmatched.pop(0))
                passenger_matched.append(passenger_unmatched.pop(0))
                user.save()
                passenger.save()
                order.save()
                return 0
            else:
                return -1
        else:
            return -2
    except Exception as e:
        logger.info(openid)
        logger.error(e, exc_info = True)
        return -2

# 检查id对应订单是否超时)
# 轮询时调用


def check_time(order_id):
    curtime = time.time()
    order = Order.objects.filter(id=order_id).first()
    if curtime - order.match_time > 30:
        return False
    else:
        return True

# 乘客/司机取消订单（或司机超时）
# 修改status myorder_id 改变池子

def cancel_order(openid, job):
    cancel_user, influenced_user, order = None, None, None
    logger.info(openid+' '+job)
    if job == "passenger":
        cancel_user = Passenger.objects.filter(name=openid).first()
        if cancel_user.name in passenger_unmatched:
            passenger_unmatched.remove(cancel_user.name)
        if cancel_user.myorder_id != -1:
            order_id = cancel_user.myorder_id    
        cancel_user.myorder_id = -1    
        if cancel_user.status < 2: # 匹配前取消
            cancel_user.status = 0
            cancel_user.save()
            return
        order = Order.objects.filter(id=order_id).first()
        influenced_user = Driver.objects.filter(name=order.mydriver).first()
        if influenced_user.name in driver_matched:
            driver_matched.remove(influenced_user.name)
            driver_unmatched.insert(0, influenced_user.name)
        if cancel_user.name in passenger_matched:
            passenger_matched.remove(cancel_user.name)    
        influenced_user.myorder_id = -1
    elif job == "driver":
        cancel_user = Driver.objects.filter(name=openid).first()
        if cancel_user.name in driver_unmatched:
            driver_unmatched.remove(cancel_user.name)
        if cancel_user.myorder_id != -1:
            order_id = cancel_user.myorder_id
        cancel_user.myorder_id = -1    
        if cancel_user.status < 2: # 匹配前取消
            cancel_user.status = 0
            cancel_user.save()
            return    
        order = Order.objects.filter(id=order_id).first()
        influenced_user = Passenger.objects.filter(
            name=order.mypassenger).first()
        if influenced_user.name in passenger_matched:
            passenger_matched.remove(influenced_user.name)
            passenger_unmatched.insert(0, influenced_user.name)
        if cancel_user.name in driver_matched:
            driver_matched.remove(cancel_user.name)
    order.status = 0
    influenced_user.status = 1
    cancel_user.status = 0
    order.save()
    cancel_user.save()
    order.save()
    influenced_user.save()

# 访问高德地图接口
# 参数：poi, order 返回(path, distance)元组


def get_path(poi, order):
    response = requests.get('https://restapi.amap.com/v5/direction/driving?key='+secoder.settings.GOD_KEY +
                            '&origin='+str(poi.longitude)+','+str(poi.latitude)+'&destination='+str(order.dest_lon)+','+str(order.dest_lat)+'&show_fields=polyline')

    response = response.json()
    distance = float([match.value for match in parse('$.route.paths[0].distance').find(response)][0])
    polylines =[match.value for match in parse('$.route.paths[0].steps[*].polyline').find(response)]
    strs = []  # ['lon,lat;lon,lat']
    for polyline in polylines:
        strs.extend(polyline.split(';'))
    path = []
    for str1 in strs:
        temp = str1.split(',')
        path.append({"longitude":float(temp[0]), "latitude":float(temp[1])})  # [{lon,lat}]
    return (path, distance)


def passenger_order(request):
    if (request.method == 'POST'):  # 乘客发起订单
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            origin = reqjson['origin']
            dest = reqjson['dest']  # name latitude longitude
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        sessionId = SessionId.objects.filter(sessId=sess).first()
        passengername = sessionId.username
        passenger = Passenger.objects.filter(name=passengername).first()
        errcode = 0
        if not passenger or sessionId.job == 'driver':
            errcode = -10
            return JsonResponse({'errcode': errcode})
        if passenger.status != 0:  # 已有订单
            errcode = -1
            return JsonResponse({'errcode': errcode})
        passenger.status = 1  # 乘客状态0->1
        order = Order.objects.create(mypassenger=passengername, departure=origin, dest_name=dest['name'],
                                     dest_lat=dest['latitude'], dest_lon=dest['longitude'])  # 创建订单
        passenger.myorder_id = order.id
        order_id = order.id
        passenger_unmatched.append(passenger.name)  # 乘客加入未匹配池
        passenger.save()
        return JsonResponse({'errcode': errcode, 'order': order_id})

    elif(request.method == 'GET'):  # 乘客询问订单状态
        try:
            sess = request.GET['sess']
            order_id = request.GET['order']
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        sessionId = SessionId.objects.filter(sessId=sess).first()
        passengername = sessionId.username
        passenger = Passenger.objects.filter(name=passengername).first()
        order = Order.objects.filter(id=order_id).first()
        errcode = -10
        if not passenger:
            return JsonResponse({'errcode': errcode})
        if passenger.status == 0:
            errcode = 0
            return JsonResponse({'errcode': errcode})    
        if check_time(order.id) == False and passenger.status == 2:# 已匹配司机超时
            order = Order.objects.filter(id=passenger.myorder_id).first()
            driver = Driver.objects.filter(myorder_id=order.id).first()
            cancel_order(driver.name, 'driver')
        # 司乘匹配 传入openid和job 返回0:匹配成功 -1:需要等待 -2:参数错误
        match_response = match(passengername, 'passenger')
        if match_response == -2:
            return JsonResponse({'errcode': errcode})
        errcode = passenger.status
        return JsonResponse({'errcode': errcode})


def get_order_info(request):  # 乘客获取当前订单信息
    try:
        sess = request.GET['sess']
        order_id = request.GET['order']
    except Exception as e:
        logger.error(e, exc_info = True)
        return HttpResponse("error:{}".format(e), status=405)
    sessionId = SessionId.objects.filter(sessId=sess).first()
    passengername = sessionId.username
    order = Order.objects.filter(id=order_id).first()
    passenger = Passenger.objects.filter(name=passengername).first()
    errcode = 0
    if not order or not passenger:
        errcode = -1
        return JsonResponse({'errcode': errcode})
    drivername = order.mydriver
    driver_info = drivername[0:5]  # 司机前五位
    passenger_info = passengername[0:5]  # 乘客前五位
    poi = Poi.objects.filter(id=order.departure).first()
    god_ans = get_path(poi, order)
    distance = god_ans[1]
    path = god_ans[0]
    money = distance * poi.price_per_meter
    order.money = money
    order.save()
    return JsonResponse({'errcode': errcode, 'driver_info': driver_info, 'passenger_info': passenger_info, 'path': path, 'money': money})


def get_order_money(request):  # 乘客获取当前订单钱数
    try:
        sess = request.GET['sess']
        order_id = request.GET['order']
    except Exception as e:
        logger.error(e, exc_info = True)
        return HttpResponse("error:{}".format(e), status=405)
    sessionId = SessionId.objects.filter(sessId=sess).first()
    passengername = sessionId.username
    order = Order.objects.filter(id=order_id).first()
    passenger = Passenger.objects.filter(name=passengername).first()
    if not order or not passenger:
        return JsonResponse({'errcode': -1})
    return JsonResponse({'errcode': 0, 'money': order.money})


def get_history_order_info(request):  # 司乘获取历史订单
    if (request.method == 'GET'):
        try:
            sess = request.GET['sess']
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        sessionId = SessionId.objects.filter(sessId=sess).first()
        user_job = sessionId.job
        user_name = sessionId.username
        orders = []
        if user_job == 'passenger':
            passenger = Passenger.objects.filter(name=user_name).first()
            for order in Order:
                if order.mypassenger == user_name:
                    passenger_info = order.mypassenger[0:5]
                    driver_info = order.mydriver[0:5]
                    money = order.money
                    poi = Poi.objects.filter(id=order.departure).first()
                    start_location = poi.name
                    start_time = order.start_time
                    end_time = order.end_time
                    end_location = order.dest_name
                    status = order.status
                    if status == 2:
                        status = 0
                    elif passenger.status == 5:
                        status = 2
                    else:
                        status = 1
                    orders.append({'driver_info': driver_info, 'passenger_info': passenger_info, 'start_time': start_time, 'end_time': end_time,
                                  'money': money, 'start_location': start_location, 'end_location': end_location, 'status': status})

        elif user_job == 'driver':
            for order in Order:
                driver = Driver.objects.filter(name=user_name).first()
                if order.mydriver == user_name:
                    passenger_info = order.mypassenger[0:5]
                    driver_info = order.mydriver[0:5]
                    money = order.money
                    poi = Poi.objects.filter(id=order.departure).first()
                    start_location = poi.name
                    start_time = order.start_time
                    end_time = order.end_time
                    end_location = order.dest_name
                    status = order.status
                    if status == 2:
                        status = 0
                    elif driver.status == 5:
                        status = 2
                    else:
                        status = 1
                    orders.append({'driver_info': driver_info, 'passenger_info': passenger_info, 'start_time': start_time, 'end_time': end_time,
                                  'money': money, 'start_location': start_location, 'end_location': end_location, 'status': status})
        return JsonResponse({'orders': orders})


def passenger_pay(request):
    if (request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            order_id = reqjson['order']
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        sessionId = SessionId.objects.filter(sessId=sess).first()
        if not sessionId or sessionId.job != 'passenger':
            return JsonResponse({'errcode': -1})
        order = Order.objects.filter(id=order_id).first()
        passenger_id = order.mypassenger
        driver_id = order.mydriver
        passenger = Passenger.objects.filter(name=passenger_id).first()
        driver = Driver.objects.filter(name=driver_id).first()
        if not passenger or not driver:
            return JsonResponse({'errcode': -1})
        passenger.status = 0
        driver.status = 0
        passenger.myorder_id = -1
        driver.myorder_id = -1
        order.end_time = time.time()
        order.status = 2
        passenger.save()
        driver.save()
        order.save()
        return JsonResponse({'errcode': 0})


def driver_order(request):
    if (request.method == 'POST'):  # POST方法，对应的是司机准备接单的环节
        try:
            reqjson = json.loads(request.body)
            sessionId = reqjson['sess']
            origin = reqjson['origin']
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first()  # 找到对应user
        errcode = -1
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode})
        driver = Driver.objects.filter(name=user.username).first()  # 找到对应的司机
        if driver.status == 0:  # 0代表没有订单
            errcode = 0
            driver.status = 1
            driver_unmatched.append(driver.name)
            driver.position = int(origin)
        driver.save()
        return JsonResponse({'errcode': errcode})
    if (request.method == 'GET'):
        try:
            sessionId = request.GET['sess']
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first()  # 找到对应user
        orderid = 0
        destination = {}
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode, 'order': orderid, 'dest': destination})
        driver = Driver.objects.filter(name=user.username).first()  # 找到对应的司机
        if driver.status == 1:  # 司机闲着就给他匹配
            match(sessionId, "driver")
        if driver.status != 0 and driver.status != 1:  # 状态不是0或者1表明有订单，要么是unactive要么是在待匹配池子里
            errcode = 0
            orderid = driver.myorder_id
            order = Order.objects.filter(id=orderid).first()
            destination = {'name': order.dest_name,
                           'latitude': order.dest_lat, 'longitude': order.dest_lon}
        errcode = driver.status
        return JsonResponse({'errcode': errcode, 'order': orderid, 'dest': destination})


def driver_get_order(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -10, 'info': "", 'path': [], 'time': 0})
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1, 'info': "", 'path': [], 'time': 0})
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1, 'info': "", 'path': [], 'time': 0})
            passenger = Passenger.objects.filter(name=order.mypassenger).first()
            info = passenger.name[0:5]
            poi = Poi.objects.filter(id=order.departure).first()
            path, distance = get_path(poi, order)
            speed = poi.speed
            esti_time = distance / speed
            passenger.status = 3
            driver.status = 3
            passenger.save()
            driver.save()
            return JsonResponse({'errcode': 0, 'info': info, 'path': path, 'time': esti_time})
        except Exception as e:
            logger.error(e, exc_info = True)
            return HttpResponse("error:{}".format(e), status=405)


def driver_confirm_aboard(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -1})
                # sessionid需存在 & 是司机
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1})
                # 对应driver存在
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1})
                # order存在
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
                # order存储passenger存在
            driver.status = 4
            passenger.status = 4
            driver.save()
            passenger.save()
            return JsonResponse({'errcode': 0})
        except exception as e:
            logger.error(e, exc_info = True)
            return JsonResponse({'errcode': -1})


def driver_confirm_arrive(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -1})
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1})
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1})
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
            driver.status = 5
            passenger.status = 5
            driver.save()
            passenger.save()
            if driver.name in driver_matched:
                driver_matched.remove(driver.name)
            if passenger.name in passenger_matched:
                passenger_matched.remove(passenger.name)
            return JsonResponse({'errcode': 0})
        except exception as e:
            logger.error(e, exc_info = True)
            return JsonResponse({'errcode': -1})


def passenger_cancel(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'passenger':
                return JsonResponse({'errcode': -1})
                # sessionid存在且为乘客
            cancel_order(user.username, "passenger")
            return JsonResponse({'errcode': 0})
        except exception as e:
            logger.error(e, exc_info = True)
            return JsonResponse({'errcode': -1})


def driver_cancel(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -1})
            cancel_order(user.username, "driver")
            return JsonResponse({'errcode': 0})
        except Exception as e:
            logger.error(e, exc_info = True)
            return JsonResponse({'errcode': -1})
