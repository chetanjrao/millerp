from datetime import datetime
import re
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.expressions import F, Func
from django.db.models.fields import FloatField
from django.http.response import JsonResponse
from miscs.models import City, Package
from core.models import Firm, Mill, Purchase, Transporter, Truck, cmr, cmr_entry
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
    entries = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=req.millcode).values(godown=F('source__name')).annotate(quantity=Func(Sum('entry__quantity'), function='ABS'))
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
    return render(req, "index.html", { "paddy_incoming": paddy_incoming, "paddy_outgoing": paddy_outgoing, "paddy_processing": paddy_processing, "paddy_trading": paddy_trading, "entries": entries, "rice_incoming": rice_incoming, "rice_outgoing": rice_outgoing, "rice_stock": rice_stock, "rice_trading": rice_trading, "average_price": average_price, "raverage_price": raverage_price } )

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
    purchase = Purchase.objects.get(owner__user=request.user)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            if len(firms) >= (purchase.bundle.mills * 3):
                return render(request, "firms.html", { "firms": firms, "purchase": purchase, "error_message": "Firm limit exceeded" })
            name = request.POST["name"]
            conversion = float(request.POST["conversion"])
            username = request.POST["username"]
            password = request.POST["password"]
            Firm.objects.create(name=name, username=username, conversion=conversion, mill=request.mill, password=password)
            return render(request, "firms.html", { "firms": firms, "purchase": purchase, "success_message": "Firm created successfully" })
        elif action == 2:
            firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
            name = request.POST["name"]
            conversion = float(request.POST["conversion"])
            firm.name = name
            firm.conversion = conversion
            firm.save()
            return render(request, "firms.html", { "firms": firms, "purchase": purchase, "success_message": "Firm updated successfully" })
        elif action == 3:
            firm = Firm.objects.get(pk=request.POST["firm"], is_deleted=False, mill=request.mill)
            firm.is_deleted = True
            firm.save()
            return render(request, "firms.html", { "firms": firms, "purchase": purchase, "success_message": "Firm deleted successfully" })
    return render(request, "firms.html", { "firms": firms, "purchase": purchase })

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

@login_required
@set_mill_session
def shortage(request):
    paddy_outgoing = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill=request.mill).aggregate(total=Sum('entry__quantity'))["total"]
    rice_stock = ProductStock.objects.filter(entry__is_deleted=False, category__mill=request.mill).aggregate(total=Sum(F("entry__bags") * F("product__quantity") / 100, output_field=FloatField()))["total"]
    return render(request, "shortage.html", { "paddy_outgoing": paddy_outgoing, "rice_stock": rice_stock })

@login_required
@set_mill_session
def reports(request):
    return render(request, "reports.html")


@login_required
@set_mill_session
def transport(request):
    transporters = Transporter.objects.filter(is_deleted=False, mill=request.mill)
    trucks = Truck.objects.filter(is_deleted=False, transporter__in=transporters)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            name = request.POST["name"]
            mobile = request.POST["mobile"]
            Transporter.objects.create(name=name, mobile=mobile, mill=request.mill)
            return render(request, "transport.html", { "transporters": transporters, "trucks": trucks, "success_message": "Transporter added successfully" })
        elif action == 2:
            name = request.POST["name"]
            mobile = request.POST["mobile"]
            transporter = Transporter.objects.get(pk=request.POST["transporter"])
            transporter.name = name
            transporter.mobile = mobile
            transporter.save()
            return render(request, "transport.html", { "transporters": transporters, "trucks": trucks, "success_message": "Transporter updated successfully" })
        elif action == 3:
            transporter = Transporter.objects.get(pk=request.POST["transporter"])
            transporter.is_deleted = True
            transporter.save()
            return render(request, "transport.html", { "transporters": transporters, "trucks": trucks, "success_message": "Transporter deleted successfully" })
        if action == 4:
            number = request.POST["number"]
            transporter = Transporter.objects.get(pk=request.POST["transporter"])
            Truck.objects.create(number=number, transporter=transporter)
            return render(request, "transport.html", { "transporters": transporters, "trucks": trucks, "success_message": "Truck added successfully" })
        elif action == 5:
            number = request.POST["number"]
            transporter = Transporter.objects.get(pk=request.POST["transporter"])
            truck = Truck.objects.get(pk=request.POST["truck"])
            truck.number = number
            truck.transporter = transporter
            truck.save()
            return render(request, "transport.html", { "transporters": transporters, "trucks": trucks, "success_message": "Truck updated successfully" })
        elif action == 6:
            truck = Truck.objects.get(pk=request.POST["truck"])
            truck.is_deleted = True
            truck.save()
            return render(request, "transport.html", { "transporters": transporters, "trucks": trucks, "success_message": "Truck deleted successfully" })
    return render(request, "transport.html", { "transporters": transporters, "trucks": trucks })

