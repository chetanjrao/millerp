from datetime import datetime
import re
from re import sub
from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.aggregates import Count
from django.db.models.expressions import F, Func
from django.db.models.fields import FloatField
from django.http.response import JsonResponse
from miscs.models import City, Package
from core.models import Expense, Firm, Mill, Purchase, Rice, Transporter, Truck, cmr, cmr_entry
from django.shortcuts import redirect, render, resolve_url
from django.contrib.auth.decorators import login_required
from .decorators import set_mill_session
from django.db.models import Sum
from django.utils.timezone import now
from materials.models import Category, Customer, IncomingStockEntry, OutgoingStockEntry, ProcessingSideEntry, Trading
from products.models import IncomingProductEntry, OutgoingProductEntry, ProductCategory, ProductStock, Trading as ProductTrading

@login_required
@set_mill_session
def index(req):
    entries = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=req.millcode).values(godown=F('source__name')).annotate(quantity=Func(Sum('entry__quantity'), function='ABS'))
    stocks = ProductStock.objects.filter(entry__is_deleted=False, category__mill__code=req.millcode).values(name=F('category__name')).annotate(quantity=Func(Sum(F('entry__bags') * F('product__quantity') / 100, output_field=FloatField()), function='ABS'))
    paddy_incoming = IncomingStockEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill).aggregate(total=Sum('entry__quantity'))["total"]
    paddy_outgoing = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill).aggregate(total=Sum('entry__quantity'))["total"]
    paddy_processing = ProcessingSideEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill).aggregate(total=Sum('entry__quantity'))["total"]
    rice_incoming = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill).aggregate(total=Sum('entry__bags', field="entry__bags*product__quantity"))["total"]
    rice_outgoing = OutgoingProductEntry.objects.filter(entry__is_deleted=False, category__mill=req.mill).aggregate(total=Sum('entry__bags', field="entry__bags*product__quantity"))["total"]
    rice_stock = ProductStock.objects.filter(entry__is_deleted=False, category__mill=req.mill).aggregate(total=Sum('entry__bags', field="entry__bags*product__quantity"))["total"]
    paddy_average_price = Trading.objects.filter(mill=req.mill, entry__is_deleted=False).aggregate(total=Sum('entry__quantity'), price=Sum(F('price') * F('entry__quantity')))
    paddy_average_price = round((0 if paddy_average_price["price"] is None else paddy_average_price["price"]) / (1 if paddy_average_price["total"] is None or paddy_average_price["total"] == 0 else paddy_average_price["total"]), 2)
    rice_average_price = ProductTrading.objects.filter(source__category__mill__code=req.millcode, source__category__rice=req.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))
    raverage_price = round((0 if rice_average_price["price"] is None else rice_average_price["price"]) / (1 if rice_average_price["total"] is None or rice_average_price["total"] == 0 else rice_average_price["total"]), 2)
    return render(req, "index.html", { "paddy_incoming": paddy_incoming, "paddy_outgoing": paddy_outgoing, "paddy_processing": paddy_processing, "paddy_trading": paddy_average_price, "entries": entries, "rice_incoming": rice_incoming, "rice_outgoing": rice_outgoing, "rice_stock": rice_stock, "average_price": paddy_average_price, "raverage_price": raverage_price, "stocks": stocks } )

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
            name: str = request.POST["name"]
            conversion: float = float(request.POST["conversion"])
            username: str = request.POST["username"]
            password: str = request.POST["password"]
            Firm.objects.create(name=name, username=username.upper(), conversion=conversion, mill=request.mill, password=password)
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
        response.set_cookie("MERP_FIRM", firm.pk, max_age=60*60*24*30)
        return response

@login_required
@set_mill_session
def set_rice(request: WSGIRequest):
    if request.method == "POST":
        next_url = request.POST["next"]
        rice = Rice.objects.get(pk=request.POST["rice"], is_deleted=False)
        response = redirect(next_url)
        response.set_cookie("rice", rice.pk, max_age=60*60*24*30)
        return response

@login_required
@set_mill_session
def load_live(request):
    firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
    cache.delete('{}'.format(firm.username))
    cache.delete('{}2020'.format(firm.username))
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
    rices = Rice.objects.filter(is_deleted=False)
    materials = Category.objects.filter(mill=request.mill, is_deleted=False)
    products = ProductCategory.objects.filter(is_biproduct=False, mill=request.mill, is_deleted=False)
    return render(request, "reports.html", { "rices": rices, "materials": materials, "products": products })

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
def truck_bill(request):
    truck = Truck.objects.get(pk=request.GET["truck"], transporter__mill=request.mill)
    from_date = request.GET.get('from', now().astimezone().strftime("%Y-%m-%d"))
    to_date = request.GET.get('to', now().astimezone().strftime("%Y-%m-%d"))
    logs = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, truck=truck, cmr__cmr_date__lte=to_date, is_deleted=False)
    total = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, truck=truck, cmr__cmr_date__lte=to_date, is_deleted=False).aggregate(total=Sum('price'))["total"]
    return render(request, "vbill.html", { "logs": logs, "total": total, "from": datetime.strptime(from_date, "%Y-%m-%d"), "to": datetime.strptime(to_date, "%Y-%m-%d"), "truck": truck })


