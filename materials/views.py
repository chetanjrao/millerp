import io
from django.db.models.expressions import Case, F, When
from django.db.models.fields import IntegerField
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.views import csrf_exempt
from django.contrib.auth.decorators import login_required
from xlsxwriter import workbook
from core.decorators import set_mill_session
from core.models import Mill
from .models import IncomingStockEntry, Category, IncomingSource, OutgoingStockEntry, OutgoingSource, ProcessingSide, ProcessingSideEntry, Stock, Trading
from datetime import datetime, timedelta
from django.utils.timezone import datetime
from django.db.models import Sum
from django.db.models.functions import Coalesce
import xlsxwriter
import calendar

@login_required
@set_mill_session
def incoming(request):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode)
    sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories})

@login_required
@set_mill_session
def get_sources(request: WSGIRequest):
    mill = Mill.objects.get(code=request.millcode)
    categories = [ {
        "id": source.pk,
        "text": source.name,
        "is_trading": source.include_trading
    } for source in IncomingSource.objects.filter(mill=mill, is_deleted=False)]
    return JsonResponse(categories, safe=False)


@login_required
@set_mill_session
def incomingAdd(request):
    mill = Mill.objects.get(code=request.millcode)
    sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    godowns = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    sides = ProcessingSide.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        date = request.POST.get('date', datetime.now().strftime("%d-%m-%Y"))
        date = datetime.strptime(date, "%d-%m-%Y")
        category = Category.objects.get(id=int(request.POST.get('incoming_category')))
        source = IncomingSource.objects.get(id=request.POST.get("incoming_source"))
        try:
            in_bags = int(request.POST['incoming_bags'])
            in_weight = float(request.POST['incoming_weight'])
            price = float(request.POST.get("price"))
            average_weight = in_weight * 100 / in_bags
            remarks = "Entry of {} - {} bags ({}qtl) from {}".format(category.name, in_bags, in_weight, source.name)
            entry = Stock.objects.create(bags=in_bags, quantity=in_weight, remarks=remarks, date=date)
            IncomingStockEntry.objects.create(source=source, category=category, entry=entry, created_by=request.user)
            if price is not None and price > 0:
                Trading.objects.create(entry=entry, mill=mill, price=price, created_by=request.user)
            pr_bags = float(request.POST["processing_bags"])
            pr_side = ProcessingSide.objects.get(pk=request.POST["processing_side"], is_deleted=False)
            remarks = "Sent {} bags ({} avg. weight) for processing into {}".format(pr_bags, average_weight, pr_side.name)
            entry = Stock.objects.create(bags=0 - pr_bags, quantity=0 - round((pr_bags * average_weight / 100), 2), remarks=remarks, date=date)
            ProcessingSideEntry.objects.create(source=pr_side, category=category, entry=entry, created_by=request.user)
            counter = int(request.POST.get("counter", 0))
            for i in range(counter):
                godown = OutgoingSource.objects.get(pk=request.POST["outgoing[{}][godown]".format(i)], is_deleted=False)
                bags = int(request.POST["outgoing[{}][bags]".format(i)])
                remarks = "Sent {} bags ({} avg. weight) to {}".format(pr_bags, average_weight, godown.name)
                entry = Stock.objects.create(bags=0 - bags, quantity=0 - round((bags * average_weight / 100), 2), date=date)
                OutgoingStockEntry.objects.create(entry=entry, source=godown, category=category, created_by=request.user)
        except ValueError:
            return render(request, "materials/incoming-add.html", {"sources": sources, "categories": categories, "error_message": "Number of bags and average weight must be a valid number"})
        return render(request, "materials/incoming-add.html", {"sources": sources, "categories": categories, "godowns": godowns, "sides": sides, "success_message": "Incoming entry added successfully"})
    return render(request, "materials/incoming-add.html", {"sources": sources, "categories": categories, "godowns": godowns, "sides": sides})

@login_required
@set_mill_session
def analysis(request):
    entries = Stock.objects.filter(is_deleted=False, category__mill__code=request.millcode).order_by('-date')
    return render(request, "materials/reports.html", { "entries": entries })

