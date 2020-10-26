from django.urls import path, include

from . import views

urlpatterns = [
    path('incoming/',  views.incoming, name="materials-incoming"),
    path('incoming/add',  views.incomingAdd, name="materials-incoming-add"),
    path('incoming/action/<int:id>',  views.incomingAction,
         name="materials-incoming-action"),
    path('outgoing/',  views.outgoing, name="materials-outgoing"),
    path('outgoing/add',  views.outgoingAdd, name="materials-outgoing-add"),
    path('outgoing/action/<int:id>',  views.outgoingAction,
         name="materials-outgoing-action"),
    path('processing/',  views.processing, name="materials-processing"),
    path('godowns/',  views.godowns, name="materials-godowns"),
]