@login_required
@set_mill_session
def trucks_api(request, transporter: int):
    transporter = Transporter.objects.get(pk=transporter, mill=request.mill, is_deleted=False)
    trucks = Truck.objects.filter(transporter=transporter, is_deleted=False)
    return JsonResponse([{
            "id": truck.pk,
            "text": truck.number
        } for truck in trucks], safe=False)


@login_required
@set_mill_session
def truck_entry(request):
    cmr_number = request.GET["cmr_no"]
    cmr_date = request.GET["cmr_date"]
    center = request.GET["center"]
    rice = float(request.GET["rice"])
    lot = int(request.GET["lot"])
    bora = request.GET["bora"]
    commodity = request.GET["commodity"]
    transporters = Transporter.objects.filter(mill=request.mill, is_deleted=False)
    entries = cmr_entry.objects.filter(cmr__cmr_no=cmr_number, is_deleted=False)
    if request.method == "POST":
        entries = cmr_entry.objects.filter(cmr__cmr_no=cmr_number, is_deleted=False)
        entries.update(is_deleted=True)
        counter = int(request.POST["counter"])
        try:
            c_cmr = cmr.objects.get(cmr_no=cmr_number)
        except cmr.DoesNotExist:
            c_cmr = cmr.objects.create(cmr_no=cmr_number, cmr_date=datetime.strptime(cmr_date, "%d/%m/%Y"), center=center, rice=rice, lot_no=lot, bora=bora, commodity=commodity, mill=request.mill)
        for i in range(counter):
            transporter = Transporter.objects.get(pk=request.POST['trucks[{}][transporter]'.format(i)], mill=request.mill)
            try:
                truck = Truck.objects.get(pk=request.POST['trucks[{}][truck]'.format(i)])
            except:
                truck = Truck.objects.create(number=request.POST['trucks[{}][truck]'.format(i)], transporter=transporter)
            entry_type = request.POST['trucks[{}][type]'.format(i)]
            bags = request.POST['trucks[{}][bags]'.format(i)]
            price = float(request.POST['trucks[{}][price]'.format(i)])
            cmr_entry.objects.create(cmr=c_cmr, entry_type=entry_type, truck=truck, price=price, bags=bags)
        return render(request, "entry.html", { "transporters": transporters, "entries": entries, "success_message": "Entry created successfully" })
    return render(request, "entry.html", { "transporters": transporters, "entries": entries })

@login_required
@set_mill_session
def entry_logs(request):
    transporters = Transporter.objects.filter(mill=request.mill, is_deleted=False)
    trucks = Truck.objects.filter(pk__in=transporters, is_deleted=False)
    entries = cmr_entry.objects.filter(cmr__mill=request.mill, is_deleted=False)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            entry = cmr_entry.objects.get(pk=request.POST["entry"])
            truck = Truck.objects.get(pk=request.POST["truck"])
            entry_type = int(request.POST["type"])
            bags = float(request.POST["bags"])
            price = float(request.POST["price"])
            entry.entry_type = entry_type
            entry.truck = truck
            entry.bags = bags
            entry.price = price
            entry.save()
            return render(request, "log.html", { "entries": entries, "transporters": transporters, "trucks": trucks, "success_message": "Entry updated successfully" })
        elif action == 2:
            entry = cmr_entry.objects.get(pk=request.POST["entry"])
            entry.is_deleted = True
            entry.save()
            return render(request, "log.html", { "entries": entries, "transporters": transporters, "trucks": trucks, "success_message": "Entry deleted successfully" })
    return render(request, "log.html", { "entries": entries, "transporters": transporters, "trucks": trucks })