@login_required
@set_mill_session
def incomingAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode)
    sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    if request.method == 'POST':
        id = int(id)
        obj = IncomingStockEntry.objects.get(id=id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            try:
                date = request.POST.get('date_in', datetime.now().strftime("%d-%m-%Y"))
                date = datetime.strptime(date, "%d-%m-%Y")
                obj.entry.date = date
                obj.source = IncomingSource.objects.get(id=int(request.POST.get('source_id')))
                obj.category = Category.objects.get(id=int(request.POST.get('category_id')))
                obj.entry.bags = float(request.POST.get('bags'))
                obj.entry.quantity = float(request.POST.get('total_weight'))
                obj.entry.save()
                obj.save()
            except ValueError:
                return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories, "error_message": "PLease enter valid entries to update"})
            obj.save()
            return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories, "success_message": "Entry updated successfully"})
        elif action == 2:
            obj.entry.is_deleted = True
            obj.entry.save()
            obj.save()
            return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories,
                                                               "error_message": "Entry deleted successfully"})
    return redirect('materials-incoming', millcode=request.millcode)


@login_required
@set_mill_session
def outgoing(request):
    mill = Mill.objects.get(code=request.millcode)
    stocks = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode, entry__bags__lte=0).order_by('-created_at')
    sources = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    entries = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode).values(type=F('category__name'), godown=F('source__name'),type_pk=F('category__pk'), godown_pk=F('source__pk')).annotate(max=Sum('entry__bags'), max_quantity=Sum('entry__quantity'))
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    sides = ProcessingSide.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        bags = int(request.POST["bags"])
        average_weight = float(request.POST["average_weight"])
        quantity = round(bags * average_weight / 100, 2)
        category = Category.objects.get(pk=request.POST["category"])
        source = OutgoingSource.objects.get(pk=request.POST["source"])
        date = request.POST["date"]
        date = datetime.strptime(date, "%d-%m-%Y")
        side = ProcessingSide.objects.get(pk=request.POST["processing_side"])
        entry = Stock.objects.create(bags=bags, quantity=quantity, remarks='{} Bags removed from godown {}'.format(bags, source.name), date=date)
        OutgoingStockEntry.objects.create(entry=entry, category=category, source=source, created_by=request.user)
        entry = Stock.objects.create(bags=0 - bags, quantity=0 - quantity, remarks='{} Bags sent to processing into {}'.format(bags, side.name), date=date)
        ProcessingSideEntry.objects.create(entry=entry, category=category, source=side, created_by=request.user)
    return render(request, "materials/outgoing.html", {"stocks": stocks, "sides": sides, "sources": sources, "categories": categories, "entries": entries})


# To be completed
@login_required
@set_mill_session
def outgoingAdd(request):
    mill = Mill.objects.get(code=request.millcode)
    sources = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    return render(request, "materials/outgoing-add.html", {"sources": sources, "categories": categories})

# To be completed
@login_required
@set_mill_session
def outgoingAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    stocks = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode).order_by('-entry__date')
    sources = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    entries = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode, entry__bags__lte=0).values(name=F('source__name')).annotate(max=Sum('entry__bags'))
    sides = ProcessingSide.objects.filter(is_deleted=False, mill=mill)
    if request.method == 'POST':
        id = int(id)
        obj: OutgoingStockEntry = OutgoingStockEntry.objects.get(id=id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            bags = int(request.POST["bags"])
            quantity = float(request.POST["quantity"])
            source = OutgoingSource.objects.get(pk=request.POST["source"])
            category = Category.objects.get(pk=request.POST["category"])
            obj.entry.bags =  0 -bags
            obj.entry.quantity = 0 - quantity
            obj.category = category
            obj.entry.save()
            obj.source = source
            obj.save()
            entries = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode, entry__bags__lte=0).values(name=F('source__name')).annotate(max=Sum('entry__bags'))
            return render(request, "materials/outgoing.html", {"stocks": stocks, "sides": sides, "sources": sources, "categories": categories, "success_message": "Entry updated successfully", "entries": entries})
        if action == 4:
            bags = int(request.POST["bags"])
            date = request.POST["date"]
            date = datetime.strptime(date, "%d-%m-%Y")
            side = ProcessingSide.objects.get(pk=request.POST["processing_side"])
            entry = Stock.objects.create(bags=bags, category=obj.category, source=obj.source, quantity=obj.entry.average_weight * bags / 100, remarks='{} Bags removed from godown {}'.format(bags, obj.source.name), date=date)
            OutgoingStockEntry.objects.create(entry=entry, created_by=request.user)
            entry = Stock.objects.create(bags=0 - bags, category=obj.category, source=obj.source, quantity=0 - obj.entry.average_weight * bags / 100, remarks='{} Bags sent to processing into {}'.format(bags, side.name), date=date)
            ProcessingSideEntry.objects.create(entry=entry, source=side, created_by=request.user)
            entries = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode, entry__bags__lte=0).values(name=F('source__name')).annotate(max=Sum('entry__bags'))
            return render(request, "materials/outgoing.html", {"stocks": stocks, "sides": sides, "sources": sources, "categories": categories, "success_message": "Stock sent to processing successfully", "entries": entries})
        elif action == 2:
            obj.entry.is_deleted = True
            obj.entry.save()
            obj.save()
            return render(request, "materials/outgoing.html", {"stocks": stocks, "sides": sides, "sources": sources, "categories": categories, "error_message": "Entry deleted successfully", "entries": entries})
    return redirect('materials-outgoing', millcode=request.millcode)

