from distutils.log import error
from urllib import response
from django.test import TestCase
from login.models import Driver, Passenger, SessionId

class helloworld_test(TestCase):
	def set_up(self):
		SessionId.objects.create(sessId = "773", username = "nana7mi", job = "Passenger")
		SessionId.objects.create(sessId = "510", username = "azi", job = "Driver")
	def test_login(self):
		pass # 需要实际code,获取对应结果以进行测试
	def test_reg_passenger(self):	
		response = self.client.get("/api/reg", {'sess' : "773"})
		try:
			code = response.json()['errcode']
			self.assertEqual(code, 1)
		except Exception as e:
			print("error:{}".format(e))
	def test_reg_driver(self):	
		response = self.client.get("/api/reg", {'sess' : "510"})
		try:
			code = response.json()['errcode']
			self.assertEqual(code, 1)
		except Exception as e:
			print("error:{}".format(e))		
			


