from jsonpath_ng import jsonpath, parse
import json
# from logging import exception
import time
import math
from django.forms.models import model_to_dict
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from GGG_backend.models import Driver, Passenger, SessionId, Order, Product, Setting, Area
import secoder.settings
import random
import string
import hashlib
import logging
logger = logging.getLogger('django')
mlogger = logging.getLogger('matchlist')
formatter = logging.Formatter('%(name)s - %(lineno)d - %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
console1 = logging.FileHandler("demo.log")
console1.setFormatter(formatter)
mlogger.addHandler(console1)
mlogger.setLevel(level=logging.DEBUG)


match_list = {}
""" 
{
 area:{
        product : { passenger_unmatched : [],  # 待匹配乘客池子 
                    driver_unmatched : [],  # 待匹配司机池子
                    passenger_matched : [],  # 已匹配乘客池子
                    driver_matched : [] # 已匹配司机池子
                }
      }          
}
# openid
"""
driver_position = {
}  # 键是order的id，值是司机的实时位置(position是一个字典，{'latitude': xxx, 'longitude':xxx})


def start_pressure_test(request):
    if request.method == 'POST':
        reqjson = json.loads(request.body)
        num = reqjson['num']
        i = 0
        passenger_list = []
        driver_list = []
        session_list = []
        while i < num:
            str1 = 'p'+str(i)
            str2 = 'd'+str(i)
            passenger_list.append(Passenger(name=str1))
            driver_list.append(Driver(name=str2, product=1))
            session_list.append(
                SessionId(sessId=str1, username=str1, job="passenger"))
            session_list.append(
                SessionId(sessId=str2, username=str2, job="driver"))
            i = i + 1
        Passenger.objects.bulk_create(passenger_list)
        Driver.objects.bulk_create(driver_list)
        SessionId.objects.bulk_create(session_list)

        return JsonResponse({'errcode': 0})


def end_pressure_test(request):
    if request.method == 'POST':
        Product.objects.filter(name='1').delete()
        Area.objects.filter(name='1').delete()
        Passenger.objects.all().delete()
        Driver.objects.all().delete()
        Order.objects.all().delete()
        SessionId.objects.all().delete()
    return JsonResponse({'errcode': 0})


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


def show_car(request):
    if(request.method == 'GET'):
        try:
            sess = request.GET['sess']
            longitude = request.GET['longitude']
            latitude = request.GET['latitude']
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1, 'cars': []})
        available_drivers = []
        range = Setting.objects.all().first().range
        for driver_name, position in driver_position.items():
            if Driver.objects.filter(name=driver_name, status=1).exists():
                driver_lat = float(position['latitude'])
                driver_lon = float(position['longitude'])
                if (((111 * (float(latitude) - driver_lat)) ** 2 + (111 * math.cos(float(latitude) / (180 * 3.14159)) * (float(longitude) - driver_lon)) ** 2) < range):
                    available_drivers.append(
                        {'latitude': driver_lat, 'longitude': driver_lon})
        return JsonResponse({'errcode': 0, 'cars': available_drivers})


def login(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            code = reqjson['code']
            job = reqjson['job']
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': 403, 'sess': ""})
        data = get_wx_response(code)
        try:
            openID = data['openid']
            sessionID = get_3rd_session(data['session_key'], openID, job)
            try:
                errorcode = data['errcode']
            except Exception:
                errorcode = 0
            if errorcode != 0:
                return JsonResponse({'errcode': errorcode, 'sess': ""})
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
                return JsonResponse({'errcode': -10, 'sess': sessionID})
            res = JsonResponse({'errcode': errorcode, 'sess': sessionID})
            return res
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': 405, 'sess': ""})


def reg(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("error:{}".format(e), status=405)
        try:
            user = SessionId.objects.filter(sessId=sess).first()
            if(user.job == "passenger"):
                Passenger.objects.create(name=user.username)
            elif(user.job == "driver"):
                Driver.objects.create(name=user.username)
            return JsonResponse({'errcode': 1})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -2})


