from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name = 'login'),
    path('reg', views.reg,name = 'reg'),
	path('pois', views.pois, name = 'pois'),
    path('passenger_order', views.passenger_order, name='passenger_order'),
    path('driver_order', views.driver_order, name='driver_order'),
    path('get_order_info', views.get_order_info, name='get_order_info'),
    path('driver_get_order', views.driver_get_order, name='driver_get_order'),
    path('driver_confirm_aboard', views.driver_confirm_aboard, name='driver_confirm_aboard'),
    path('driver_confirm_arrive', views.driver_confirm_arrive, name='driver_confirm_arrive'),
    path('passenger_cancel', views.passenger_cancel, name='passenger_cancel'),
    path('driver_cancel', views.driver_cancel, name='driver_cancel'),
    path('get_history_order_info',views.get_history_order_info,name='get_history_order_info'),
    path('passenger_pay',views.passenger_pay,name='passenger_pay'),
    path('get_order_money',views.get_order_money,name='get_order_money'),
]