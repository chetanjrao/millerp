from django.contrib import admin
from .models import IncomingProductEntry, OutgoingProductEntry, ProductCategory, ProductionType, Stock, ProductStock, TradingSource, Trading
# Register your models here.
admin.site.register(ProductCategory)
admin.site.register(ProductionType)
admin.site.register(IncomingProductEntry)
admin.site.register(OutgoingProductEntry)
admin.site.register(Stock)
admin.site.register(ProductStock)
admin.site.register(TradingSource)
admin.site.register(Trading)