def product_list(request):
    if(request.method == 'GET'):
        try:
            sess = request.GET['sess']
            if not SessionId.objects.filter(sessId=sess).first():
                return JsonResponse({'errcode': -2, 'product': []})
            else:
                product_str = Setting.objects.exclude(
                    products='').first().products
                product_list = product_str.split(',')
                array = []
                for i in product_list:
                    product = Product.objects.filter(id=i).first()
                    array.append(
                        {"id": i, "name": product.name, "price": product.price_per_meter * 1000})
                return JsonResponse({'errcode': 0, 'product': array})
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("error:{}".format(e), status=405)


def driver_choose_product(request):
    if(request.method == 'POST'):
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        product = reqjson['product']
        user = SessionId.objects.filter(sessId=sess).first()
        if not user or user.job != 'driver':
            return JsonResponse({'errcode': -1})
        driver = Driver.objects.filter(name=user.username).first()
        if not driver:
            return JsonResponse({'errcode': -1})
        driver.product = product
        driver.save()
        return JsonResponse({'errcode': 0})

# 判断点是否在开城围栏中


def check_area(border, lat, lng):
    lat = float(lat)
    lng = float(lng)
    pointlist = json.loads(border)
    crossing = 0
    for i in range(len(pointlist) - 1):
        # 避免与端点相交两次
        if lat == pointlist[i]['lat'] and pointlist[i]['lat'] > pointlist[i + 1]['lat']:
            continue
        if lat == pointlist[i + 1]['lat'] and pointlist[i]['lat'] < pointlist[i + 1]['lat']:
            continue
        # 开区域
        if pointlist[i]['lat'] - pointlist[i + 1]['lat'] == 0:
            continue
        if pointlist[i]['lat'] - pointlist[i + 1]['lat'] != 0:
            slope = (pointlist[i]['lng'] - pointlist[i + 1]['lng']) / \
                (pointlist[i]['lat'] - pointlist[i + 1]['lat'])
            betw1 = (pointlist[i]['lat'] <= lat) and (
                lat < pointlist[i + 1]['lat'])
            betw2 = (pointlist[i + 1]['lat'] <=
                     lat) and (lat < pointlist[i]['lat'])
            above = (lng < slope *
                     (lat - pointlist[i]['lat']) + pointlist[i]['lng'])
            if (betw1 or betw2) and above:
                crossing += 1
    return (crossing % 2 != 0)

# 乘客/司机发单时调用
# 传入 独乘产品id, openid, job
# (若match_list无该独乘产品池子则创建之,并)加入待匹配池子


def init_match_list(area, product, name, job):
    mlogger.info("init_match_list %s %s %s %s %s ",
                 area, product, name, job, match_list)
    if not area in match_list:
        match_list[area] = {}
    if not product in match_list[area]:
        match_list[area][product] = {'passenger_unmatched': [], 'driver_unmatched': [],
                                     'passenger_matched': [], 'driver_matched': []}
    if job == "passenger" and name not in match_list[area][product]['passenger_unmatched']:
        match_list[area][product]['passenger_unmatched'].append(name)
    elif job == "driver" and name not in match_list[area][product]['driver_unmatched']:
        match_list[area][product]['driver_unmatched'].append(name)

# 司乘匹配 传入开城围栏id 独乘产品id openid和job 返回0:匹配成功 -1:错误
# 修改order.status mydriver


