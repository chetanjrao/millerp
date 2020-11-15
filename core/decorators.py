import random
import string
from django.shortcuts import redirect, render, resolve_url
from django.contrib.auth.decorators import login_required
from .models import Firm, Mill


def set_mill_session(view_func):
    def wrapper(request, millcode, *args, **kwargs):
        mill = Mill.objects.get(code=millcode)
        firms = Firm.objects.filter(mill=mill, is_deleted=False)
        if mill.is_deleted == True or request.user not in mill.access.all():
            return redirect(resolve_url('home'))
        request.mill = mill
        request.millcode = millcode
        request.firms = firms
        return view_func(request, *args, **kwargs)
    return wrapper
