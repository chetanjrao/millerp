from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import set_mill_session
# Create your views here.
@login_required
@set_mill_session
def index(req):
    return render(req, "starter.html")