def match(area, product, openid, job):
    mlogger.info("match %s %s %s %s %s ", area,
                 product, openid, job, match_list)
    try:
        driver_unmatched = match_list[area][product]['driver_unmatched']
        driver_matched = match_list[area][product]['driver_matched']
        passenger_unmatched = match_list[area][product]['passenger_unmatched']
        passenger_matched = match_list[area][product]['passenger_matched']
        if job == "passenger":
            if len(driver_unmatched) > 0:
                driver_name = driver_unmatched.pop(0)
                passenger_name = passenger_unmatched.pop(0)
                user = Passenger.objects.filter(name=openid).first()
                order = Order.objects.filter(id=user.myorder_id).first()
                if not order:
                    return -1
                order.mydriver = driver_name
                order.match_time = time.time()
                order.status = 1
                driver = Driver.objects.filter(name=driver_name).first()
                driver.myorder_id = order.id
                driver_matched.append(driver_name)
                passenger_matched.append(passenger_name)
                driver.status = 2
                user.status = 2
                user.save()
                driver.save()
                order.save()
                return 0
            else:
                return -1
        elif job == "driver":
            if len(passenger_unmatched) > 0:
                driver_name = driver_unmatched.pop(0)
                passenger_name = passenger_unmatched.pop(0)
                user = Driver.objects.filter(name=openid).first()
                passenger = Passenger.objects.filter(
                    name=passenger_name).first()
                order_id = passenger.myorder_id
                order = Order.objects.filter(id=order_id).first()
                order.mydriver = user.name
                order.match_time = time.time()
                user.myorder_id = order.id
                order.status = 1
                user.status = 2
                passenger.status = 2
                driver_matched.append(driver_name)
                passenger_matched.append(passenger_name)
                user.save()
                passenger.save()
                order.save()
                return 0
            else:
                return -1
        else:
            return -1
    except Exception as e:
        logger.info(openid)
        logger.error(e, exc_info=True)
        return -1

# 检查id对应订单是否超时
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


def cancel_order(area, product, openid, job):
    cancel_user, influenced_user, order = None, None, None
    logger.info(openid+' '+job)
    driver_unmatched = match_list[area][product]['driver_unmatched']
    driver_matched = match_list[area][product]['driver_matched']
    passenger_unmatched = match_list[area][product]['passenger_unmatched']
    passenger_matched = match_list[area][product]['passenger_matched']
    if job == "passenger":
        cancel_user = Passenger.objects.filter(name=openid).first()
        if cancel_user.name in passenger_unmatched:
            passenger_unmatched.remove(cancel_user.name)
        order_id = cancel_user.myorder_id
        order = Order.objects.filter(id=order_id).first()
        cancel_user.myorder_id = -1
        if cancel_user.status < 2:  # 匹配前取消
            cancel_user.status = 0
            cancel_user.save()
            if order:
                order.delete()
            return
        influenced_user = Driver.objects.filter(name=order.mydriver).first()
        influenced_user.status = 1
        influenced_user.myorder_id = -1
        influenced_user.save()
        if influenced_user.name in driver_matched:
            driver_matched.remove(influenced_user.name)
            driver_unmatched.insert(0, influenced_user.name)
            match(int(area), int(product), influenced_user.name, "driver")
        if cancel_user.name in passenger_matched:
            passenger_matched.remove(cancel_user.name)
        if order:
            order.delete()
    elif job == "driver":
        cancel_user = Driver.objects.filter(name=openid).first()
        if cancel_user.name in driver_unmatched:
            driver_unmatched.remove(cancel_user.name)
        order_id = cancel_user.myorder_id
        order = Order.objects.filter(id=order_id).first()
        cancel_user.myorder_id = -1
        if cancel_user.status < 2:  # 匹配前取消
            cancel_user.status = 0
            cancel_user.save()
            return
        if cancel_user.name in driver_matched:
            driver_matched.remove(cancel_user.name)
        order.status = 0
        order.mydriver = ""
        order.save()
        influenced_user = Passenger.objects.filter(
            name=order.mypassenger).first()
        influenced_user.status = 1
        influenced_user.save()
        if influenced_user.name in passenger_matched:
            passenger_matched.remove(influenced_user.name)
            passenger_unmatched.insert(0, influenced_user.name)
            match(int(area), int(product), influenced_user.name, "passenger")
    cancel_user.status = 0
    cancel_user.save()


# 访问高德地图接口

