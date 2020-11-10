from django.contrib import admin
from .models import Category, IncomingSource, Stock, IncomingStockEntry, OutgoingSource, OutgoingStockEntry, ProcessingSide, ProcessingSideEntry
# Register your models here.
admin.site.register(Category)
admin.site.register(IncomingSource)
admin.site.register(OutgoingSource)
admin.site.register(IncomingStockEntry)
admin.site.register(OutgoingStockEntry)
admin.site.register(ProcessingSide)
admin.site.register(ProcessingSideEntry)
admin.site.register(Stock)