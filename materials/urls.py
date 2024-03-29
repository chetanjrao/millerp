from miscs.views import get_do_stats, get_guarantee, get_print, get_print_url, guarantee
from materials.views import get_sources, trading
from django.urls import path, include
from . import views

urlpatterns = [
    path('incoming/',  views.incoming, name="materials-incoming"),
    path('excel/',  views.export_to_excel, name="materials-excel"),
    path('analysis/',  views.analysis, name="materials-analysis"),
    path('incoming/add/',  views.incomingAdd, name="materials-incoming-add"),
    path('sources/', views.get_sources, name='materials_sources'),
    path('incoming/action/<int:id>/',  views.incomingAction, name="materials-incoming-action"),
    path('outgoing/',  views.outgoing, name="materials-outgoing"),
    path('outgoing/data/',  views.outgoing_data, name="materials-outgoing-data"),
    path('outgoing/add/',  views.outgoingAdd, name="materials-outgoing-add"),
    path('outgoing/action/<int:id>/',  views.outgoingAction, name="materials-outgoing-action"),
    path('sales/',  views.sales, name="materials-sales"),
    path('processing/',  views.processing, name="materials-processing"),
    path('processing/add/',  views.processingAdd, name="materials-processing-add"),
    path('godowns/',  views.godowns, name="materials-godowns"),
    path('godowns/action/<int:id>/',  views.godownsAction, name="materials-godowns-action"),
    path('configuration/', views.configuration, name="materials-configuration"),
    path('stocks/', views.stock, name="materials-stock"),
    path('trading/', views.trading, name='materials-trading'),
    path('sales/<int:sale>/', views.bill, name='materials-bill'),
    path('trading/<int:category>/max/', views.get_max_quantity, name='materials-max'),
    path('configuration/action/<int:id>/', views.configurationAction, name="materials-configuration-action"),
    path('stock/<int:category>/check/', views.get_stock_available, name='stock_check'),
    path('guarantee/', guarantee, name='guarantee'),
    path('live/api/', get_guarantee, name='guarantee-api'),
    path('agreement/api/', get_print_url, name='print-api'),
    path('do/api/', get_do_stats, name='do-api')
]