# 获取接乘客行程路径 返回path
def get_passenger_path(order):
    passenger = Passenger.objects.filter(name=order.mypassenger).first()
    response = requests.get('https://restapi.amap.com/v5/direction/driving?key='+secoder.settings.GOD_KEY +
                            '&origin='+str(driver_position[order.mydriver]['longitude'])+','+str(driver_position[order.mydriver]['latitude'])+'&destination='+str(passenger.lon)+','+str(passenger.lat)+'&show_fields=polyline')
    response = response.json()
    if(response['infocode'] != '10000'):
        path = [{"longitude": float(driver_position[order.mydriver].longitude), "latitude": float(driver_position[order.mydriver].latitude)},
                {"longitude": float(passenger.lon), "latitude": float(passenger.lat)}]
        return path
    polylines = [match.value for match in parse(
        '$.route.paths[0].steps[*].polyline').find(response)]
    strs = []  # ['lon,lat;lon,lat']
    for polyline in polylines:
        strs.extend(polyline.split(';'))
    path = []
    for str1 in strs:
        temp = str1.split(',')
        # [{lon,lat}]
        path.append({"longitude": float(temp[0]), "latitude": float(temp[1])})
    return path

# 获取订单行程路径&长度
# 参数: order 返回(path, distance)元组


def get_order_path(order):
    response = requests.get('https://restapi.amap.com/v5/direction/driving?key='+secoder.settings.GOD_KEY +
                            '&origin='+str(order.origin_lon)+','+str(order.origin_lat)+'&destination='+str(order.dest_lon)+','+str(order.dest_lat)+'&show_fields=polyline')
    response = response.json()
    if(response['infocode'] != '10000'):
        path = [{"longitude": float(order.origin_lon), "latitude": float(order.origin_lat)},
                {"longitude": float(order.dest_lon), "latitude": float(order.dest_lat)}]
        distance = 9990000
        return (path, distance)
    distance = float([match.value for match in parse(
        '$.route.paths[0].distance').find(response)][0])
    polylines = [match.value for match in parse(
        '$.route.paths[0].steps[*].polyline').find(response)]
    strs = []  # ['lon,lat;lon,lat']
    for polyline in polylines:
        strs.extend(polyline.split(';'))
    path = []
    for str1 in strs:
        temp = str1.split(',')
        # [{lon,lat}]
        path.append({"longitude": float(temp[0]), "latitude": float(temp[1])})
    return (path, distance)


def passenger_order(request):
    if (request.method == 'POST'):  # 乘客发起订单
        # logger.info(request.body)
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        origin = reqjson['origin']
        dest = reqjson['dest']  # name latitude longitude
        product_id = reqjson['product']
        areas = Area.objects.all().values()
        area_id = [-1, -1]
        area_name = ["", ""]
        sessionId = SessionId.objects.filter(
            sessId=sess).only("username").first()
        passengername = sessionId.username
        flag1, flag2 = True, True
        for area in areas:
            if(flag1 and check_area(area['border'], origin['latitude'], origin['longitude'])):
                area_id[0] = area['id']
                area_name[0] = area['name']
                flag1 = False
            if(flag2 and check_area(area['border'], dest['latitude'], dest['longitude'])):
                area_id[1] = area['id']
                area_name[1] = area['name']
                flag2 = False
            if(not (flag1 or flag2)):
                break
        if(flag1 or flag2):
            return JsonResponse({'errcode': 0, 'area': area_id, 'info': area_name})
        order = Order.objects.create(mypassenger=passengername, origin_name=origin['name'], origin_lat=origin['latitude'], origin_lon=origin['longitude'], dest_name=dest['name'],
                                     dest_lat=dest['latitude'], dest_lon=dest['longitude'], start_time=time.time(), product=product_id, area=area_id[0])  # 创建订单
        product = Product.objects.filter(id=product_id).first()
        order_path, distance = get_order_path(order)
        order.money = distance * product.price_per_meter + 5  # 起步价
        order.order_path = json.dumps(order_path)
        order.distance = distance
        order.save()
        if(Passenger.objects.filter(name=passengername).update(myorder_id=order.id, product=product_id, lon=origin['longitude'], lat=origin['latitude'], status=1) == 0):
            return JsonResponse({'errcode': -1})
        init_match_list(int(area_id[0]), int(
            product_id), passengername, 'passenger')
        match(int(area_id[0]), int(product_id), passengername, 'passenger')
        return JsonResponse({'errcode': 0, 'order': order.id, 'area': area_id, 'info': area_name})

    elif(request.method == 'GET'):  # 乘客询问订单状态
        sess = request.GET['sess']
        order_id = int(request.GET['order'])
        sessionId = SessionId.objects.filter(sessId=sess).first()
        passengername = sessionId.username
        passenger = Passenger.objects.filter(name=passengername).first()
        order = Order.objects.filter(id=order_id).first()
        product = order.product
        errcode = -10
        if not passenger:
            return JsonResponse({'errcode': errcode})
        if passenger.status == 0:
            errcode = 0
            return JsonResponse({'errcode': errcode})
        if check_time(order.id) == False and passenger.status == 2:  # 已匹配司机超时
            order = Order.objects.filter(id=passenger.myorder_id).first()
            driver = Driver.objects.filter(myorder_id=order.id).first()
            cancel_order(int(order.area), int(product), driver.name, 'driver')
        passenger = Passenger.objects.filter(name=passengername).first()
        errcode = passenger.status
        drivername = order.mydriver
        driver = Driver.objects.filter(name=drivername).first()
        if (not driver) or driver.status <= 2 or passenger.status <= 2:
            return JsonResponse({'errcode': errcode})
        elif order.mydriver in driver_position and driver_position[order.mydriver]['latitude'] and driver_position[order.mydriver]['longitude']:
            return JsonResponse({'errcode': errcode, 'driver': {'latitude': driver_position[order.mydriver]['latitude'], 'longitude': driver_position[order.mydriver]['longitude']}})
        else:
            return JsonResponse({'errcode': errcode})  # ????


