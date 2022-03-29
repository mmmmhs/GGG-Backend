from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name = 'login'),
    path('reg', views.reg,name = 'reg'),
	path('pois', views.pois, name = 'pois')
]