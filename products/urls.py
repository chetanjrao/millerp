from django.urls import path, include

from . import views

urlpatterns = [
     path('<int:category>/types/', views.get_production_types, name="products-types"),
     path('incoming/', views.incoming, name="products-incoming"),
     path('book/', views.analysis, name="products-book"),
     path('stock/', views.stocks, name="products-stocks"),
     path('trading/', views.trading, name="products-trading"),
     path('trading/<int:category>/sources/', views.sources, name="products-sources"),
     path('trading/<int:category>/max/', views.max_trading_stock, name="products-max-trading"),
     path('stock/<int:category>/max/', views.max_stock, name="max-stocks"),
     path('incoming/add/', views.incomingAdd, name="products-incoming-add"),
     path('incoming/action/<int:id>/', views.incomingAction, name="products-incoming-action"),
     path('outgoing/', views.outgoing, name="products-outgoing"),
     path('outgoing/action/<int:id>/', views.outgoingAction, name="products-outgoing-action"),
     path('configuration/', views.configuration, name="products-configuration"),
     path('configuration/action/<int:id>/', views.configurationAction, name="products-configuration-action"),
     path('excel/',  views.export_to_excel, name="products-excel"),
     path('sales/',  views.sales, name="products-sales"),
     path('analysis/',  views.analysis, name="analysis"),
]