def get_order_info(request):  # 乘客获取当前订单信息

    sess = request.GET['sess']
    order_id = request.GET['order']
    sessionId = SessionId.objects.filter(sessId=sess).first()
    errcode = -1
    order = Order.objects.filter(id=order_id).first()
    passenger = Passenger.objects.filter(name=order.mypassenger).first()
    if not order or not passenger or not(sessionId.username == order.mypassenger or sessionId.username == order.mydriver):
        return JsonResponse({'errcode': errcode})
    errcode = passenger.status
    mlogger.info(order)
    drivername = order.mydriver
    driver_info = drivername[-5:]  # 司机前五位
    passenger_info = order.mypassenger[-5:]  # 乘客前五位
    order_path = json.loads(order.order_path)
    passenger_path = json.loads(order.passenger_path)
    money = order.money
    origin = {'name': order.origin_name,
              'latitude': order.origin_lat, 'longitude': order.origin_lon}
    dest = {'name': order.dest_name,
            'latitude': order.dest_lat, 'longitude': order.dest_lon}
    return JsonResponse({'errcode': errcode, 'driver_info': driver_info, 'passenger_info': passenger_info, 'order_path': order_path, 'passenger_path': passenger_path, 'money': money, 'origin': origin, 'dest': dest})


def get_order_money(request):  # 乘客获取当前订单钱数

    sess = request.GET['sess']
    order_id = request.GET['order']
    sessionId = SessionId.objects.filter(sessId=sess).first()

    order = Order.objects.filter(id=order_id).first()
    if not order or not(sessionId.username == order.mypassenger or sessionId.username == order.mydriver):
        return JsonResponse({'errcode': -1})
    return JsonResponse({'errcode': 0, 'money': order.money})


def get_history_order_info(request):  # 司乘获取历史订单
    if (request.method == 'GET'):
        sess = request.GET['sess']
        sessionId = SessionId.objects.filter(sessId=sess).first()
        user_job = sessionId.job
        user_name = sessionId.username
        orders_info = []
        if user_job == 'passenger':
            passenger = Passenger.objects.filter(name=user_name).first()
            orders = Order.objects.filter(mypassenger=user_name)
            for order in orders:
                if order.mypassenger == user_name:
                    passenger_info = order.mypassenger[-5:]
                    driver_info = order.mydriver[-5:]
                    money = order.money
                    start_location = order.origin_name
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
                    order_path = json.loads(order.order_path)
                    passenger_path = json.loads(order.passenger_path)
                    orders_info.append({'driver_info': driver_info, 'passenger_info': passenger_info, 'start_time': start_time, 'end_time': end_time,
                                        'money': money, 'start_location': start_location, 'end_location': end_location, 'status': status, 'order_path': order_path, 'passenger_path': passenger_path})

        elif user_job == 'driver':
            driver = Driver.objects.filter(name=user_name).first()
            orders = Order.objects.filter(mydriver=user_name)
            for order in orders:
                if order.mydriver == user_name:
                    passenger_info = order.mypassenger[-5:]
                    driver_info = order.mydriver[-5:]
                    money = order.money
                    start_location = order.origin_name
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
                    order_path = json.loads(order.order_path)
                    passenger_path = json.loads(order.passenger_path)
                    orders_info.append({'driver_info': driver_info, 'passenger_info': passenger_info, 'start_time': start_time, 'end_time': end_time,
                                        'money': money, 'start_location': start_location, 'end_location': end_location, 'status': status, 'order_path': order_path, 'passenger_path': passenger_path})
        return JsonResponse({'orders': orders_info})