@csrf_exempt
@login_required
@set_mill_session
def get_stock_available(request: WSGIRequest, category: int):
    Category.objects.get(pk=category, mill__code=request.millcode)
    stock_purchased = IncomingStockEntry.objects.raw("SELECT id, SUM(bags) as stock FROM ( SELECT id, bags FROM materials_incomingstockentry i WHERE category_id={} GROUP BY id UNION SELECT stock_id, 0 - SUM(o.bags) bags FROM materials_incomingstockentry i INNER JOIN materials_outgoingstockentry o ON i.id = o.stock_id GROUP BY o.stock_id UNION SELECT stock_id, 0 - SUM(p.bags) bags FROM materials_incomingstockentry i INNER JOIN materials_processingsideentry p ON i.id = p.stock_id GROUP BY p.stock_id) as bags GROUP by id".format(category))
    stocks = [{
        "id": stock.pk,
        "stock": stock.stock,
        "text": "Incoming Stock - {}".format(stock.date.strftime("%d/%m/%Y"))
    } for stock in stock_purchased]
    return JsonResponse(stocks, safe=False)

@login_required
@set_mill_session
def outgoingAdd(request):
    categories = Category.objects.filter(mill__code=request.millcode)
    godowns = OutgoingSource.objects.filter(mill__code=request.millcode)
    if request.method == "POST":
        stock = IncomingStockEntry.objects.get(pk=request.POST["stock"], category__mill__code=request.millcode)
        godown = OutgoingSource.objects.get(pk=request.POST["godown"], mill__code=request.millcode)
        bags = int(request.POST["quantity"])
        OutgoingStockEntry.objects.create(stock=stock, source=godown, bags=bags, created_by=request.user)
        return render(request, "materials/outgoing-add.html", { "categories": categories, "godowns": godowns, "success_message": "Outgoing Stock entered successfully" } )
    return render(request, "materials/outgoing-add.html", { "categories": categories, "godowns": godowns } )

@login_required
@set_mill_session
def processingAdd(request):
    categories = Category.objects.filter(mill__code=request.millcode)
    sides = ProcessingSide.objects.filter(mill__code=request.millcode)
    if request.method == "POST":
        stock = IncomingStockEntry.objects.get(pk=request.POST["stock"], category__mill__code=request.millcode)
        side = ProcessingSide.objects.get(pk=request.POST["side"], mill__code=request.millcode)
        bags = int(request.POST["quantity"])
        ProcessingSideEntry.objects.create(stock=stock, source=side, bags=bags, created_by=request.user)
        return render(request, "materials/processing-add.html", { "categories": categories, "sides": sides, "success_message": "Processing side stock entered successfully" } )
    return render(request, "materials/processing-add.html", { "categories": categories, "sides": sides } )


