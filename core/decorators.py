import random
import string
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Mill


def set_mill_session(view_func):
    def wrapper(request, millcode, *args, **kwargs):
        mill = Mill.objects.get(code=millcode)
        request.mill = mill
        request.millcode = millcode
        return view_func(request, *args, **kwargs)
    return wrapper