def passenger_pay(request):
    if (request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            order_id = reqjson['order']
        except Exception as e:
            logger.error(e, exc_info=True)
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
            return HttpResponse("error:{}".format(e), status=405)
        origin_latitude = origin['latitude']
        origin_longitude = origin['longitude']
        areas = Area.objects.all().values()
        area_id = -1
        area_name = ""
        errcode = -1
        user = SessionId.objects.filter(sessId=sessionId).first()  # 找到对应user
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode, 'area': area_id, 'info': area_name})
        driver = Driver.objects.filter(name=user.username).first()  # 找到对应的司机
        if driver.status == 0:  # 0代表没有订单
            errcode = 0
            for area in areas:
                if (check_area(area['border'], origin_latitude, origin_longitude)):
                    area_id = area['id']
                    area_name = area['name']
                    break
            if (area_id == -1):
                return JsonResponse({'errcode': errcode, 'area': area_id, 'info': area_name})
            driver.status = 1
            driver.save()
            init_match_list(int(area_id), int(
                driver.product), driver.name, "driver")
            match(int(area_id), int(driver.product),
                  driver.name, "driver")  # 为司机进行匹配
        return JsonResponse({'errcode': errcode, 'area': area_id, 'info': area_name})
    if (request.method == 'GET'):
        try:
            sessionId = request.GET['sess']
            latitude = request.GET['latitude']
            longitude = request.GET['longitude']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        user = SessionId.objects.filter(sessId=sessionId).first()  # 找到对应user
        orderid = 0
        destination = {}
        origin = {}
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode, 'order': orderid, 'dest': destination})
        driver = Driver.objects.filter(name=user.username).first()  # 找到对应的司机
        driver_position[driver.name] = {
            'latitude': latitude, 'longitude': longitude}
        if driver.status != 0 and driver.status != 1:  # 状态不是0或者1表明有订单，要么是unactive要么是在待匹配池子里
            errcode = 0
            orderid = driver.myorder_id
            order = Order.objects.filter(id=orderid).first()
            origin = {'name': order.origin_name,
                      'latitude': order.origin_lat, 'longitude': order.origin_lon}
            destination = {'name': order.dest_name,
                           'latitude': order.dest_lat, 'longitude': order.dest_lon}
        errcode = driver.status
        return JsonResponse({'errcode': errcode, 'order': orderid, 'passenger_loc': origin, 'dest': destination})


def driver_get_order(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -10, 'info': "", 'passenger_path': []})
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1, 'info': "", 'passenger_path': []})
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1, 'info': "", 'passenger_path': []})
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            info = passenger.name[-5:]
            passenger.status = 3
            driver.status = 3
            passenger.save()
            driver.save()
            passenger_path = get_passenger_path(order)
            order.passenger_path = json.dumps(passenger_path)
            order.save()
            position = reqjson['position']
            driver_position[user.username] = position
            return JsonResponse({'errcode': 0, 'info': info, 'passenger_path': passenger_path})
        except Exception as e:
            logger.error(e, exc_info=True)
            return HttpResponse("error:{}".format(e), status=405)


