from miscs.views import get_do_view, get_print_view
from core.views import reports, set_firm, shortage
from django.urls import path, include
from accounts.views import profile
from . import views

urlpatterns = [
    path('dashboard/', views.index, name='dashboard_home'),
    path('materials/', include('materials.urls')),
    path('products/', include('products.urls')),
    path('firms/', views.firms, name='firms'),
    path('settings/', views.settings, name='settings'),
    path('profile/', profile, name='profile'),
    path('set-firm/', set_firm, name='set-firm'),
    path('reload/', views.load_live, name='reload-data'),
    path('print-do/', get_print_view, name='print-do'),
    path('do-status/', get_do_view, name='do-status'),
    path('reports/', reports, name='reports'),
    path('shortage/', shortage, name='shortage'),
]
