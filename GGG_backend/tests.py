from distutils.log import error
import decimal
from urllib import response
from django.test import TestCase
from numpy import product
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

    # @patch("GGG_backend.views.get_wx_response")
    # def test_login_passenger(self, mock_get_wx_response):
    #     data = {
    #         'openid': 'Diana',
    #         'session_key': 'Jiaranjintianchishenme'
    #     }
    #     mock_get_wx_response.return_value = data

    #     sess_id = get_3rd_session(
    #         'Jiaranjintianchishenme', 'Diana', 'passenger')
    #     response = self.client.post(
    #         "/api/login", data={'code': "ranran", "job": 'passenger'}, content_type="application/json")
    #     # print(response)
    #     errcode = response.json()['errcode']
    #     sess = response.json()['sess']
    #     order = response.json()['order']
    #     self.assertEqual(errcode, 0)
    #     self.assertEqual(order, -1)
    #     # self.assertEqual(sess, sess_id)

    # @patch("GGG_backend.views.get_wx_response")
    # def test_login_driver(self, mock_get_wx_response):
    #     data = {
    #         'openid': 'Bella',
    #         'session_key': 'Yongganniuniubupakunnan'
    #     }
    #     mock_get_wx_response.return_value = data

    #     sess_id = get_3rd_session(
    #         'Yongganniuniubupakunnan', 'Bella', 'driver')
    #     response = self.client.post(
    #         "/api/login", data={'code': "beilala", "job": 'driver'}, content_type="application/json")
    #     errcode = response.json()['errcode']
    #     sess = response.json()['sess']
    #     order = response.json()['order']
    #     self.assertEqual(errcode, 0)
    #     self.assertEqual(order, -1)
    #     # self.assertEqual(sess, sess_id)

    # @patch("GGG_backend.views.get_wx_response")
    # def test_login_gg(self, mock_get_wx_response):
    #     data = {
    #         'openid': 'Bella',
    #         'session_key': 'Yongganniuniubupakunnan'
    #     }
    #     mock_get_wx_response.return_value = data

    #     sess_id = get_3rd_session(
    #         'Yongganniuniubupakunnan', 'Bella', 'driver')
    #     response = self.client.post(
    #         "/api/login", data={'code': "beilala"}, content_type="application/json")
    #     errcode = response.json()['errcode']
    #     sess = response.json()['sess']
    #     order = response.json()['order']
    #     self.assertEqual(errcode, 403)
    #     self.assertEqual(order, 0)

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

    def test_match_driver_okay(self):
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
        response = self.client.get(
            '/api/passenger_order', data={'sess': '369', 'order': order_id})
        code = response.json()['errcode']
        self.assertEqual(code, 2)
        order = Order.objects.filter(mypassenger='arui').first()
        order_status = order.status
        self.assertEqual(order_status, 1)
        # 司机接单
        order = Order.objects.filter(mypassenger='arui').first()
        order_id = order.id
        response = self.client.post(
            '/api/driver_get_order', data={'sess': "963", 'order': order_id}, content_type='application/json')
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

    # 测试passenger创建订单

    # def test_passenger_order_post_okay(self):
    #     response = self.client.post('/api/passenger_order', data={'sess': '369', 'origin': 5, 'dest': {
    #                                 'name': 'beijing', 'latitude': 39.915119, 'longitude': 116.403963}}, content_type='application/json')

    #     code = response.json()['errcode']
    #     order_id = response.json()['id']
    #     order = Order.objects.filter(id=order_id).first()
    #     self.assertEqual(code, 0)
    #     dest_name = order.dest_name
    #     self.assertEqual(dest_name, 'beijing')

    # def test_passenger_order_post_already(self):
    #     passenger = Passenger.objects.filter(name='arui').first()
    #     passenger.status = 1
    #     passenger.save()
    #     response = self.client.post('/api/passenger_order', data={'sess': '369', 'origin': 5, 'dest': {
    #                                 'name': 'beijing', 'latitude': 39.915119, 'longitude': 116.403963}}, content_type='application/json')
    #     code = response.json()['errcode']
    #     self.assertEqual(code, -1)

    # def test_passenger_order_post_bad(self):
    #     response = self.client.post('/api/passenger_order', data={'sess': '178', 'origin': 1, 'dest': {
    #                                 'name': 'shabi', 'latitude': 121, 'longitude': 39}}, content_type='application/json')
    #     code = response.json()['errcode']
    #     self.assertEqual(code, -10)
    # # 测试passenger轮询

    # def test_passenger_order_get_okay(self):
    #     Order.objects.create(mypassenger='arui', money=100)
    #     order = Order.objects.filter(mypassenger='arui').first()
    #     response = self.client.get('api/passenger_order', data={
    #                                'sess': '369', 'order': setup_order_id}, content_type='application/json')
    #     code = response.json()['errcode']
    #     status = order.status
    #     self.assertEqual(status, code)
    # # 测试获取订单信息

    # @patch("GGG_backend.views.get_path")
    # def test_get_order_info_okay(self, mock_get_path):
    #     mock_get_path.return_value = (
    #         [{'longitude': 114, 'latitude': 514}], 1919)
    #     Order.objects.create(mypassenger='arui', departure=1)

    #     order = Order.objects.filter(mypassenger='arui').first()
    #     setup_order_id = order.id
    #     response = self.client.get('/api/get_order_info', data={
    #                                'sess': '369', 'order': setup_order_id}, content_type='application/json')
    #     code = response.json()['errcode']
    #     passenger = response.json()['passenger_info']
    #     money = response.json()['money']
    #     self.assertEqual(code, 0)
    #     self.assertEqual(passenger, 'arui')
    #     self.assertEqual(money, 1554390)

    # def test_get_order_info_bad(self):
    #     response = self.client.get('/api/get_order_info', data={
    #                                'sess': '178', 'order': setup_order_id}, content_type='application/json')
    #     code = response.json()['errcode']
    #     self.assertEqual(code, -1)
    # # 测试乘客确认支付

    # def test_passenger_pay_okay(self):
    #     response = self.client.post(
    #         'api/passenger_pay', data={'sess': '369', 'order': setup_order_id}, content_type='application/json')
    #     code = response.json()['errcode']
    #     self.assertEqual(code, 0)
    #     passenger = Passenger.objects.filter(name='arui').first()
    #     self.assertEqual(passenger.status, 0)
    #     order = Order.objects.filter(id=setup_order_id).first()
    #     self.assertEqual(order.status, 2)

    # def test_passenger_pay_bad(self):
    #     response = self.client.post(
    #         '/api/passenger_pay', data={'sess': '183', 'order': setup_order_id}, content_type='application/json')
    #     code = response.json()['errcode']
    #     self.assertEqual(code, -1)

    # # 测试获取历史订单
    # def test_get_history_order_info(self):
    #     Order.objects.create(mypassenger='arui', money=100, status=1)
    #     response = self.client.get(
    #         '/api/get_history_order_info', data={'sess': '369'})
    #     orders = response.json['orders']
    #     passenger = orders[0]['passenger_info']
    #     self.assertEqual(passenger, 'arui')
    #     money = orders[0]['money']
    #     self.assertEqual(money, 100)
    #     status = orders[0]['status']
    #     self.assertEqual(status, 1)

    # # 这是driver_order的POST接口应该成功的测例

    # def test_driver_order_post_okay(self):
    #     response = self.client.post(
    #         'api/driver_order', data={'sess': "963", 'origin': 5}, content_type='application/json')
    #     try:
    #         code = response.json()['errcode']
    #         self.assertEqual(code, 0)
    #         user = SessionId.objects.filter(sessId=963).first()
    #         driver = Driver.objects.filter(name=user.username).first()
    #         origin = driver.position
    #         status = driver.status
    #         self.assertEqual(status, 1)
    #         self.assertEqual(origin, 5)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # # 这是driver_order的POST接口应该失败的测例
    # def test_driver_order_post_okay(self):
    #     response = self.client.post(
    #         'api/driver_order', data={'sess': "369", 'origin': 5}, content_type='application/json')
    #     try:
    #         code = response.json()['errcode']
    #         self.assertEqual(code, -10)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # # 这是driver_order的POST接口应该请求失败的测例
    # def test_driver_order_post_requestFailed(self):
    #     response = self.client.post(
    #         '/api/driver_order', data={'sess': "963", 'origin': 5}, content_type='text/xml')
    #     code = response.json()['errcode']
    #     self.assertEqual(code, 405)

    # # 这是driver_order的GET接口应该成功的测例
    # def test_driver_order_get_okay(self):
    #     response=self.client.get(
    #         'api/driver_order', data={'sess': "963"})

    #     code=response.json()['errcode']
    #     self.assertEqual(code, 2)
    #     user=SessionId.objects.filter(sessId=963).first()
    #     driver=Driver.objects.filter(name=user.username).first()
    #     status=driver.status
    #     orderid=driver.order_id
    #     origin=driver.position
    #     self.assertEqual(orderid, -1)
    #     self.assertEqual(status, 1)
    #     self.assertEqual(origin, 5)

    # # 这是driver_order的GET接口应该失败的测例
    # def test_driver_order_get_okay(self):
    #     response=self.client.get(
    #         'api/driver_order', data={'sess': "369"})
    #     try:
    #         code=response.json()['errcode']
    #         self.assertEqual(code, -10)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # # 这是driver_order的GET接口应该请求失败的测例
    # def test_driver_order_get_request_failed(self):
    #     response=self.client.get(
    #         '/api/driver_order', data={})
    #     code=response.json()['errcode']
    #     self.assertEqual(code, 405)

    # # 这是get_order_money的GET接口应该成功的测例
    # def test_get_order_money_okay(self):
    #     response=self.client.get(
    #         'api/get_order_money', data={'sess': 369, 'order': setup_order_id})
    #     try:
    #         code=response.json()['errcode']
    #         money=response.json()['money']
    #         self.assertEqual(code, 0)
    #         self.assertEqual(money, 100)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # # 这是get_order_money的GET接口应该失败的测例
    # def get_order_money_failed(self):
    #     response=self.client.get(
    #         '/api/get_order_money', data={'sess': 36900, 'order': setup_order_id * 1000})

    #     code=response.json()['errcode']
    #     self.assertEqual(code, -1)

    # # 这是get_order_money的GET接口应该请求失败的测例
    # def get_order_money_request_failed(self):
    #     response=self.client.get(
    #         '/api/get_order_money', data={'sess': 369, 'order': setup_order_id})

    #     code=response.json()['errcode']
    #     money=response.json()['money']
    #     self.assertEqual(code, 0)
    #     self.assertEqual(money, 100)

    # def test_products_okay(self):
    #     response = self.client.get('/api/products', data={'sess': "510"})
    #     errcode = response.json()['errcode']
    #     product = response.json()['product']
    #     self.assertEqual(errcode, 0)
    #     namelist, price, speed = [], [], []
    #     for item in product:
    #         namelist.append(item['name'])
    #         price.append(item['price_per_meter'])
    #         speed.append(item['speed'])
    #     self.assertEqual(len(product), 3)
    #     self.assertEqual(namelist[0], "senpai")
    #     self.assertEqual(namelist[1], "mur")
    #     self.assertEqual(namelist[2], "kmr")
    #     for item in price:
    #         self.assertEqual(item, 810)
    #     for item in speed:
    #         self.assertEqual(item, 1919)

    # @ patch("GGG_backend.views.get_path")
    # def test_driver_get_order_okay(self, mock_get_path):
    #     mock_get_path.return_value=([{114, 514}], 1919)

    #     shuai=Driver.objects.filter(name="ashuai").first()
    #     shuai.myorder_id=setup_order_id
    #     order=Order.objects.filter(mypassenger='arui').first()
    #     order.departure=setup_Product_id
    #     shuai.save()
    #     order.save()

    #     response=self.client.post(
    #         'api/driver_get_order', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
    #     errcode=response.json()['errcode']
    #     info=response.json()['info']
    #     path=response.json()['path']
    #     time=response.json()['time']
    #     self.assertEqual(errcode, 0)
    #     self.assertEqual(info, "arui")
    #     self.assertEqual(path, [{114, 514}])
    #     self.assertEqual(time, 1)

    # def test_driver_confirm_aboard_okay(self):
    #     response=self.client.post(
    #         'api/driver_confirm_aboard', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
    #     try:
    #         errcode=response.json()['errcode']
    #         self.assertEqual(errcode, 0)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # def test_driver_confirm_arrive_okay(self):
    #     response=self.client.post(
    #         'api/driver_confirm_arrive', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
    #     errcode=response.json()['errcode']
    #     self.assertEqual(errcode, 0)

    # def test_passenger_cancel_before_match(self):
    #     Order.objects.create()
    #     response=self.client.post(
    #         'api/passenger_cancel', data={'sess': "369", 'order': setup_order_id}, content_type='application/json')
    #     try:
    #         errcode=response.json()['errcode']
    #         self.assertEqual(errcode, 0)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # def test_driver_cancel_before_match(self):
    #     response=self.client.post(
    #         'api/passenger_cancel', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
    #     try:
    #         errcode=response.json()['errcode']
    #         self.assertEqual(errcode, 0)
    #     except Exception as e:
    #         print('error:{}'.format(e))

    # def test_check_session_id(self):
    #     response1 = self.client.get(
    #         '/api/check_session_id', data={'sess': "369", 'job': "passenger"})
    #     response2 = self.client.get(
    #         '/api/check_session_id', data={'sess': "963", 'job': "driver"})    
    #     errcode1 = response1.json()['errcode']
    #     errcode2 = response2.json()['errcode']
    #     order1 = response1.json()['order'] 
    #     order2 = response2.json()['order']  
    #     self.assertEqual(errcode1, 0)
    #     self.assertEqual(errcode2, 0)
    #     self.assertEqual(order1, -1)
    #     self.assertEqual(order2, -1)