def driver_confirm_aboard(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -1, 'order_path': [], 'time': 0})
                # sessionid需存在 & 是司机
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1, 'order_path': [], 'time': 0})
                # 对应driver存在
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1, 'order_path': [], 'time': 0})
                # order存在
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            if not passenger:
                return JsonResponse({'errcode': -1, 'order_path': [], 'time': 0})
                # order存储passenger存在
            driver.status = 4
            passenger.status = 4
            driver.save()
            passenger.save()
            product = Product.objects.filter(id=passenger.product).first()
            speed = product.speed
            esti_time = order.distance / speed
            order_path = json.loads(order.order_path)
            return JsonResponse({'errcode': 0, 'order_path': order_path, 'time': esti_time})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1, 'order_path': [], 'time': 0})


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
            driver_matched = match_list[order.area][passenger.product]['driver_matched']
            passenger_matched = match_list[order.area][passenger.product]['passenger_matched']
            driver.status = 5
            passenger.status = 5
            driver.save()
            passenger.save()
            if driver.name in driver_matched:
                driver_matched.remove(driver.name)
            if passenger.name in passenger_matched:
                passenger_matched.remove(passenger.name)
            return JsonResponse({'errcode': 0})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1})


def passenger_cancel(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            area = reqjson['area']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'passenger':
                return JsonResponse({'errcode': -1})
                # sessionid存在且为乘客
            passenger = Passenger.objects.filter(name=user.username).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
            if area == -1:
                areas = Area.objects.all().values()
                if passenger.status == 1:
                    for a in areas:
                        if int(a['id']) in match_list and int(passenger.product) in match_list[int(a['id'])] and passenger.name in match_list[int(a['id'])][int(passenger.product)]['passenger_unmatched']:
                            area = a
                            break
                if passenger.status == 2:
                    for a in areas:
                        if int(a['id']) in match_list and int(passenger.product) in match_list[int(a['id'])] and passenger.name in match_list[int(a['id'])][int(passenger.product)]['passenger_matched']:
                            area = a
                            break
            if area == -1:
                passenger.status = 0
                passenger.save()
                return JsonResponse({'errcode': 0})
            cancel_order(int(area), int(passenger.product),
                         user.username, "passenger")
            return JsonResponse({'errcode': 0})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1})


def driver_cancel(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            area = reqjson['area']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -1})
            driver = Driver.objects.filter(name=user.username).first()
            if not driver:
                return JsonResponse({'errcode': -1})
            if area == -1:
                areas = Area.objects.all().values()
                if driver.status == 1:
                    for a in areas:
                        if int(a['id']) in match_list and int(driver.product) in match_list[int(a['id'])] and driver.name in match_list[int(a['id'])][int(driver.product)]['driver_unmatched']:
                            area = a
                            break
                if driver.status == 2 or driver.status == 3:
                    for a in areas:
                        if int(a['id']) in match_list and int(driver.product) in match_list[int(a['id'])] and driver.name in match_list[int(a['id'])][int(driver.product)]['driver_matched']:
                            area = a
                            break
            if area == -1:
                driver.status = 0
                driver.save()
                return JsonResponse({'errcode': 0})
            cancel_order(int(area), int(driver.product),
                         user.username, "driver")
            return JsonResponse({'errcode': 0})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1})


def check_session_id(request):
    if(request.method == 'GET'):
        sess = request.GET['sess']
        user = SessionId.objects.filter(sessId=sess).first()
        job = request.GET['job']
        if not user or user.job != job:
            return JsonResponse({'errcode': -1})
        if job == "passenger":
            passenger = Passenger.objects.filter(name=user.username).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
        elif job == "driver":
            driver = Driver.objects.filter(name=user.username).first()
            if not driver:
                return JsonResponse({'errcode': -1})
        return JsonResponse({'errcode': 0})


