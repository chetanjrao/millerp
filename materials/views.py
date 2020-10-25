from django.shortcuts import render

# Create your views here.


def incoming(request):
    return render(request, "materials/incoming.html")


def outgoing(request):
    return render(request, "materials/outgoing.html")


def processing(request):
    return render(request, "materials/processing.html")


def godowns(request):
    return render(request, "materials/godowns.html")
