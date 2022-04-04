from distutils.log import error
from urllib import response
from django.test import TestCase
from GGG_backend.models import Driver, Order, Passenger, SessionId, Poi
import GGG_backend.views
from unittest import mock
from unittest.mock import patch
from GGG_backend.views import get_3rd_session, driver_unmatched


class login_test(TestCase):
    def setUp(self):
        SessionId.objects.create(
            sessId="773", username="nana7mi", job="Passenger")
        SessionId.objects.create(sessId="510", username="azi", job="Driver")
        Passenger.objects.create(name='Diana')
        Driver.objects.create(name="Bella")
        Poi.objects.create(name='senpai', latitude=114,
                           longitude=514, price_per_meter=810, speed=1919)
        Poi.objects.create(name='mur', latitude=114,
                           longitude=514, price_per_meter=810, speed=1919)
        Poi.objects.create(name='kmr', latitude=114,
                           longitude=514, price_per_meter=810, speed=1919)                                       

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
        print(response)
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

    def test_driver_order_post_okay(self):
        response = self.client.post(
            'api/driver_order', data={'sess': "510", 'origin': 5}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 0)
            driver = Driver.objects.get(name='510')
            origin = driver.position
            status = driver.status
            self.assertEqual(status, 1)
            self.assertEqual(origin, 5)
        except Exception as e:
            print('error:{}'.format(e))

    def test_driver_order_get_okay(self):
        response = self.client.get(
            'api/driver_order', data={'sess': "510"}, content_type='application/json')
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 2)
            driver = Driver.objects.get(name='510')
            status = driver.status
            orderid = driver.order_id
            origin = driver.position
            self.assertEqual(orderid, -1)
            self.assertEqual(status, 1)
            self.assertEqual(origin, 5)
        except Exception as e:
            print('error:{}'.format(e))

    def test_pois(self):
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
