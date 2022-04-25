from jsonpath_ng import jsonpath, parse
import json
from logging import exception
import time
from django.forms.models import model_to_dict
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from GGG_backend.models import Driver, Passenger, SessionId, Order, Product, Setting
import secoder.settings
import random
import string
import hashlib
import logging
logger = logging.getLogger('django')
mlogger =logging.getLogger('matchlist')
formatter = logging.Formatter('%(name)s - %(lineno)d - %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
console1 = logging.FileHandler("demo.log")
console1.setFormatter(formatter)
mlogger.addHandler(console1)
mlogger.setLevel(level = logging.DEBUG)


match_list = {}
""" 
{id : { passenger_unmatched : [],  # 待匹配乘客池子 
        driver_unmatched : [],  # 待匹配司机池子
        passenger_matched : [],  # 已匹配乘客池子
        driver_matched : [] # 已匹配司机池子
      }
}
# openid
"""
driver_position = {
}  # 键是order的id，值是司机的实时位置(position是一个字典，{'latitude': xxx, 'longitude':xxx})

   

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
            tmp = SessionId.objects.filter(username=openID).update(sessId=sessionID, job=job)
            if tmp == 0:
                SessionId.objects.create(username=openID, sessId=sessionID, job=job)
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
                product_str = Setting.objects.filter(id=1).first().products
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


# 乘客/司机发单时调用
# 传入 独乘产品id, openid, job
# (若match_list无该独乘产品池子则创建之,并)加入待匹配池子
def init_match_list(product, name, job):
    if not product in match_list:
        match_list[product] = {'passenger_unmatched': [], 'driver_unmatched': [],
                               'passenger_matched': [], 'driver_matched': []}
    if job == "passenger" and name not in match_list[product]['passenger_unmatched']:
        match_list[product]['passenger_unmatched'].append(name)
    elif job == "driver" and name not in match_list[product]['driver_unmatched']:
        match_list[product]['driver_unmatched'].append(name)

# 司乘匹配 传入 独乘产品id openid和job 返回0:匹配成功 -1:需要等待 -2:参数错误
# 修改order.status mydriver


def match(product, openid, job):
    try:
        driver_unmatched = match_list[product]['driver_unmatched']
        driver_matched = match_list[product]['driver_matched']
        passenger_unmatched = match_list[product]['passenger_unmatched']
        passenger_matched = match_list[product]['passenger_matched']
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
                user.save()
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
        logger.error(e, exc_info=True)
        return -2

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


def cancel_order(product, openid, job):
    cancel_user, influenced_user, order = None, None, None
    logger.info(openid+' '+job)
    driver_unmatched = match_list[product]['driver_unmatched']
    driver_matched = match_list[product]['driver_matched']
    passenger_unmatched = match_list[product]['passenger_unmatched']
    passenger_matched = match_list[product]['passenger_matched']
    if job == "passenger":
        cancel_user = Passenger.objects.filter(name=openid).first()
        if cancel_user.name in passenger_unmatched:
            passenger_unmatched.remove(cancel_user.name)
        if cancel_user.myorder_id != -1:
            order_id = cancel_user.myorder_id
        cancel_user.myorder_id = -1
        if cancel_user.status < 2:  # 匹配前取消
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
        order.delete()
        cancel_user.myorder_id = -1
    elif job == "driver":
        cancel_user = Driver.objects.filter(name=openid).first()
        if cancel_user.name in driver_unmatched:
            driver_unmatched.remove(cancel_user.name)
        if cancel_user.myorder_id != -1:
            order_id = cancel_user.myorder_id
        cancel_user.myorder_id = -1
        if cancel_user.status < 2:  # 匹配前取消
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
        order.mydriver = ""
        order.save()
    cancel_user.status = 0
    cancel_user.save()
    influenced_user.status = 1
    influenced_user.save()
            

# 访问高德地图接口
# 参数：product, order 返回(path, distance)元组


def get_path(order):
    response = requests.get('https://restapi.amap.com/v5/direction/driving?key='+secoder.settings.GOD_KEY +
                            '&origin='+str(order.origin_lon)+','+str(order.origin_lat)+'&destination='+str(order.dest_lon)+','+str(order.dest_lat)+'&show_fields=polyline')
    response = response.json()
    if(response['infocode']!='10000'):
        path = [{order.origin_lon,order.origin_lat},{order.dest_lon,order.dest_lat}]
        distance = 9990000
        return (path,distance)
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
        reqjson = json.loads(request.body)
        sess = reqjson['sess']
        origin = reqjson['origin']
        dest = reqjson['dest']  # name latitude longitude
        product = reqjson['product']
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
        passenger.lat = origin['latitude']
        passenger.lon = origin['longitude']
        passenger.product = product
        order = Order.objects.create(mypassenger=passengername, origin_name=origin['name'], origin_lat=origin['latitude'], origin_lon=origin['longitude'], dest_name=dest['name'],
                                     dest_lat=dest['latitude'], dest_lon=dest['longitude'], start_time=time.time(), product=product)  # 创建订单
        passenger.myorder_id = order.id
        order_id = order.id
        passenger.save()
        init_match_list(int(product), passengername, 'passenger')
        match(int(product), passengername, 'passenger')
        return JsonResponse({'errcode': errcode, 'order': order_id})

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
            cancel_order(product, driver.name, 'driver')
        passenger = Passenger.objects.filter(name=passengername).first()
        errcode = passenger.status
        drivername = order.mydriver
        driver = Driver.objects.filter(name=drivername).first()
        if not driver or driver.status <= 2 or passenger.status <= 2:
            return JsonResponse({'errcode': errcode})
        if driver_position[order_id]['latitude'] and driver_position[order_id]['longitude']:
            return JsonResponse({'errcode': errcode, 'driver': {'latitude': driver_position[order_id]['latitude'], 'longitude': driver_position[order_id]['longitude']}})
        else:
            return JsonResponse({'errcode':errcode,'latitude':114,'longitude':36})


def get_order_info(request):  # 乘客获取当前订单信息

    sess = request.GET['sess']
    order_id = request.GET['order']
    sessionId = SessionId.objects.filter(sessId=sess).first()
    errcode = -1
    order = Order.objects.filter(id=order_id).first()
    passenger = Passenger.objects.filter(name=order.mypassenger).first()
    if not order or not passenger or  not(sessionId.username==order.mypassenger or sessionId.username==order.mydriver):
        return JsonResponse({'errcode': errcode})
    errcode = passenger.status
    mlogger.info(order)
    drivername = order.mydriver
    driver_info = drivername[0:5]  # 司机前五位
    passenger_info = order.mypassenger[0:5]  # 乘客前五位
    product = Product.objects.filter(id=order.product).first()
    god_ans = get_path(order)
    distance = god_ans[1]
    path = god_ans[0]
    money = distance * product.price_per_meter
    order.money = money
    order.save()
    origin = {'name': order.origin_name,
              'latitude': order.origin_lat, 'longitude': order.origin_lon}
    dest = {'name': order.dest_name,
            'latitude': order.dest_lat, 'longitude': order.dest_lon}
    return JsonResponse({'errcode': errcode, 'driver_info': driver_info, 'passenger_info': passenger_info, 'path': path, 'money': money, 'origin': origin, 'dest': dest})


def get_order_money(request):  # 乘客获取当前订单钱数

    sess = request.GET['sess']
    order_id = request.GET['order']
    sessionId = SessionId.objects.filter(sessId=sess).first()
    
    order = Order.objects.filter(id=order_id).first()
    if not order or not(sessionId.username==order.mypassenger or sessionId.username==order.mydriver):
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
                    passenger_info = order.mypassenger[0:5]
                    driver_info = order.mydriver[0:5]
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
                    orders_info.append({'driver_info': driver_info, 'passenger_info': passenger_info, 'start_time': start_time, 'end_time': end_time,
                                        'money': money, 'start_location': start_location, 'end_location': end_location, 'status': status})

        elif user_job == 'driver':
            driver = Driver.objects.filter(name=user_name).first()
            orders = Order.objects.filter(mydriver=user_name)
            for order in orders:
                if order.mydriver == user_name:
                    passenger_info = order.mypassenger[0:5]
                    driver_info = order.mydriver[0:5]
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
                    orders_info.append({'driver_info': driver_info, 'passenger_info': passenger_info, 'start_time': start_time, 'end_time': end_time,
                                        'money': money, 'start_location': start_location, 'end_location': end_location, 'status': status})
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
        user = SessionId.objects.filter(sessId=sessionId).first()  # 找到对应user
        errcode = -1
        if not user or user.job == 'passenger':  # 不能为空，不能为乘客
            errcode = -10
            return JsonResponse({'errcode': errcode})
        driver = Driver.objects.filter(name=user.username).first()  # 找到对应的司机
        if driver.status == 0:  # 0代表没有订单
            errcode = 0
            driver.status = 1
            driver.lat = origin['latitude']
            driver.lon = origin['longitude']
            driver.save()
            init_match_list(driver.product, driver.name, "driver")
            match(driver.product, driver.name, "driver")  # 为司机进行匹配
        return JsonResponse({'errcode': errcode})
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
        if driver.status != 0 and driver.status != 1:  # 状态不是0或者1表明有订单，要么是unactive要么是在待匹配池子里
            errcode = 0
            orderid = driver.myorder_id
            order = Order.objects.filter(id=orderid).first()
            if driver.status >= 3:
                driver_position[orderid] = {
                    'latitude': latitude, 'longitude': longitude}
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
                return JsonResponse({'errcode': -10, 'info': ""})
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1, 'info': ""})
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1, 'info': ""})
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            info = passenger.name[0:5]
            passenger.status = 3
            driver.status = 3
            passenger.save()
            driver.save()
            position = reqjson['position']
            driver_position[orderid] = position
            return JsonResponse({'errcode': 0, 'info': info})
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
                return JsonResponse({'errcode': -1, 'path': [], 'time': 0})
                # sessionid需存在 & 是司机
            driver = Driver.objects.filter(name=user.username).first()
            if not driver or driver.myorder_id == -1:
                return JsonResponse({'errcode': -1, 'path': [], 'time': 0})
                # 对应driver存在
            orderid = reqjson['order']
            order = Order.objects.filter(id=orderid).first()
            if not order:
                return JsonResponse({'errcode': -1, 'path': [], 'time': 0})
                # order存在
            passenger = Passenger.objects.filter(
                name=order.mypassenger).first()
            if not passenger:
                return JsonResponse({'errcode': -1, 'path': [], 'time': 0})
                # order存储passenger存在
            driver.status = 4
            passenger.status = 4
            driver.save()
            passenger.save()
            product = Product.objects.filter(id=passenger.product).first()
            path, distance = get_path(order)
            speed = product.speed
            esti_time = distance / speed
            return JsonResponse({'errcode': 0, 'path': path, 'time': esti_time})
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1, 'path': [], 'time': 0})


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
            driver_matched = match_list[passenger.product]['driver_matched']
            passenger_matched = match_list[passenger.product]['passenger_matched']
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
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'passenger':
                return JsonResponse({'errcode': -1})
                # sessionid存在且为乘客
            passenger = Passenger.objects.filter(name=user.username).first()
            if not passenger:
                return JsonResponse({'errcode': -1})
            if passenger.myorder_id != -1:
                cancel_order(passenger.product, user.username, "passenger")
            else:
                passenger.status = 0
                passenger.save()    
            return JsonResponse({'errcode': 0})
        except exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse({'errcode': -1})


def driver_cancel(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
            user = SessionId.objects.filter(sessId=sess).first()
            if not user or user.job != 'driver':
                return JsonResponse({'errcode': -1})
            driver = Driver.objects.filter(name=user.username).first()
            if not driver:
                return JsonResponse({'errcode': -1})
            if driver.myorder_id != -1:
                cancel_order(driver.product, user.username, "driver")
            else:
                driver.status = 0
                driver.save()    
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
