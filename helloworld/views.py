
from ast import Return
from email.policy import default
from logging import exception
from django.forms import ValidationError
from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse, JsonResponse
import requests
from helloworld.models import Driver, Passenger, SessionId
import secoder.settings
from cryptography.fernet import Fernet

def index(request):
    return HttpResponse("Hello world.")

def get_3rd_session(session_key, openId, job):
    key = Fernet.generate_key()
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(session_key.encode('utf-8'))
    SessionId.objects.create(Id = encrypted_data, key = key, username = openId, job = job)
    return encrypted_data

def login(request):
    if(request.method =='GET'):
        code = request.GET.get('code',default = '')
        job = request.GET.get('job',default = '')
        response = requests.get("https://api.weixin.qq.com/sns/jscode2session?appid="+secoder.settings.APPID+"&secret="+secoder.settings.APPSECRET+"&js_code="+code+"&grant_type=authorization_code")
        data = response.json()
        try:
            openID = data['openId']
            sessionID = get_3rd_session(data['session_key'], openID, job)
            errorcode = data['errorcode']
            if job =='passenger':
                user = Passenger.objects.filter(name = openID).first()
                if not user and errorcode == 0:
                    errorcode = -10
            if job =='driver':
                user = Driver.objects.filter(name = openID).first()
                if not user and errorcode == 0:
                    errorcode = -10
            return JsonResponse({'errorcode':errorcode,'sess':sessionID})
        except Exception:
            return HttpResponse("Invalid", status=405)

def reg(request):
    if(request.method =='GET'):
        try:
            sess = request.GET.get('sess',default = '')
            user = SessionId.objects.filter(Id = sess).first()
            if(user.job == "passenger"):
                Passenger.objects.create(name = user.username)
            elif(user.job == "driver"):
                Driver.objects.create(name = user.username)
            return JsonResponse({'errorcode':1})
        except Exception:
            return JsonResponse({'errorcode':-2})
    
    