@login_required
@set_mill_session
def processing(request):
    mill = Mill.objects.get(code=request.millcode)
    sources = ProcessingSide.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    entries = ProcessingSideEntry.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode)
    if request.method == "POST":
        action = int(request.POST["action"])
        stock = ProcessingSideEntry.objects.get(pk=request.POST["entry"], entry__is_deleted=False)
        if action == 1:
            stock.entry.bags = 0 - int(request.POST["bags"])
            stock.entry.quantity = 0 - float(request.POST["quantity"])
            stock.category = Category.objects.get(pk=request.POST["category"])
            stock.source = ProcessingSide.objects.get(pk=request.POST["side"])
            date = request.POST["date"]
            stock.entry.date = datetime.strptime(date, "%d-%m-%Y")
            stock.entry.save()
            stock.save()
        elif action == 2:
            stock.entry.is_deleted = True
            stock.entry.save()
            stock.save()
        return render(request, "materials/processing.html", { "sources": sources, "categories": categories, "sides": sources, "entries": entries, "success_message": "Stock updated successfully"})
    return render(request, "materials/processing.html", { "sources": sources, "categories": categories, "sides": sources, "entries": entries})


# outgoing sources
@login_required
@set_mill_session
def godowns(request):
    mill = Mill.objects.get(code=request.millcode)
    godowns = OutgoingSource.objects.filter(mill=mill, is_deleted=False)
    if request.method == "POST":
        name = request.POST.get('name')
        OutgoingSource.objects.create(name=name, mill=mill, created_by=request.user, created_at=datetime.now)
        return redirect("materials-godowns", millcode=request.millcode)
    return render(request, "materials/godowns.html", {"godowns": godowns})


@login_required
@set_mill_session
def godownsAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    godowns = OutgoingSource.objects.filter(mill=mill, is_deleted=False)
    if request.method == "POST":
        id = int(id)
        obj = OutgoingSource.objects.get(id=id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            obj.name = request.POST.get('name')
            obj.save()
            return render(request, "materials/godowns.html", {"godowns": godowns, "success_message": "Godown updated successfully"})
        elif action == 2:
            obj.is_deleted = True
            obj.save()
            return render(request, "materials/godowns.html", {"godowns": godowns, "error_message": "Godown deleted successfully"})
    return redirect("materials-godowns", millcode=request.millcode)


@login_required
@set_mill_session
def configuration(request):
    mill = Mill.objects.get(code=request.millcode)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    incoming_sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    processing_sides = ProcessingSide.objects.filter(is_deleted=False, mill=mill)
    if request.method == 'POST':
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            Category.objects.create(name=name, mill=mill, created_by=request.user, created_at=datetime.now())
            return redirect("materials-configuration", millcode=request.millcode)
        elif action == 2:
            name = request.POST.get('name')
            trade = bool(request.POST.get("trade", 0))
            IncomingSource.objects.create(name=name, mill=mill, include_trading=trade, created_by=request.user, created_at=datetime.now())
            return redirect("materials-configuration", millcode=request.millcode)
        elif action == 3:
            name = request.POST.get('name')
            ProcessingSide.objects.create(name=name, mill=mill, created_by=request.user, created_at=datetime.now())
            return redirect("materials-configuration", millcode=request.millcode)
    return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides})

@login_required
@set_mill_session
def stock(request: WSGIRequest):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingStockEntry.objects.raw('SELECT id, c.name, SUM(bags) as stock FROM ( SELECT category_id, bags FROM materials_incomingstockentry i GROUP BY category_id UNION SELECT i.category_id, 0 - SUM(o.bags) bags FROM materials_incomingstockentry i LEFT OUTER JOIN materials_outgoingstockentry o ON i.id = o.stock_id GROUP BY o.stock_id, i.category_id UNION SELECT i.category_id, 0 - SUM(p.bags) bags FROM materials_incomingstockentry i LEFT OUTER JOIN materials_processingsideentry p ON i.id = p.stock_id GROUP BY p.stock_id, i.category_id) as bags INNER JOIN materials_category c ON category_id=c.id WHERE mill_id={} GROUP by category_id'.format(mill.pk))
    return render(request, "materials/stocks.html", { "stocks": stocks })

