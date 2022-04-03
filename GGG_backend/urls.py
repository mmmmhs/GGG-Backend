from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name = 'login'),
    path('reg', views.reg,name = 'reg'),
	path('pois', views.pois, name = 'pois'),
    path('passenger_order', views.passenger_order, name='passenger_order'),
    path('driver_order', views.driver_order, name='driver_order'),
    path('get_order_info',views.get_order_info,name = 'get_order_info')
]