from django.shortcuts import render

# Create your views here.


def incoming(request):
    return render(request, "products/incoming.html")
