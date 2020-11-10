from django.urls import path, include

from . import views

urlpatterns = [
     path('<int:category>/types/', views.get_production_types, name="products-types"),
     path('incoming/', views.incoming, name="products-incoming"),
     path('book/', views.analysis, name="products-book"),
     path('stock/', views.stocks, name="products-stocks"),
     path('stock/<int:category>/max/', views.max_stock, name="max-stocks"),
     path('incoming/add/', views.incomingAdd, name="products-incoming-add"),
     path('incoming/action/<int:id>/', views.incomingAction, name="products-incoming-action"),
     path('outgoing/', views.outgoing, name="products-outgoing"),
     path('outgoing/action/<int:id>/', views.outgoingAction, name="products-outgoing-action"),
     path('configuration/', views.configuration, name="products-configuration"),
     path('configuration/action/<int:id>/', views.configurationAction, name="products-configuration-action"),
]
