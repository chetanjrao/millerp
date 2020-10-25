from django.urls import path, include

from . import views

urlpatterns = [
    path('incoming/', views.incoming, name="products-incoming")
]
