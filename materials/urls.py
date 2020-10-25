from django.urls import path, include

from . import views

urlpatterns = [
    path('incoming/',  views.incoming, name="materials-incoming"),
    path('outgoing/',  views.outgoing, name="materials-outgoing"),
    path('processing/',  views.processing, name="materials-processing"),
    path('godowns/',  views.godowns, name="materials-godowns"),
]
