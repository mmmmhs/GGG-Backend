from ast import Return
from email.policy import default
import json
from logging import exception
from re import U
from django.forms import ValidationError
from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from login.models import Driver, Passenger, SessionId
import secoder.settings
import random
import string
import hashlib
import logging
logger = logging.getLogger('django')


def index(request):
    return HttpResponse("Hello world.")


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
            return HttpResponse("error:{}".format(e), status=405)
        data = get_wx_response(code)
        try:
            openID = data['openid']
            sessionID = get_3rd_session(data['session_key'], openID, job)
            print(openID, sessionID)
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
                user = 0
            if not user:
                errorcode = -10
            SessionId.objects.update_or_create(username=openID, defaults={
                                               "sessId": sessionID, "job": job})
            res = JsonResponse({'errcode': errorcode, 'sess': sessionID})
            # res.headers['Content-Type'] = 'application/json'
            return res
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)


def reg(request):
    if(request.method == 'POST'):
        try:
            reqjson = json.loads(request.body)
            sess = reqjson['sess']
        except Exception as e:
            return HttpResponse("error:{}".format(e), status=405)
        try:
            user = SessionId.objects.filter(sessId=sess).first()
            if(user.job == "passenger"):
                Passenger.objects.create(name=user.username)
            elif(user.job == "driver"):
                Driver.objects.create(name=user.username)
            return JsonResponse({'errcode': 1})
        except Exception as e:
            logger.warning(e)
            return JsonResponse({'errcode': -2})