def get_former(request):
    if(request.method == 'GET'):
        sess = request.GET['sess']
        user = SessionId.objects.filter(sessId=sess).first()
        job = request.GET['job']
        if not user or user.job != job:
            return JsonResponse({'errcode': -1, 'order': -1})
        order = -1
        default_product = {'id': -1, 'name': "请选择车型", 'price': 0}
        if job == "passenger":
            passenger = Passenger.objects.filter(name=user.username).first()
            if not passenger:
                return JsonResponse({'errcode': -1, 'order': -1})
            order = passenger.myorder_id
            return JsonResponse({'errcode': 0, 'order': order})
        elif job == "driver":
            driver = Driver.objects.filter(name=user.username).first()
            if not driver:
                return JsonResponse({'errcode': -1, 'order': -1, 'product': default_product})
            order = driver.myorder_id
            product = Product.objects.filter(id=driver.product).first()
            if not product:
                return JsonResponse({'errcode': 0, 'order': -1, 'product': default_product})
            product_dict = {'id': driver.product, 'name': product.name,
                            'price': product.price_per_meter * 1000}
            return JsonResponse({'errcode': 0, 'order': order, 'product': product_dict})


def get_user_info(request):
    if request.method == 'GET':
        sess = request.GET['sess']
        user = SessionId.objects.filter(sessId=sess).first()
        if not user:
            return JsonResponse({'errcode': -1})
        if user.job == "passenger":
            passenger = Passenger.objects.filter(name=user.username).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
            try:
                order_id = request.GET['order']
            except Exception:
                return JsonResponse({'errcode': 0, 'name': passenger.realname, 'phone': passenger.phone})
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return JsonResponse({'errcode': -1})
            driver = Driver.objects.filter(name=order.mydriver).first()
            if not driver:
                return JsonResponse({'errcode': -1})
            return JsonResponse({'errcode': 0, 'name': driver.realname, 'phone': driver.phone, 'carinfo': driver.carinfo, 'carcolor': driver.carcolor, 'carnum': driver.carnum, 'score': driver.score, 'product': driver.product})
        if user.job == "driver":
            driver = Driver.objects.filter(name=user.username).first()
            if not driver:
                return JsonResponse({'errcode': -1})
            try:
                order_id = request.GET['order']
            except Exception:
                return JsonResponse({'errcode': 0, 'name': driver.realname, 'phone': driver.phone, 'carinfo': driver.carinfo, 'carcolor': driver.carcolor, 'carnum': driver.carnum, 'score': driver.score, 'product': driver.product})
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return JsonResponse({'errcode': -1})
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
            return JsonResponse({'errcode': 0, 'name': passenger.realname, 'phone': passenger.phone})


def give_score(request):
    if request.method == 'POST':
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        user = SessionId.objects.filter(sessId=sess).first()
        if not user or user.job != 'passenger':
            return JsonResponse({'errcode': -1})
        order_id = reqjson['order']
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return JsonResponse({'errcode': -1})
        driver = Driver.objects.filter(name=order.mydriver).first()
        if not driver:
            return JsonResponse({'errcode': -1})
        score = reqjson['score']
        driver.score = (driver.score * driver.scorenum +
                        score) / (driver.scorenum + 1)
        driver.scorenum += 1
        driver.save()
        return JsonResponse({'errcode': 0})


def set_user_info(request):
    if request.method == 'POST':
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        user = SessionId.objects.filter(sessId=sess).first()
        if not user:
            return JsonResponse({'errcode': -1})
        if user.job == "passenger":
            passenger = Passenger.objects.filter(name=user.username).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
            name = reqjson['name']
            phone = reqjson['phone']
            passenger.realname = name
            passenger.phone = phone
            passenger.save()
            return JsonResponse({'errcode': 0})
        if user.job == "driver":
            driver = Driver.objects.filter(name=user.username).first()
            if not driver:
                return JsonResponse({'errcode': -1})
            name = reqjson['name']
            phone = reqjson['phone']
            carinfo = reqjson['carinfo']
            carcolor = reqjson['carcolor']
            carnum = reqjson['carnum']
            product = reqjson['product']
            driver.realname = name
            driver.phone = phone
            driver.carinfo = carinfo
            driver.carcolor = carcolor
            driver.carnum = carnum
            if Product.objects.filter(id=product).first():
                driver.product = product
                driver.save()
                return JsonResponse({'errcode': 0})
            else:
                logger.info("product:{}".format(product))
                return HttpResponse("product{}不存在".format(product), status=405)
