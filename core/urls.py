from miscs.views import get_cmr_status, get_cmr_view, get_do_view, get_print_view
from core.views import entry_logs, reports, set_firm, set_rice, shortage, transport, transporter_bill, truck_bill, truck_entry, trucks_api
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
    path('switch-rice/', set_rice, name='switch-rice'),
    path('reload/', views.load_live, name='reload-data'),
    path('print-do/', get_print_view, name='print-do'),
    path('do-status/', get_do_view, name='do-status'),
    path('reports/', reports, name='reports'),
    path('shortage/', shortage, name='shortage'),
    path('transports/', transport, name='transport'),
    path('transports/api/<int:transporter>/', trucks_api, name='trucks_api'),
    path('cmr/status/api/', get_cmr_status, name='cmr_status_api'),
    path('cmr-status/', get_cmr_view, name='cmr_status'),
    path('cmr/entry/', truck_entry, name='cmr_entry'),
    path('log/', entry_logs, name='entry_logs'),
    path('log/print/trucks/<int:truck>/', truck_bill, name='truck_bill'),
    path('log/print/transporters/<int:transporter>/', transporter_bill, name='transporter_bill'),
]
