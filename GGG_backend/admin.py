from django.contrib import admin
from GGG_backend.models import Passenger, Driver, SessionId, Order, Product, Setting, Area
# Register your models here.


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('/static/map/map.css',),
        }
        js = (
            'https://map.qq.com/api/gljs?v=1.exp&key=U3ZBZ-Q253X-GL44Q-7RD64-43RR3-Q2BLM&libraries=tools',
            '/static/map/map.js'
        )


admin.site.register([Passenger, Driver, SessionId,
                    Order, Product, Setting])
