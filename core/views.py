import re
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.expressions import F, Func
from django.db.models.fields import FloatField
from miscs.models import City
from core.models import Firm, Mill
from django.shortcuts import redirect, render, resolve_url
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
    average_price = Trading.objects.filter(mill=req.mill, entry__is_deleted=False).aggregate(total=Sum('entry__quantity'), price=Sum(F('price') * F('entry__quantity') / Func(F('entry__quantity'), function='ABS')))
    average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
    raverage_price = ProductTrading.objects.filter(source__category__mill__code=req.millcode, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum(F('price'), output_field=FloatField()))
    raverage_price = round((0 if raverage_price["price"] is None else raverage_price["price"]) / (1 if raverage_price["total"] is None or raverage_price["total"] == 0 else raverage_price["total"]), 2)
    return render(req, "index.html", { "paddy_incoming": paddy_incoming, "paddy_outgoing": paddy_outgoing, "paddy_processing": paddy_processing, "paddy_trading": paddy_trading, "rice_incoming": rice_incoming, "rice_outgoing": rice_outgoing, "rice_stock": rice_stock, "rice_trading": rice_trading, "average_price": average_price, "raverage_price": raverage_price } )

@login_required
@set_mill_session
def settings(request):
    mill = Mill.objects.get(pk=request.mill.pk, is_deleted=False)
    cities = City.objects.filter(is_deleted=False)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            mill = Mill.objects.get(pk=request.POST["mill"], is_deleted=False)
            name = request.POST["name"]
            address = request.POST["address"]
            city = City.objects.get(pk=request.POST["city"], is_deleted=False)
            mill.name = name
            mill.address = address
            mill.city = city
            mill.save()
            return render(request, "settings.html", { "mill": mill, "cities": cities, "success_message": "Details updated successfully" })
        elif action == 2:
            mill = request.mill
            mill.is_deleted = True
            mill.save()
            return redirect(resolve_url('home'))
    return render(request, "settings.html", { "mill": mill, "cities": cities } )

@login_required
@set_mill_session
def firms(request):
    firms = Firm.objects.filter(mill=request.mill, is_deleted=False)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            name = request.POST["name"]
            conversion = float(request.POST["conversion"])
            username = request.POST["username"]
            password = request.POST["password"]
            Firm.objects.create(name=name, username=username, conversion=conversion, mill=request.mill, password=password)
            return render(request, "firms.html", { "firms": firms, "success_message": "Firm created successfully" })
        elif action == 2:
            firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
            name = request.POST["name"]
            conversion = float(request.POST["conversion"])
            firm.name = name
            firm.conversion = conversion
            firm.save()
            return render(request, "firms.html", { "firms": firms, "success_message": "Firm updated successfully" })
        elif action == 3:
            firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
            firm.is_deleted = True
            firm.save()
            return render(request, "firms.html", { "firms": firms, "success_message": "Firm deleted successfully" })
    return render(request, "firms.html", { "firms": firms })

@login_required
@set_mill_session
def set_firm(request: WSGIRequest):
    if request.method == "POST":
        firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
        response = redirect(resolve_url('dashboard_home', millcode=request.millcode))
        response.set_cookie("MERP_FIRM", firm.pk)
        return response

@login_required
@set_mill_session
def load_live(request):
    firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
    cache.delete('{}'.format(firm.username))
    return redirect(resolve_url('dashboard_home', millcode=request.millcode))