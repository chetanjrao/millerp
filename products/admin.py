from django.contrib import admin
from .models import IncomingProductEntry, OutgoingProductEntry, ProductCategory, ProductionType
# Register your models here.
admin.site.register(ProductCategory)
admin.site.register(ProductionType)
admin.site.register(IncomingProductEntry)
admin.site.register(OutgoingProductEntry)
