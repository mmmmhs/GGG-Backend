from distutils.log import error
from urllib import response
from django.test import TestCase
from models import Driver, Passenger, SessionId

class helloworld_test(TestCase):
	def set_up(self):
		SessionId.objects.create(Id = "773", username = "nana7mi", job = "Passenger")
		SessionId.objects.create(Id = "510", username = "azi", job = "Driver")
	def test_login(self):
		pass
		# 暂时无法测试：需要合法code以匹配相应结果
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
			

# Create your tests here.