@login_required
@set_mill_session
def type_bill(request):
    entry_type = int(request.GET["type"])
    from_date = request.GET.get('from', now().astimezone().strftime("%Y-%m-%d"))
    to_date = request.GET.get('to', now().astimezone().strftime("%Y-%m-%d"))
    entries = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, cmr__mill=request.mill, entry_type=entry_type, cmr__cmr_date__lte=to_date, is_deleted=False).values('cmr', name=F('cmr__cmr_no')).annotate(Count('cmr')).values('name', 'cmr')
    total = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, cmr__mill=request.mill, entry_type=entry_type, cmr__cmr_date__lte=to_date, is_deleted=False).aggregate(total=Sum('price'))["total"]
    logs = []
    max_trucks = 0
    diff = cmr_entry.objects.filter(entry_type=entry_type, cmr__cmr_date__gte=from_date, cmr__cmr_date__lte=to_date, is_deleted=False).values('cmr__pk').annotate(count=Count('cmr__pk')).values('count').order_by('-count')
    diff = diff[0]["count"] if len(diff) > 0 else 0
    for entry in entries:
        current = {}
        current["info"] = cmr.objects.get(pk=entry["cmr"], mill=request.mill, is_deleted=False)
        subs = cmr_entry.objects.filter(cmr__pk=entry["cmr"], entry_type=entry_type, cmr__cmr_date__gte=from_date, cmr__cmr_date__lte=to_date, is_deleted=False)
        current.setdefault("trucks", []).append(subs)
        if len(subs) > max_trucks:
            max_trucks = len(subs)
        current['diff'] = range(diff - len(subs))
        current["total"] = subs.aggregate(total=Sum('price'))["total"]
        logs.append(current)
    entry_type = "FCI" if entry_type == 1 else "NAN"
    return render(request, "ebill.html", { "logs": logs, "max_trucks": range(max_trucks), "type": entry_type, "total": total, "from": datetime.strptime(from_date, "%Y-%m-%d"), "to": datetime.strptime(to_date, "%Y-%m-%d") })

@login_required
@set_mill_session
def bills(request):
    transporters = Transporter.objects.filter(mill=request.mill, is_deleted=False)
    trucks = Truck.objects.filter(transporter__in=transporters, is_deleted=False)
    return render(request, "bills.html", { "transporters": transporters, "trucks": trucks })

@login_required
@set_mill_session
def transporter_bill(request):
    from_date = request.GET.get('from', now().astimezone().strftime("%Y-%m-%d"))
    to_date = request.GET.get('to', now().astimezone().strftime("%Y-%m-%d"))
    transporter = Transporter.objects.get(pk=request.GET["transporter"], mill=request.mill)
    entries = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, truck__transporter=transporter, cmr__mill=request.mill, cmr__cmr_date__lte=to_date, is_deleted=False).values('cmr', name=F('cmr__cmr_no')).annotate(Count('cmr')).values('name', 'cmr')
    total = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, cmr__mill=request.mill, cmr__cmr_date__lte=to_date, is_deleted=False).aggregate(total=Sum('price'))["total"]
    logs = []
    max_trucks = 0
    diff = cmr_entry.objects.filter(cmr__cmr_date__gte=from_date, cmr__mill=request.mill, cmr__cmr_date__lte=to_date, is_deleted=False).values('cmr__pk').annotate(count=Count('cmr__pk')).values('count').order_by('-count')
    diff = diff[0]["count"] if len(diff) > 0 else 0
    for entry in entries:
        current = {}
        current["info"] = cmr.objects.get(pk=entry["cmr"], mill=request.mill, is_deleted=False)
        subs = cmr_entry.objects.filter(cmr__pk=entry["cmr"], cmr__mill=request.mill, cmr__cmr_date__gte=from_date, cmr__cmr_date__lte=to_date, is_deleted=False)
        current.setdefault("trucks", []).append(subs)
        if len(subs) > max_trucks:
            max_trucks = len(subs)
        current['diff'] = range(diff - len(subs))
        current["total"] = subs.aggregate(total=Sum('price'))["total"]
        logs.append(current)
    return render(request, "obill.html", { "logs": logs, "transporter": transporter, "max_trucks": range(max_trucks), "total": total, "from": datetime.strptime(from_date, "%Y-%m-%d"), "to": datetime.strptime(to_date, "%Y-%m-%d") })

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


