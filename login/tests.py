from distutils.log import error
from urllib import response
from django.test import TestCase
from login.models import Driver, Passenger, SessionId
from login.views import wx_response
from pytest_mock import mocker
import pytest
import json


class mockreq:
    def json():
        return {"openid": "ddddddddddddddddddd",
                "session_key": "eeeeeeeeeeeeeeeeeee"
                }


class login_test(TestCase):
    def set_up(self):
        SessionId.objects.create(
            sessId="773", username="nana7mi", job="Passenger")
        SessionId.objects.create(sessId="510", username="azi", job="Driver")
    # def test_login_passenger(self, mocker):
    #	instance = wx_response()
    #	data = {
    #		'openid' : 'nana7mi',
    #		'session_key' : 'tieguizongdeichuangsiyigeren'
    #	}
    #	instance.get_wx_response = mocker.patch('login.views.get_wx_response', return_value = json.dumps(data))
    #	response = self.client.get("/api/login", {'code' : "qihai", "job" : "Passenger"})
    #	errcode = response.json()['errcode']
    #	sess = response.json()['sess']
    #	self.assertEqual(errcode, 0)
    #	self.assertEqual(sess, "773")

    def test_login_passenger(self, monkeypatch):
        def mockreturn(*args, **kwargs):
            return mockreq()
		
		

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
