from distutils.log import error
from unicodedata import name
from urllib import response
from django.test import TestCase
from GGG_backend.models import Driver, Order, Passenger, SessionId, Poi
import GGG_backend.views
from unittest import mock
from unittest.mock import patch
from GGG_backend.views import get_3rd_session, driver_unmatched

setup_order_id = 0
setup_poi_id = 0


class GGG_test(TestCase):
    def setUp(self):
        # 以下用于测试注册
        SessionId.objects.create(
            sessId="773", username="nana7mi", job="Passenger")
        SessionId.objects.create(sessId="510", username="azi", job="Driver")

        # 以下用于测试登录
        Passenger.objects.create(name='Diana')
        Driver.objects.create(name="Bella")

        # 以下用于测试订单流转
        SessionId.objects.create(sessId="369", username="arui", job="Passenger")
        Passenger.objects.create(name="arui", status=0)
        SessionId.objects.create(sessId="963", username='ashuai', job='Driver')
        Driver.objects.create(name="ashuai", status=0)
        Order.objects.create(mypassenger="arui", money=100)
        order = Order.objects.filter(mypassenger='arui').first()
        setup_order_id = order.id

        # POI
        Poi.objects.create(name='senpai', latitude=114,
                           longitude=514, price_per_meter=810, speed=1919)
        Poi.objects.create(name='mur', latitude=114,
                           longitude=514, price_per_meter=810, speed=1919)
        Poi.objects.create(name='kmr', latitude=114,
                           longitude=514, price_per_meter=810, speed=1919)
        setup_poi_id = Poi.objects.filter(name='senpai').first().id

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
        order = response.json()['order']
        self.assertEqual(errcode, 0)
        self.assertEqual(order, -1)
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
        order = response.json()['order']
        self.assertEqual(errcode, 0)
        self.assertEqual(order, -1)
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
        order = response.json()['order']
        self.assertEqual(errcode, 403)
        self.assertEqual(order, 0)

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
    def test_all_okay(self):
        response = self.client.post(
            "/api/reg", data={'sess': "963", 'origin': 1}, content_type="application/json")
        driver = Driver.objects.filter(name='ashuai').first()
        status = driver.status
        self.assertEqual(status, 1)


    # 测试passenger创建订单
    def test_passenger_order_post_okay(self):
        response = self.client.post('api/passenger_order', data={'sess': '369', 'origin': 5, 'dest': {
                                    'name': 'beijing', 'latitude': 39.915119, 'longitude': 116.403963}}, content_type='application/json')
        try:
            code = response.json()['errcode']
            order_id = response.json()['id']
            order = Order.objects.filter(id=order_id).first()
            self.assertEqual(code, 0)
            depature = order.depature
            self.assertEqual(depature, 5)
            dest_name = order.dest_name
            self.assertEqual(dest_name, 'beijing')
        except Exception as e:
            print('error:{}'.format(e))

    def test_passenger_order_post_already(self):
        passenger = Passenger.objects.filter(name='arui').first()
        passenger.status = 1
        passenger.save()
        response = self.client.post('api/passenger_order', data={'sess': '369', 'origin': 5, 'dest': {
                                    'name': 'beijing', 'latitude': 39.915119, 'longitude': 116.403963}}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -1)
            passenger.status = 0
            passenger.save()
        except Exception as e:
            print('error:{}'.format(e))

    def test_passenger_order_post_bad(self):
        response = self.client.post('api/passenger_order', data={'sess': '178', 'origin': 1, 'dest': {
                                    'name': 'shabi', 'latitude': 121, 'longitude': 39}}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -10)
        except Exception as e:
            print('error:{}'.format(e))
    # 测试passenger轮询

    def test_passenger_order_get_okay(self):
        order = Order.objects.filter(id=setup_order_id).first()
        passenger = Passenger.objects.filter(name='arui')
        response = self.client.get('api/passenger_order', data={
                                   'sess': '369', 'order': setup_order_id}, content_type='application/json')
        try:
            code = response.json()['errcode']
            status = order.status
            self.assertEqual(status, code)
        except Exception as e:
            print('error:{}'.format(e))
    # 测试获取订单信息

    def test_get_order_info_okay(self):
        order = Order.objects.filter(id=setup_order_id).first()
        response = self.client.get('api/get_order_info', data={
                                   'sess': '369', 'order': setup_order_id}, content_type='application/json')
        try:
            code = response.json()['errcode']
            passenger = response.json()['passenger_info']
            money = response.json()['money']
            self.assertEqual(code, 0)
            self.assertEqual(passenger, 'arui')
            self.assertEqual(money, 100)
        except Exception as e:
            print('error:{}'.format(e))

    def test_get_order_info_bad(self):
        response = self.client.get('api/get_order_info', data={
                                   'sess': '178', 'order': setup_order_id}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -1)
        except Exception as e:
            print('error:{}'.format(e))
    # 测试乘客确认支付

    def test_passenger_pay_okay(self):
        response = self.client.post(
            'api/passenger_pay', data={'sess': '369', 'order': setup_order_id}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 0)
            passenger = Passenger.objects.filter(name='arui').first()
            self.assertEqual(passenger.status, 0)
            order = Order.objects.filter(id=setup_order_id).first()
            self.assertEqual(order.status, 2)
        except Exception as e:
            print('error:{}'.format(e))

    def test_passenger_pay_bad(self):
        response = self.client.post(
            'api/passenger_pay', data={'sess': '183', 'order': setup_order_id}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -1)
        except Exception as e:
            print('error:{}'.format(e))

    # 测试获取历史订单
    def test_get_history_order_info(self):
        response = self.client.get(
            'api/get_history_order_info', data={'sess': '369'}, content_type='application/json')
        try:
            orders = response.json['orders']
            passenger = orders[0]['passenger_info']
            self.assertEqual(passenger, 'arui')
            money = orders[0]['money']
            self.assertEqual(money, 100)
            status = orders[0]['status']
            self.assertEqual(status, 1)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是driver_order的POST接口应该成功的测例
    def test_driver_order_post_okay(self):
        response = self.client.post(
            'api/driver_order', data={'sess': "963", 'origin': 5}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 0)
            user = SessionId.objects.filter(sessId=963).first()
            driver = Driver.objects.filter(name=user.username).first()
            origin = driver.position
            status = driver.status
            self.assertEqual(status, 1)
            self.assertEqual(origin, 5)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是driver_order的POST接口应该失败的测例
    def test_driver_order_post_okay(self):
        response = self.client.post(
            'api/driver_order', data={'sess': "369", 'origin': 5}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -10)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是driver_order的POST接口应该请求失败的测例
    def test_driver_order_post_requestFailed(self):
        response = self.client.post(
            'api/driver_order', data={'sess': "963", 'origin': 5}, content_type='text/xml')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 405)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是driver_order的GET接口应该成功的测例
    def test_driver_order_get_okay(self):
        response = self.client.get(
            'api/driver_order', data={'sess': "963"})

        code = response.json()['errcode']
        self.assertEqual(code, 2)
        user = SessionId.objects.filter(sessId=963).first()
        driver = Driver.objects.filter(name=user.username).first()
        status = driver.status
        orderid = driver.order_id
        origin = driver.position
        self.assertEqual(orderid, -1)
        self.assertEqual(status, 1)
        self.assertEqual(origin, 5)

    # 这是driver_order的GET接口应该失败的测例
    def test_driver_order_get_okay(self):
        response = self.client.get(
            'api/driver_order', data={'sess': "369"})
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -10)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是driver_order的GET接口应该请求失败的测例
    def test_driver_order_get_request_failed(self):
        response = self.client.get(
            'api/driver_order', data={})
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 405)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是get_order_money的GET接口应该成功的测例
    def test_get_order_money_okay(self):
        response = self.client.get(
            'api/get_order_money', data={'sess': 369, 'order': setup_order_id})
        try:
            code = response.json()['errcode']
            money = response.json()['money']
            self.assertEqual(code, 0)
            self.assertEqual(money, 100)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是get_order_money的GET接口应该失败的测例
    def get_order_money_failed(self):
        response = self.client.get(
            'api/get_order_money', data={'sess': 36900, 'order': setup_order_id * 1000})
        try:
            code = response.json()['errcode']
            self.assertEqual(code, -1)
        except Exception as e:
            print('error:{}'.format(e))

    # 这是get_order_money的GET接口应该请求失败的测例
    def get_order_money_request_failed(self):
        response = self.client.get(
            'api/get_order_money', data={'sess': 369, 'order': setup_order_id})
        try:
            code = response.json()['errcode']
            money = response.json()['money']
            self.assertEqual(code, 0)
            self.assertEqual(money, 100)
        except Exception as e:
            print('error:{}'.format(e))

    def test_pois_okay(self):
        response = self.client.get(
            'api/pois', data={'sess': "510"}, content_type='application/json')
        try:
            errcode = response.json()['errcode']
            pois = response.json()['pois']
            self.assertEqual(errcode, 0)
            namelist, lat, lon, price, speed = []
            for item in pois:
                namelist.append(item['name'])
                lat.append(item['latitude'])
                lon.append(item['longitude'])
                price.append(item['price_per_meter'])
                speed.append(item['speed'])
            self.assertEqual(len(pois), 3)
            self.assertEqual(namelist[0], "senpai")
            self.assertEqual(namelist[1], "mur")
            self.assertEqual(namelist[2], "kmr")
            for item in lat:
                self.assertEqual(item, 114)
            for item in lon:
                self.assertEqual(item, 514)
            for item in price:
                self.assertEqual(item, 810)
            for item in speed:
                self.assertEqual(item, 1919)
        except Exception as e:
            print('error:{}'.format(e))

    @patch("GGG_backend.views.get_path")
    def test_driver_get_order_okay(self, mock_get_path):
        mock_get_path.return_value = ([{114, 514}], 1919)

        shuai = Driver.objects.filter(name="ashuai").first()
        shuai.myorder_id = setup_order_id
        order = Order.objects.filter(mypassenger='arui').first()
        order.departure = setup_poi_id
        shuai.save()
        order.save()

        response = self.client.post(
            'api/driver_get_order', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
        try:
            errcode = response.json()['errcode']
            info = response.json()['info']
            path = response.json()['path']
            time = response.json()['time']
            self.assertEqual(errcode, 0)
            self.assertEqual(info, "arui")
            self.assertEqual(path, [{114, 514}])
            self.assertEqual(time, 1)
        except Exception as e:
            print('error:{}'.format(e))

    def test_driver_confirm_aboard_okay(self):
        response = self.client.post(
            'api/driver_confirm_aboard', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
        try:
            errcode = response.json()['errcode']
            self.assertEqual(errcode, 0)
        except Exception as e:
            print('error:{}'.format(e))

    def test_driver_confirm_arrive_okay(self):
        response = self.client.post(
            'api/driver_confirm_arrive', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
        try:
            errcode = response.json()['errcode']
            self.assertEqual(errcode, 0)
        except Exception as e:
            print('error:{}'.format(e))

    def test_passenger_cancel_okay(self):
        response = self.client.post(
            'api/passenger_cancel', data={'sess': "369", 'order': setup_order_id}, content_type='application/json')
        try:
            errcode = response.json()['errcode']
            self.assertEqual(errcode, 0)
        except Exception as e:
            print('error:{}'.format(e))

    def test_driver_cancel_okay(self):
        response = self.client.post(
            'api/passenger_cancel', data={'sess': "963", 'order': setup_order_id}, content_type='application/json')
        try:
            errcode = response.json()['errcode']
            self.assertEqual(errcode, 0)
        except Exception as e:
            print('error:{}'.format(e))
