from django.core.handlers.wsgi import WSGIRequest
from millerp.settings.base import RZP_KEY
import random
import string
from django.shortcuts import redirect, render, resolve_url
from django.contrib.auth.decorators import login_required
from .models import Firm, Mill, Rice

def set_rzp_session(view_func):
    def wrapper(request, *args, **kwargs):
        request.RZP_KEY = RZP_KEY
        return view_func(request, *args, **kwargs)
    return wrapper

def set_mill_session(view_func):
    def wrapper(request: WSGIRequest, millcode, *args, **kwargs):
        mill = Mill.objects.get(code=millcode)
        firms = Firm.objects.filter(mill=mill, is_deleted=False)
        if request.COOKIES.get('rice'):
            request.rice = Rice.objects.get(is_deleted=False, pk=request.COOKIES.get('rice'))
        else:
            request.rice = Rice.objects.filter(is_deleted=False).first()
        if mill.is_deleted == True or (request.user not in mill.access.all() and not request.user.is_superuser):
            return redirect(resolve_url('home'))
        request.mill = mill
        request.rices = Rice.objects.filter(is_deleted=False)
        request.millcode = millcode
        request.firms = firms
        return view_func(request, *args, **kwargs)
    return wrapper
