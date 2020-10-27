from django.urls import path, include

from . import views

urlpatterns = [
    path('incoming/', views.incoming, name="products-incoming"),
    path('incoming/add', views.incomingAdd, name="products-incoming-add"),
    path('incoming/action/<int:id>', views.incomingAction,
         name="products-incoming-action"),
]
