from distutils.log import error
import decimal
from urllib import response
from django.test import TestCase
from GGG_backend.models import Driver, Order, Passenger, SessionId, Product, Setting
from unittest import mock
from unittest.mock import patch
from GGG_backend.views import get_3rd_session


class GGG_test(TestCase):
    def setUp(self):
        # 以下用于测试注册
        SessionId.objects.create(
            sessId="773", username="nana7mi", job="passenger")
        SessionId.objects.create(sessId="510", username="azi", job="driver")

        # 以下用于测试登录
        Passenger.objects.create(name='Diana')
        Driver.objects.create(name="Bella")

        # 以下用于测试订单流转
        SessionId.objects.create(
            sessId="369", username="arui", job="passenger")
        Passenger.objects.create(name="arui", status=0)
        SessionId.objects.create(sessId="963", username='ashuai', job='driver')
        Driver.objects.create(name="ashuai", status=0, product=1)
        # Order.objects.create(mypassenger="arui", money=100)
        # order = Order.objects.filter(mypassenger='arui').first()
        # setup_order_id = order.id

        # Product
        Product.objects.create(name='senpai', price_per_meter=810, speed=1919)
        Product.objects.create(name='mur', price_per_meter=810, speed=1919)
        Product.objects.create(name='kmr', price_per_meter=810, speed=1919)

        Setting.objects.create(products="1,2,3")

    @patch("GGG_backend.views.get_wx_response")
    def test_login_passenger(self, mock_get_wx_response):
        data = {
            'openid': 'Diana',
            'session_key': 'Jiaranjintianchishenme'
        }
        mock_get_wx_response.return_value = data

        sess_id = get_3rd_session(
            'Jiaranjintianchishenme', 'Diana', 'passenger')
        response = self.client.post(
            "/api/login", data={'code': "ranran", "job": 'passenger'}, content_type="application/json")
        # print(response)
        errcode = response.json()['errcode']
        sess = response.json()['sess']
        self.assertEqual(errcode, 0)
        # self.assertEqual(sess, sess_id)

    @patch("GGG_backend.views.get_wx_response")
    def test_login_driver(self, mock_get_wx_response):
        data = {
            'openid': 'Bella',
            'session_key': 'Yongganniuniubupakunnan'
        }
        mock_get_wx_response.return_value = data

        sess_id = get_3rd_session(
            'Yongganniuniubupakunnan', 'Bella', 'driver')
        response = self.client.post(
            "/api/login", data={'code': "beilala", "job": 'driver'}, content_type="application/json")
        errcode = response.json()['errcode']
        sess = response.json()['sess']
        self.assertEqual(errcode, 0)
        # self.assertEqual(sess, sess_id)

    @patch("GGG_backend.views.get_wx_response")
    def test_login_gg(self, mock_get_wx_response):
        data = {
            'openid': 'Bella',
            'session_key': 'Yongganniuniubupakunnan'
        }
        mock_get_wx_response.return_value = data

        sess_id = get_3rd_session(
            'Yongganniuniubupakunnan', 'Bella', 'driver')
        response = self.client.post(
            "/api/login", data={'code': "beilala"}, content_type="application/json")
        errcode = response.json()['errcode']
        sess = response.json()['sess']
        self.assertEqual(errcode, 403)

    def test_reg_passenger(self):
        response = self.client.post(
            "/api/reg", data={'sess': "773"}, content_type="application/json")
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 1)
        except Exception as e:
            print("error:{}".format(e))

    def test_reg_driver(self):
        response = self.client.post(
            "/api/reg", data={'sess': "510"}, content_type="application/json")
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 1)
        except Exception as e:
            print("error:{}".format(e))

    # 测试订单流转
    @patch("GGG_backend.views.get_path")
    def test_all_okay(self, mock_get_path):
        mock_get_path.return_value = (
            [{'longitude': 114, 'latitude': 514}], 1919)
        # 司机发单
        response = self.client.post(
            "/api/driver_order", data={'sess': "963", 'origin': {'latitude': '39.935119', 'longitude': '116.423963'}}, content_type="application/json")
        driver = Driver.objects.filter(name='ashuai').first()
        status = driver.status
        self.assertEqual(status, 1)
        driver_lat = driver.lat
        driver_lon = driver.lon
        self.assertEqual(driver_lat, decimal.Decimal('39.935119'))
        self.assertEqual(driver_lon, decimal.Decimal('116.423963'))
        code = response.json()['errcode']
        self.assertEqual(code, 0)
        # 司机轮询
        response = self.client.get('/api/driver_order', data={'sess': "963", 'latitude': '39.935120', 'longitude': '116.423973'})
        code = response.json()['errcode']
        self.assertEqual(code, 1)
        user = SessionId.objects.filter(sessId="963").first()
        driver = Driver.objects.filter(name=user.username).first()
        orderid = driver.myorder_id
        self.assertEqual(orderid, -1)
        # 乘客叫车
        response = self.client.post("/api/passenger_order", data={'sess': '369', 'origin': {
                                    'name': 'Beijing', 'latitude': '39.925119', 'longitude': '116.423963'}, 'dest': {
                                    'name': 'beijing', 'latitude': '39.915119', 'longitude': '116.403963'}, 'product': 1}, content_type='application/json')
        code = response.json()['errcode']
        order_id = response.json()['order']
        order = Order.objects.filter(id=order_id).first()
        self.assertEqual(code, 0)
        product = order.product
        self.assertEqual(product, 1)
        dest_name = order.dest_name
        self.assertEqual(dest_name, 'beijing')
        origin_name = order.origin_name
        self.assertEqual(origin_name, 'Beijing')
        # 司机轮询2
        response = self.client.get('/api/driver_order', data={'sess': "963", 'latitude': '39.935120', 'longitude': '116.423973'})
        # 乘客轮询
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.get('/api/passenger_order', data={'sess': '369', 'order': order_id})
        code = response.json()['errcode']
        self.assertEqual(code, 2)
        order = Order.objects.filter(mypassenger='arui').first()
        order_status = order.status
        self.assertEqual(order_status, 1)
        # 司机接单
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        position = {'latitude': 114, 'longitude': 514}
        response = self.client.post(
            '/api/driver_get_order', data={'sess': "963", 'order': order_id, 'position': position}, content_type='application/json')
        errcode = response.json()['errcode']
        info = response.json()['info']
        self.assertEqual(errcode, 0)
        self.assertEqual(info, "arui")
        # 司机确认乘客上车
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.post(
            '/api/driver_confirm_aboard', data={'sess': "963", 'order': order_id}, content_type='application/json')
        errcode = response.json()['errcode']
        self.assertEqual(errcode, 0)
        path = response.json()['path']
        time = response.json()['time']
        self.assertEqual(path, [{'longitude': 114, 'latitude': 514}])
        self.assertEqual(time, 1)
        # 司机确认乘客到达
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.post(
            '/api/driver_confirm_arrive', data={'sess': "963", 'order': order_id}, content_type='application/json')
        errcode = response.json()['errcode']
        self.assertEqual(errcode, 0)
        # 乘客确认支付
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.post(
            '/api/passenger_pay', data={'sess': '369', 'order': order_id}, content_type='application/json')
        code = response.json()['errcode']
        self.assertEqual(code, 0)
        passenger = Passenger.objects.filter(name='arui').first()
        self.assertEqual(passenger.status, 0)
        order = Order.objects.filter(id=order_id).first()
        self.assertEqual(order.status, 2)
        # 查询历史订单
        # 乘客查询
        response = self.client.get(
            '/api/get_history_order_info', data={'sess': '369'})
        orders = response.json()['orders']
        passenger = orders[0]['passenger_info']
        self.assertEqual(passenger, 'arui')
        status = orders[0]['status']
        self.assertEqual(status, 0)
        # 司机查询
        response = self.client.get(
            '/api/get_history_order_info', data={'sess': '963'})
        orders = response.json()['orders']
        driver = orders[0]['driver_info']
        self.assertEqual(driver, 'ashua')
        status = orders[0]['status']
        self.assertEqual(status, 0)
        res1 = self.client.get('/api/get_former', data={'sess': "963", 'job': "driver"})
        res2 = self.client.get('/api/get_former', data={'sess': "369", 'job': "passenger"})
        order_id1 = Passenger.objects.filter(name="arui").first().myorder_id
        order_id2 = Driver.objects.filter(name="ashuai").first().myorder_id
        errcode1 = res1.json()['errcode']
        order1 = res1.json()['order']
        product1 = res1.json()['product']
        self.assertEqual(errcode1, 0)
        self.assertEqual(order1, order_id1)
        self.assertEqual(product1['id'], 1)
        self.assertEqual(product1['name'], "senpai")
        self.assertEqual(product1['price'], 810000.0)
        errcode2 = res2.json()['errcode']
        order2 = res2.json()['order']
        self.assertEqual(errcode2, 0)
        self.assertEqual(order2, order_id2)

    @patch("GGG_backend.views.get_path")
    def test_get_order_info_okay(self, mock_get_path):
        mock_get_path.return_value = (
            [{'longitude': 114, 'latitude': 514}], 1919)
        Order.objects.create(mypassenger='arui',product = 1,origin_lon = 1,origin_lat = 2,dest_lon= 2,dest_lat = 3)

        order = Order.objects.filter(mypassenger='arui').first()
        setup_order_id = order.id
        response = self.client.get('/api/get_order_info', data={
                                   'sess': '369', 'order': setup_order_id}, content_type='application/json')
        code = response.json()['errcode']
        passenger = response.json()['passenger_info']
        money = response.json()['money']
        self.assertEqual(code, 0)
        self.assertEqual(passenger, 'arui')
        self.assertEqual(money, 1554390)

    # # 测试获取历史订单
    def test_get_history_order_info(self):
        Order.objects.create(mypassenger='arui',mydriver = 'ashuai', money=100, status=1)
        response = self.client.get(
            '/api/get_history_order_info', data={'sess': '369'})
        orders = response.json()['orders']
        passenger = orders[0]['passenger_info']
        self.assertEqual(passenger, 'arui')
        money = orders[0]['money']
        self.assertEqual(money, 100)
        status = orders[0]['status']
        self.assertEqual(status, 1)
        response = self.client.get(
            '/api/get_history_order_info', data={'sess': '963'})
        orders = response.json()['orders']
        driver = orders[0]['driver_info']
        self.assertEqual(driver,'ashua')
        money = orders[0]['money']
        self.assertEqual(money,100)
        status = orders[0]['status']
        self.assertEqual(status,1)


    # 这是get_order_money的GET接口应该成功的测例
    def test_get_order_money_okay(self):
        Order.objects.create(mypassenger = 'arui',money = 100)
        order = Order.objects.filter(mypassenger = 'arui').first()
        order_id = order.id
        response=self.client.get(
            '/api/get_order_money', data={'sess': 369, 'order': order_id})
    
        code=response.json()['errcode']
        money=response.json()['money']
        self.assertEqual(code, 0)
        self.assertEqual(money, 100)

    # 这是get_order_money的GET接口应该失败的测例
    def test_get_order_money_failed(self):
        response=self.client.get(
            '/api/get_order_money', data={'sess': 36900, 'order': 112})

        code=response.json()['errcode']
        self.assertEqual(code, -1)

    def test_products_okay(self):
        response = self.client.get('/api/product_list', data={'sess': "510"})
        errcode = response.json()['errcode']
        product = response.json()['product']
        self.assertEqual(errcode, 0)
        namelist, price = [], []
        for item in product:
            namelist.append(item['name'])
            price.append(item['price'])
        self.assertEqual(len(product), 3)
        self.assertEqual(namelist[0], "senpai")
        self.assertEqual(namelist[1], "mur")
        self.assertEqual(namelist[2], "kmr")
        for item in price:
            self.assertEqual(item, 810000.0)
    
    def test_passenger_cancel(self):
        # 乘客叫车
        response = self.client.post("/api/passenger_order", data={'sess': '369', 'origin': {
                                    'name': 'Beijing', 'latitude': '39.925119', 'longitude': '116.423963'}, 'dest': {
                                    'name': 'beijing', 'latitude': '39.915119', 'longitude': '116.403963'}, 'product': 1}, content_type='application/json')
        code = response.json()['errcode']
        order_id = response.json()['order']
        order = Order.objects.filter(id=order_id).first()
        self.assertEqual(code, 0)
        product = order.product
        self.assertEqual(product, 1)
        dest_name = order.dest_name
        self.assertEqual(dest_name, 'beijing')
        origin_name = order.origin_name
        self.assertEqual(origin_name, 'Beijing')
        # 乘客轮询
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.get(
            '/api/passenger_order', data={'sess': '369', 'order': order_id})
        code = response.json()['errcode']
        self.assertEqual(code, 1)
        user = SessionId.objects.filter(sessId="369").first()
        passenger = Passenger.objects.filter(name=user.username).first()
        origin_lat = passenger.lat
        self.assertEqual(origin_lat, decimal.Decimal('39.925119'))
        origin_lon = passenger.lon
        self.assertEqual(origin_lon, decimal.Decimal('116.423963'))
        # 司机发单
        response = self.client.post(
            "/api/driver_order", data={'sess': "963", 'origin': {'latitude': '39.935119', 'longitude': '116.423963'}}, content_type="application/json")
        driver = Driver.objects.filter(name='ashuai').first()
        status = driver.status
        self.assertEqual(status, 2)
        driver_lat = driver.lat
        driver_lon = driver.lon
        self.assertEqual(driver_lat, decimal.Decimal('39.935119'))
        self.assertEqual(driver_lon, decimal.Decimal('116.423963'))
        code = response.json()['errcode']
        self.assertEqual(code, 0)
        # 司机轮询
        response = self.client.get('/api/driver_order', data={'sess': "963", 'latitude': '39.935120', 'longitude': '116.423973'})
        code = response.json()['errcode']
        self.assertEqual(code, 2)
        order = Order.objects.filter(mydriver='ashuai').first()
        order_status = order.status
        self.assertEqual(order_status, 1)
        res = self.client.post("/api/passenger_cancel", data={'sess': "369", 'order': order.id}, content_type="application/json")
        passenger = Passenger.objects.filter(name=user.username).first()
        driver = Driver.objects.filter(name='ashuai').first()
        self.assertEqual(passenger.status, 0)
        self.assertEqual(driver.status, 1)
        self.assertEqual(res.json()['errcode'], 0)

    def test_driver_cancel(self):
        # 乘客叫车
        response = self.client.post("/api/passenger_order", data={'sess': '369', 'origin': {
                                    'name': 'Beijing', 'latitude': '39.925119', 'longitude': '116.423963'}, 'dest': {
                                    'name': 'beijing', 'latitude': '39.915119', 'longitude': '116.403963'}, 'product': 1}, content_type='application/json')
        code = response.json()['errcode']
        order_id = response.json()['order']
        order = Order.objects.filter(id=order_id).first()
        self.assertEqual(code, 0)
        product = order.product
        self.assertEqual(product, 1)
        dest_name = order.dest_name
        self.assertEqual(dest_name, 'beijing')
        origin_name = order.origin_name
        self.assertEqual(origin_name, 'Beijing')
        # 乘客轮询
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.get(
            '/api/passenger_order', data={'sess': '369', 'order': order_id})
        code = response.json()['errcode']
        self.assertEqual(code, 1)
        user = SessionId.objects.filter(sessId="369").first()
        passenger = Passenger.objects.filter(name=user.username).first()
        origin_lat = passenger.lat
        self.assertEqual(origin_lat, decimal.Decimal('39.925119'))
        origin_lon = passenger.lon
        self.assertEqual(origin_lon, decimal.Decimal('116.423963'))
        # 司机发单
        response = self.client.post(
            "/api/driver_order", data={'sess': "963", 'origin': {'latitude': '39.935119', 'longitude': '116.423963'}}, content_type="application/json")
        driver = Driver.objects.filter(name='ashuai').first()
        status = driver.status
        self.assertEqual(status, 2)
        driver_lat = driver.lat
        driver_lon = driver.lon
        self.assertEqual(driver_lat, decimal.Decimal('39.935119'))
        self.assertEqual(driver_lon, decimal.Decimal('116.423963'))
        code = response.json()['errcode']
        self.assertEqual(code, 0)
        # 司机轮询
        response = self.client.get('/api/driver_order', data={'sess': "963", 'latitude': '39.935120', 'longitude': '116.423973'})
        code = response.json()['errcode']
        self.assertEqual(code, 2)
        order = Order.objects.filter(mydriver='ashuai').first()
        order_status = order.status
        self.assertEqual(order_status, 1)
        res = self.client.post("/api/driver_cancel", data={'sess': "963", 'order': order.id}, content_type="application/json")
        passenger = Passenger.objects.filter(name=user.username).first()
        driver = Driver.objects.filter(name='ashuai').first()
        self.assertEqual(passenger.status, 1)
        self.assertEqual(driver.status, 0)
        self.assertEqual(res.json()['errcode'], 0)

    def test_check_session_id(self):
        res1 = self.client.get('/api/check_session_id', data={'sess': "369", 'job': "passenger"})
        res2 = self.client.get('/api/check_session_id', data={'sess': "963", 'job': "driver"})
        errcode1 = res1.json()['errcode']
        errcode2 = res2.json()['errcode']
        self.assertEqual(errcode1, 0)
        self.assertEqual(errcode2, 0)

    def test_driver_choose_product(self):
        res = self.client.post('/api/driver_choose_product', data={'sess': "963", 'product': 2}, content_type="application/json")  
        driver = Driver.objects.filter(name="ashuai").first()  
        self.assertEqual(driver.product, 2)
        self.assertEqual(res.json()['errcode'], 0)