@login_required
@set_mill_session
def configurationAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    incoming_sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    processing_sides = ProcessingSide.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        id = int(id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            if len(name) > 0:
                obj = Category.objects.get(id=id)
                obj.name = name
                obj.save()
                return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides, "success_message": "Category updated successfully"})
        elif action == 2:
            obj = Category.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides, "error_message": "Category deleted successfully"})
        elif action == 3:
            name = request.POST.get('name')
            if len(name) > 0:
                obj: IncomingSource = IncomingSource.objects.get(id=id)
                obj.name = name
                obj.include_trading = bool(request.POST.get("trade", 0))
                obj.save()
                return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides, "success_message": "Incoming source updated successfully"})
        elif action == 4:
            obj = IncomingSource.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides, "error_message": "Incoming source deleted successfully"})
        elif action == 5:
            name = request.POST.get('name')
            if len(name) > 0:
                obj = ProcessingSide.objects.get(id=id)
                obj.name = name
                obj.save()
                return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides, "success_message": "Processing side updated successfully"})
        elif action == 6:
            obj = ProcessingSide.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "materials/configuration.html", {'categories': categories, 'sources': incoming_sources, 'sides': processing_sides, "error_message": "Processing side deleted successfully"})
    return redirect("materials-configuration", millcode=request.millcode)

@login_required
@set_mill_session
def trading(request: WSGIRequest):
    categories = Category.objects.filter(mill__code=request.millcode, is_deleted=False)
    mill = Mill.objects.get(code=request.millcode)
    trading = Trading.objects.filter(mill__code=request.millcode, entry__is_deleted=False)
    quantity = trading.values().aggregate(quantity=Sum('entry__quantity'), bags=Sum('entry__bags'))
    average_weight = 0 if quantity['quantity'] is None else quantity['quantity'] * 100 / quantity['bags'] if quantity['bags'] is not None else 1
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            price = float(request.POST["price"])
            quantity = float(request.POST["quantity"])
            bags = int(quantity * 100 / average_weight)
            entry = Stock.objects.create(bags=0 - bags, quantity=0 - quantity, date=datetime.now().astimezone().date(), remarks='Sold {} - {} quintal for \u20b9{}/- per/qtl'.format(bags, quantity, price))
            Trading.objects.create(entry=entry, price=price, mill=mill, created_by=request.user)
            return render(request, "materials/trading.html", { "trading": trading, "categories": categories, "success_message": "Trading record created successfully" })
        elif action == 2:
            price = float(request.POST["price"])
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            trade.price = price
            trade.save()
            return render(request, "materials/trading.html", { "trading": trading, "categories": categories, "success_message": "Trading record updated successfully" })
        elif action == 3:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            trade.entry.is_deleted = True
            trade.entry.save()
            trade.save()
            return render(request, "materials/trading.html", { "trading": trading, "categories": categories, "success_message": "Trading record deleted successfully", "quantity": quantity })
    return render(request, "materials/trading.html", { "trading": trading, "categories": categories, "quantity": quantity })

@login_required
@set_mill_session
def get_max_quantity(request: WSGIRequest, category: int):
    stocks = OutgoingStockEntry.objects.filter(category=category, category__mill__code=request.millcode, source__include_trading=True).values('source__pk',name=F('source__name')).annotate(quantity=Sum('entry__quantity'))
    stocks = [{
        "id": stock["source__pk"],
        "text": stock["name"],
        "max": abs(round(stock["quantity"], 2))
    } for stock in stocks]
    return JsonResponse(stocks, safe=False)

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

