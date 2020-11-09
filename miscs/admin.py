from django.contrib import admin
from .models import Package, Addon, Bundle, City, State, Country

# Register your models here.
admin.site.register(Package)
admin.site.register(Addon)
admin.site.register(Bundle)
admin.site.register(City)
admin.site.register(State)
admin.site.register(Country)