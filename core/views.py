import re
from core.models import Firm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .decorators import set_mill_session
from django.db.models import Sum
from django.utils.timezone import now
from materials.models import IncomingStockEntry, OutgoingStockEntry, ProcessingSideEntry, Trading
from products.models import IncomingProductEntry, OutgoingProductEntry, ProductStock, Trading as ProductTrading
# Create your views here.
@login_required
@set_mill_session
def index(req):
    month = now().astimezone().date().month
    paddy_incoming = IncomingStockEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__quantity'))["total"]
    paddy_outgoing = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__quantity'))["total"]
    paddy_processing = ProcessingSideEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__quantity'))["total"]
    paddy_trading = Trading.objects.filter(entry__is_deleted=False, entry__bags__lte=0, mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__quantity'))["total"]
    rice_incoming = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__bags', field="entry__bags*product__quantity"))["total"]
    rice_outgoing = OutgoingProductEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__bags', field="entry__bags*product__quantity"))["total"]
    rice_stock = ProductStock.objects.filter(entry__is_deleted=False, category__mill=req.mill, entry__date__month=month).aggregate(total=Sum('entry__bags', field="entry__bags*product__quantity"))["total"]
    rice_trading = ProductTrading.objects.filter(entry__is_deleted=False, source__category__mill=req.mill, entry__bags__lte=0, entry__date__month=month).aggregate(total=Sum('entry__bags', field="entry__bags*source__quantity"))["total"]
    return render(req, "index.html", { "paddy_incoming": paddy_incoming, "paddy_outgoing": paddy_outgoing, "paddy_processing": paddy_processing, "paddy_trading": paddy_trading, "rice_incoming": rice_incoming, "rice_outgoing": rice_outgoing, "rice_stock": rice_stock, "rice_trading": rice_trading } )


@login_required
@set_mill_session
def firms(request):
    firms = Firm.objects.filter(mill=request.mill, is_deleted=False)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            name = request.POST["name"]
            agreement_no = request.POST["agreement"]
            username = request.POST["username"]
            password = request.POST["password"]
            Firm.objects.create(name=name, agreement_no=agreement_no, username=username, mill=request.mill, password=password)
            return render(request, "firms.html", { "firms": firms, "success_message": "Firm created successfully" })
        elif action == 2:
            firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
            name = request.POST["name"]
            agreement_no = request.POST["agreement"]
            firm.name = name
            firm.agreement_no = agreement_no
            firm.save()
            return render(request, "firms.html", { "firms": firms, "success_message": "Firm updated successfully" })
        elif action == 3:
            firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
            firm.is_deleted = True
            firm.save()
            return render(request, "firms.html", { "firms": firms, "success_message": "Firm deleted successfully" })
    return render(request, "firms.html", { "firms": firms })