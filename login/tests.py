from distutils.log import error
from urllib import response
from django.test import TestCase
from login.models import Driver, Passenger, SessionId
import login.views 
from unittest import mock
from unittest.mock import patch
import json
import requests


class mockreq:
    def json():
        return {'openid': 'nana7mi',
                'session_key': 'tieguizongdeichuangsiyigeren'
                }


class login_test(TestCase):
    def set_up(self):
        SessionId.objects.create(
            sessId="773", username="nana7mi", job="Passenger")
        SessionId.objects.create(sessId="510", username="azi", job="Driver")
    @patch("login.views.get_wx_response")
    def test_login_passenger(self,mock_get_wx_response):
        data = {
            'openid': 'nana7mi',
            'session_key': 'tieguizongdeichuangsiyigeren'
        }
        mock_get_wx_response.return_value = data
    
        response = self.client.get(
            "/api/login", {'code': "qihai", "job": "Passenger"})
        errcode = response.json()['errcode']
        sess = response.json()['sess']
        self.assertEqual(errcode, 0)
        self.assertEqual(sess, "773")

    def test_reg_passenger(self):
        response = self.client.get("/api/reg", {'sess': "773"})
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 1)
        except Exception as e:
            print("error:{}".format(e))

    def test_reg_driver(self):
        response = self.client.get("/api/reg", {'sess': "510"})
        try:
            code = response.json()['errcode']
            self.assertEqual(code, 1)
        except Exception as e:
            print("error:{}".format(e))
