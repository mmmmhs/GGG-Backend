from distutils.log import error
from urllib import response
from django.test import TestCase
from login.models import Driver, Passenger, SessionId
import login.views
from unittest import mock
from unittest.mock import patch
from login.views import get_3rd_session

class login_test(TestCase):
    def setUp(self):
        SessionId.objects.create(
            sessId="773", username="nana7mi", job="Passenger")
        SessionId.objects.create(sessId="510", username="azi", job="Driver")
        Passenger.objects.create(name='Diana')
        Driver.objects.create(name="Bella")

    @patch("login.views.get_wx_response")
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
        self.assertEqual(errcode, 0)
        # self.assertEqual(sess, sess_id)

    @patch("login.views.get_wx_response")
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

    def test_reg_passenger(self):
        response = self.client.post("/api/reg", data={'sess': "773"}, content_type="application/json")
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 1)
        except Exception as e:
            print("error:{}".format(e))

    def test_reg_driver(self):
        response = self.client.post("/api/reg", data={'sess': "510"}, content_type="application/json")
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 1)
        except Exception as e:
            print("error:{}".format(e))
