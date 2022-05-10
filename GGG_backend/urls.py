from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name = 'login'),
    path('reg', views.reg,name = 'reg'),
	path('product_list', views.product_list, name = 'product_list'),
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
    path('check_session_id', views.check_session_id, name='check_session_id'),
    path('driver_choose_product', views.driver_choose_product, name='driver_choose_product'),
    path('get_former', views.get_former, name='get_former'),
    path('start_pressure_test', views.start_pressure_test, name="start_pressure_test"),
    path('end_pressure_test', views.end_pressure_test, name="end_pressure_test"),
    path('get_user_info', views.get_user_info, name='get_user_info'),
    path('set_user_info', views.set_user_info, name='set_user_info'),
    path('give_score', views.give_score, name='give_score'),
    path('show_car', views.show_car, name='show_car'),
]