@login_required
@set_mill_session
def export_to_excel(request):
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output)
    categories = Category.objects.filter(mill__code=request.millcode, is_deleted=False)
    now = datetime.now().astimezone().date()
    _, day = calendar.monthrange(now.year, now.month)
    start = now.replace(day=1)
    end = now.replace(day=day)
    title_format = wb.add_format({ "font_size": 24, "underline": True, "bold": True, "align": 'center' })
    source_format = wb.add_format({ "bg_color": '#FFFF00', "bold": True, "font_size": 11, "align": 'center' })
    source_format.set_bold()
    source_format.set_text_v_align('vcenter')
    source_format.set_text_h_align('center')
    source_format.set_text_wrap()
    color_format = wb.add_format({ "bg_color": '#FF7F00', "bold": True })
    color_format.set_text_v_align('vcenter')
    color_format.set_text_h_align('center')
    color_format.set_text_wrap()
    normal_format = wb.add_format({ "align": 'center' })
    for category in categories:
        ws = wb.add_worksheet(category.name)
        incoming_sources = IncomingSource.objects.filter(is_deleted=False, mill__code=request.millcode)
        ws.set_row(1, height=36)
        ws.set_row(2, height=24)
        ws.merge_range(0, 0, 0, 2 * len(incoming_sources), "INCOMING", title_format)
        for i in range(0, len(incoming_sources), 1):
            ws.merge_range(1, 2 * i + 1, 1, 2 * i + 2, incoming_sources[i].name, source_format)
            ws.write(2, 2 * i + 1, '(In Bags)', color_format)
            ws.write(2, 2 * i + 2, '(In Qtl)', color_format)
            for j, date in zip(range(day), daterange(start, end)):
                ws.write(j+3, 0, '{}'.format(date.strftime("%d/%m/%Y")))
                incoming = IncomingStockEntry.objects.filter(entry__is_deleted=False, category=category, source=incoming_sources[i], entry__date=date).values('source').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum('entry__quantity'), 0)).values('bags', 'quantity')
                ws.write(j+3, 2 * i + 1, incoming[0]["bags"] if len(incoming) > 0 else '', normal_format)
                ws.write(j+3, 2 * i + 2, incoming[0]["quantity"] if len(incoming) > 0 else '', normal_format)
        outgoing_sources = OutgoingSource.objects.filter(is_deleted=False, mill__code=request.millcode)
        ws.merge_range(0,  2 * len(incoming_sources) + 1, 0, 2 * (len(incoming_sources) + len(outgoing_sources)), "OUTGOING", title_format)
        for i in range(len(incoming_sources), len(incoming_sources) + len(outgoing_sources), 1):
            ws.merge_range(1, 2 * i + 1, 1, 2 * i + 2, outgoing_sources[i - len(incoming_sources)].name, source_format)
            ws.write(2, 2 * i + 1, '(In Bags)')
            ws.write(2, 2 * i + 2, '(In Qtl)')
            for j, date in zip(range(day), daterange(start, end)):
                ws.write(j+3, 0, '{}'.format(date.strftime("%d/%m/%Y")))
                outgoing = OutgoingStockEntry.objects.filter(entry__is_deleted=False, category=category, source=outgoing_sources[i - len(incoming_sources)], entry__date=date).values('source').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum('entry__quantity'), 0)).values('bags', 'quantity')
                ws.write(j+3, 2 * i + 1, abs(outgoing[0]["bags"]) if len(outgoing) > 0 else '')
                ws.write(j+3, 2 * i + 2, abs(outgoing[0]["quantity"]) if len(outgoing) > 0 else '')  
        processing_sources = ProcessingSide.objects.filter(is_deleted=False, mill__code=request.millcode)
        ws.write(0, 2 * (len(incoming_sources) + len(outgoing_sources)) + 1, "PROCESSING", title_format)
        for i in range(len(incoming_sources) + len(outgoing_sources), len(incoming_sources) + len(processing_sources) + len(outgoing_sources), 1):
            ws.write(1, 2 * i + 1, processing_sources[i - (len(incoming_sources) + len(outgoing_sources))].name, source_format)
            ws.write(2, 2 * i + 1, '(In Bags)')
            ws.write(2, 2 * i + 2, '(In Qtl)')
            for j, date in zip(range(day), daterange(start, end)):
                ws.write(j+3, 0, '{}'.format(date.strftime("%d/%m/%Y")))
                processing = ProcessingSideEntry.objects.filter(entry__is_deleted=False, category=category, source=processing_sources[i - (len(incoming_sources) + len(outgoing_sources))], entry__date=date).values('source').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum('entry__quantity'), 0)).values('bags', 'quantity')
                ws.write(j+3, 2 * i + 1, abs(processing[0]["bags"]) if len(processing) > 0 else '')
                ws.write(j+3, 2 * i + 2, abs(processing[0]["quantity"]) if len(processing) > 0 else '')      
    wb.close()
    output.seek(0)
    response = HttpResponse(output ,content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="users.xlsx"'
    return response