@login_required
@set_mill_session
def customers(request):
    customers = Customer.objects.filter(is_deleted=False, mill=request.mill)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            name = request.POST["name"]
            Customer.objects.create(name=name, mill=request.mill, created_by=request.user)
            customers = Customer.objects.filter(is_deleted=False, mill=request.mill)
            return render(request, "customers.html", {'customers': customers, "success_message": "Customer created successfully"})
        elif action == 2:
            obj = Customer.objects.get(id=request.POST["customer"])
            name = request.POST["name"]
            obj.name = name
            obj.save()
            customers = Customer.objects.filter(is_deleted=False, mill=request.mill)
            return render(request, "customers.html", {'customers': customers, "success_message": "Customer updated successfully"})
        elif action == 3:
            obj = Customer.objects.get(id=request.POST["customer"])
            obj.is_deleted = True
            obj.save()
            customers = Customer.objects.filter(is_deleted=False, mill=request.mill)
            return render(request, "customers.html", { 'customers': customers, "error_message": "Customer deleted successfully"})
    return render(request, "customers.html", { "customers": customers })


@login_required
@set_mill_session
def expenses(request):
    expenses = Expense.objects.filter(mill=request.mill, is_deleted=False)
    types = Expense.objects.filter(mill=request.mill, is_deleted=False).values(type=F('bill_type')).annotate(amount=Sum(F('taxable_amount') + (F('tax') * F('taxable_amount') / 100) + F('miscs'), output_field=FloatField()))
    total = expenses.values('name').annotate(amount=Sum(F('taxable_amount') + (F('tax') * F('taxable_amount') / 100) + F('miscs'), output_field=FloatField()))
    summary = total.aggregate(total=Sum('amount'))["total"]
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            name: str = request.POST["name"].lower().strip().capitalize()
            bill_type: str = request.POST["type"].lower().strip().capitalize()
            amount = float(request.POST["taxable_amount"])
            tax = float(request.POST.get("tax", "0"))
            date = datetime.strptime(request.POST["date"], "%d-%m-%Y")
            miscs = float(request.POST.get("miscs", "0"))
            remarks = request.POST.get("remarks")
            Expense.objects.create(name=name, bill_type=bill_type, taxable_amount=amount, date=date, remarks=remarks, tax=tax, miscs=miscs, created_by=request.user, mill=request.mill)
            expenses = Expense.objects.filter(mill=request.mill, is_deleted=False)
            total = expenses.values('name').annotate(amount=Sum(F('taxable_amount') + (F('tax') * F('taxable_amount') / 100) + F('miscs'), output_field=FloatField()))
            summary = total.aggregate(total=Sum('amount'))["total"]
            return render(request, "expenses.html", { "expenses": expenses, "total": total, "summary": summary, "success_message": "Expense created sucessfully" })
        if action == 2:
            name: str = request.POST["name"].lower().strip().capitalize()
            bill_type: str = request.POST["type"].lower().strip().capitalize()
            amount = float(request.POST["taxable_amount"])
            tax = float(request.POST.get("tax", "0"))
            date = datetime.strptime(request.POST["date"], "%d-%m-%Y")
            miscs = float(request.POST.get("miscs", "0"))
            remarks = request.POST.get("remarks")
            expense = Expense.objects.get(pk=request.POST["expense"])
            expense.name = request.POST["name"].lower().strip().capitalize()
            expense.tax = tax
            expense.bill_type = bill_type
            expense.date = date
            expense.miscs = miscs
            expense.taxable_amount = amount
            expense.remarks = remarks
            expense.save()
            expenses = Expense.objects.filter(mill=request.mill, is_deleted=False)
            total = expenses.values('name').annotate(amount=Sum(F('taxable_amount') + (F('tax') * F('taxable_amount') / 100) + F('miscs'), output_field=FloatField()))
            summary = total.aggregate(total=Sum('amount'))["total"]
            return render(request, "expenses.html", { "expenses": expenses, "summary": summary, "total": total, "success_message": "Expense updated sucessfully" })
        if action == 3:
            expense = Expense.objects.get(pk=request.POST["expense"])
            expense.is_deleted = True
            expense.save()
            expenses = Expense.objects.filter(mill=request.mill, is_deleted=False)
            total = expenses.values('name').annotate(amount=Sum(F('taxable_amount') + (F('tax') * F('taxable_amount') / 100) + F('miscs'), output_field=FloatField()))
            summary = total.aggregate(total=Sum('amount'))["total"]
            return render(request, "expenses.html", { "expenses": expenses, "total": total, "summary": summary, "success_message": "Expense deleted sucessfully" })
    return render(request, "expenses.html", { "expenses": expenses, "types": types, "summary": summary, "total": total })


@login_required
@set_mill_session
def print_expense(request, expense):
    expense = Expense.objects.get(pk=expense, mill=request.mill, is_deleted=False)
    return render(request, "expense_bill.html", { "expense": expense } )


@login_required
@set_mill_session
def trips(request):
    
    return render(request, "trips.html")
