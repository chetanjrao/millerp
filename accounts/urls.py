from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.mlogin, name='login'),
    path('login/verify/', views.login_verify, name='login_verify'),
    re_path(r'^console/$', views.index, name='index'),
    path('payment-process/<int:bundle>/', views.payment_process, name='payment_process'),
    path('signup/', views.register, name='register'),
    re_path(r'^signup/verify/$', views.verify, name='verify'),
    path('logout/', views.mlogout, name='logout')
]