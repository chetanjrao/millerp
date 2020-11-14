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