import io
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.fields import FloatField, IntegerField
from django.db.models.functions.comparison import Coalesce
import xlsxwriter
from materials.models import Category
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from core.decorators import set_mill_session
from .models import IncomingProductEntry, ProductCategory, ProductStock, ProductionType, OutgoingProductEntry, Stock, Trading, TradingSource
from core.models import Mill


@login_required
@set_mill_session
def incoming(request):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingProductEntry.objects.filter(entry__is_deleted=False)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    return render(request, "products/incoming.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})


@login_required
@set_mill_session
def incomingAdd(request):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        try:
            date = request.POST.get('date')
            bags = int(request.POST.get('bags'))
            outgoing_bags = int(request.POST.get('outgoing_bags', '0'))
            category: ProductCategory = ProductCategory.objects.get(id=int(request.POST.get('category')))
            product_type: ProductionType = ProductionType.objects.get(id=int(request.POST.get('type')))
            remarks = "Added {} bags of {} - {}".format(bags, product_type.name, category.name)
            entry = Stock.objects.create(bags=bags, date=date, remarks=remarks)
            IncomingProductEntry.objects.create(entry=entry, created_by=request.user, category=category, product=product_type)
            remarks = "Sent {} bags of {} - {}".format(outgoing_bags, product_type.name, category.name)
            entry = Stock.objects.create(bags=0 - outgoing_bags, date=date, remarks=remarks)
            OutgoingProductEntry.objects.create(entry=entry, category=category, product=product_type, created_by=request.user)
            remarks = "Stock {} bags of {} - {}".format(bags - outgoing_bags, product_type.name, category.name)
            entry = Stock.objects.create(bags=0 - (bags - outgoing_bags), date=date, remarks=remarks)
            ProductStock.objects.create(entry=entry, category=category, product=product_type, created_by=request.user)
            return render(request, "products/incoming-add.html", {'categories': categories, 'success_message': "Incoming product entry added successfully"})
        except ValueError:
            return render(request, "products/incoming-add.html", {'categories': categories, 'error_message': "Please enter valid entries"})
    return render(request, "products/incoming-add.html", {'categories': categories })


@login_required
@set_mill_session
def incomingAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingProductEntry.objects.filter(entry__is_deleted=False)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        action = int(request.POST.get('action', '0'))
        id = int(id)
        obj = IncomingProductEntry.objects.get(id=id, category__mill__code=request.millcode)
        if action == 1:
            try:
                obj.entry.date = request.POST.get('date')
                obj.entry.bags = float(request.POST.get('bags'))
                obj.category = ProductCategory.objects.get(id=int(request.POST.get('category')))
                obj.product = ProductionType.objects.get(id=int(request.POST.get('product')))
                obj.entry.save()
                obj.save()
                return render(request, "products/incoming.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types, 'success_message': "Product entry updated successfully"})
            except ValueError:
                return render(request, "products/incoming.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types, 'error_message': "Number of bags must be a valid number"})
        elif action == 2:
            obj.entry.is_deleted = True
            obj.entry.save()
            obj.save()
            return render(request, "products/incoming.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types, 'error_message': "Entry deleted successfully"})
    return redirect("products-incoming", millcode=request.millcode)


@login_required
@set_mill_session
def outgoing(request):
    mill = Mill.objects.get(code=request.millcode)
    stocks = OutgoingProductEntry.objects.filter(entry__is_deleted=False)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    return render(request, "products/outgoing.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})

@login_required
@set_mill_session
def outgoing_data(request):
    if request.method == "POST":
        mill = Mill.objects.get(code=request.millcode)
        stocks = OutgoingProductEntry.objects.filter(entry__is_deleted=False)
        categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
        production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
        return render(request, "products/outgoing.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})
    return redirect('materials-outgoing', millcode=request.millcode)


@login_required
@set_mill_session
def max_stock(request, category: int):
    stocks = ProductStock.objects.filter(category__pk=category, entry__is_deleted=False).values(name=F('product__pk')).annotate(max=Sum('entry__bags'))
    stocks = [{
        "id": stock["name"],
        "text": ProductionType.objects.get(pk=stock["name"]).name,
        "max": abs(stock["max"])
    } for stock in stocks]
    return JsonResponse(stocks, safe=False)

@login_required
@set_mill_session
def outgoingAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    if request.method == "POST":
        action = int(request.POST.get('action', '0'))
        id = int(id)
        obj = OutgoingProductEntry.objects.get(id=id, category__mill=mill)
        if action == 1:
            obj.entry.date = request.POST.get('date')
            obj.entry.bags = 0 - int(request.POST.get('bags'))
            obj.category = ProductCategory.objects.get(id=int(request.POST.get('category')))
            obj.product = ProductionType.objects.get(id=int(request.POST.get('product')))
            obj.entry.save()
            obj.save()
        elif action == 2:
            obj.entry.is_deleted = True
            obj.entry.save()
            obj.save()
    return redirect("products-outgoing-data", millcode=request.millcode)


@login_required
@set_mill_session
def configuration(request):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    trading_sources = TradingSource.objects.filter(is_deleted=False, category__mill=mill)
    if request.method == 'POST':
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            ProductCategory.objects.create(name=name, mill=mill, created_by=request.user, created_at=datetime.now())
            return redirect("products-configuration", millcode=request.millcode)
        elif action == 2:
            try:
                name = request.POST.get('name')
                category = ProductCategory.objects.get(id=int(request.POST.get('category')))
                quantity = float(request.POST.get('quantity'))
                mix = bool(request.POST.get("mix", 0))
                ProductionType.objects.create(name=name, category=category, is_mixture=mix, quantity=quantity, mill=mill, created_by=request.user, created_at=datetime.now())
                return redirect("products-configuration", millcode=request.millcode)
            except ValueError:
                return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "error_message": "Please enter valid entries"})
        elif action == 3:
            try:
                name = request.POST.get('name')
                category = ProductCategory.objects.get(id=int(request.POST.get('category')))
                quantity = float(request.POST.get('quantity'))
                TradingSource.objects.create(name=name, category=category, quantity=quantity, created_by=request.user)
                return redirect("products-configuration", millcode=request.millcode)
            except ValueError:
                return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "error_message": "Please enter valid entries"})
    return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources })

@login_required
@set_mill_session
def get_production_types(request, category: int):
    types = [{
        "id": ptype.pk,
        "text": ptype.name,
        "quantity": ptype.quantity,
        "is_trading": False
    } for ptype in ProductionType.objects.filter(category=category, is_deleted=False)]
    return JsonResponse(types, safe=False)

@login_required
@set_mill_session
def configurationAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    trading_sources = TradingSource.objects.filter(is_deleted=False, category__mill=mill)
    if request.method == "POST":
        id = int(id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            if len(name) > 0:
                obj = ProductCategory.objects.get(id=id)
                obj.name = name
                obj.save()
                return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "success_message": "Category updated successfully"})
        elif action == 2:
            obj = ProductCategory.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "error_message": "Category deleted successfully"})
        elif action == 3:
            name = request.POST.get('name')
            if len(name) > 0:
                try:
                    obj = ProductionType.objects.get(id=id)
                    obj.name = name
                    obj.quantity = float(request.POST.get('quantity'))
                    obj.category = ProductCategory.objects.get(
                        id=int(request.POST.get('category')))
                    obj.save()
                    return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "success_message": "Production type updated successfully"})
                except ValueError:
                    return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "error_message": "Please enter valid entries"})
        elif action == 4:
            obj = ProductionType.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "error_message": "Production type deleted successfully"})
        elif action == 5:
            obj = TradingSource.objects.get(pk=request.POST["trading"])
            obj.name = request.POST["name"]
            obj.quantity = request.POST["quantity"]
            obj.category = ProductCategory.objects.get(pk=request.POST["category"])
            obj.save()
            return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "success_message": "Trading source updated successfully"})
        elif action == 6:
            obj = TradingSource.objects.get(pk=request.POST["trading"])
            obj.is_deleted = True
            obj.save()
            return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "trading_sources": trading_sources, "success_message": "Trading source deleted successfully"})
    return redirect("products-configuration", millcode=request.millcode)

@login_required
@set_mill_session
def stocks(request):
    stocks = ProductStock.objects.filter(entry__is_deleted=False, category__mill__code=request.millcode)
    categories = ProductCategory.objects.filter(mill__code=request.millcode, is_deleted=False)
    return render(request, "products/stocks.html", { "stocks": stocks, "categories": categories })

@login_required
@set_mill_session
def analysis(request):
    mill = Mill.objects.get(code=request.millcode)
    entries = Stock.objects.filter(is_deleted=False, category__mill__code=request.millcode).order_by('-date')
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    return render(request, "products/reports.html", { "entries": entries, "categories": categories, "production_types": production_types })

@login_required
@set_mill_session
def max_trading_stock(request, category):
    entries = Trading.objects.filter(entry__is_deleted=False, source__category=category, source__is_deleted=False).values(name=F('source__id')).annotate(max=Sum("entry__bags"))
    entries = [{
        "id": entry["name"],
        "text": TradingSource.objects.get(pk=entry["name"]).name,
        "max": entry["max"]
    } for entry in entries]
    return JsonResponse(entries, safe=False)

@login_required
@set_mill_session
def sources(request, category):
    sources = TradingSource.objects.filter(category=category, is_deleted=False)
    print(sources)
    sources = [{
        "id": source.pk,
        "text": source.name
    } for source in sources]
    return JsonResponse(sources, safe=False)

@login_required
@set_mill_session
def trading(request: WSGIRequest):
    categories = ProductCategory.objects.filter(mill__code=request.millcode, is_deleted=False)
    trading = Trading.objects.filter(source__category__mill__code=request.millcode, entry__is_deleted=False)
    quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
    average_price = Trading.objects.filter(source__category__mill__code=request.millcode, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum(F('price'), output_field=FloatField()))
    average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            price = float(request.POST["price"])
            source = TradingSource.objects.get(pk=request.POST["source"])
            bags = int(request.POST["bags"])
            entry = Stock.objects.create(bags=bags, date=datetime.now().astimezone().date(), remarks='Added {} - {} bags for \u20b9{}/-'.format(source.name, bags, price))
            Trading.objects.create(entry=entry, price=price, source=source, created_by=request.user)
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, 'average_price': average_price, "success_message": "Trading stock added successfully" })
        elif action == 2:
            price = 0 - float(request.POST["price"])
            source = TradingSource.objects.get(pk=request.POST["source"])
            bags = 0 - int(request.POST["bags"])
            entry = Stock.objects.create(bags=bags, date=datetime.now().astimezone().date(), remarks='Added {} - {} bags for \u20b9{}/-'.format(source.name, bags, price))
            Trading.objects.create(entry=entry, price=price, source=source, created_by=request.user)
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, 'average_price': average_price, "success_message": "Trading stock added successfully" })
        elif action == 3:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            price = float(request.POST["price"])
            trade.price = price
            trade.entry.save()
            trade.save()
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, 'average_price': average_price, "success_message": "Trading record updated successfully" })
        elif action == 4:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            price = float(request.POST["price"])
            trade.price = 0 - price
            trade.entry.save()
            trade.save()
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, 'average_price': average_price, "success_message": "Trading record updated successfully" })
        elif action == 5:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            trade.entry.is_deleted = True
            trade.entry.save()
            trade.save()
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, 'average_price': average_price, "success_message": "Trading record deleted successfully", "quantity": quantity })
    return render(request, "products/trading.html", { "trading": trading, "categories": categories, "quantity": quantity, 'average_price': average_price })


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)
        

@login_required
@set_mill_session
def export_to_excel(request):
    output = io.BytesIO()
    start = datetime.strptime(request.GET["from"], "%Y-%m-%d")
    end = datetime.strptime(request.GET["to"], "%Y-%m-%d")
    day = (end - start).days + 1
    wb = xlsxwriter.Workbook(output)
    categories = ProductCategory.objects.filter(mill__code=request.millcode, is_deleted=False)
    title_format = wb.add_format({ "font_size": 16, "underline": True, "bold": True, "align": 'center' })
    source_format = wb.add_format({ "bg_color": '#FFFF00', "bold": True, "font_size": 10, "align": 'center' })
    source_format.set_bold()
    source_format.set_border()
    source_format.set_text_wrap()
    color_format = wb.add_format({ "bg_color": '#FF7F00', "align": 'center', "bold": True })
    color_format.set_text_wrap()
    color_format.set_border()
    normal_format = wb.add_format({ "align": 'center' })
    for category in categories:
        ws = wb.add_worksheet(category.name)
        types = ProductionType.objects.filter(is_deleted=False, category=category)
        ws.set_row(1, height=48)
        ws.set_row(2, height=36)
        ws.merge_range(0, 1, 0, len(types), "INCOMING + PRODUCTION", title_format)
        ws.merge_range(0, len(types) + 1, 0, 2 * len(types), "OUTGOING", title_format)
        ws.merge_range(0, 2 * len(types) + 1, 0, 3 * len(types), "STOCK", title_format)
        for i in range(0, len(types), 1):
            ws.write(1, i + 1, types[i].name, source_format)
            ws.write(2, i + 1, types[i].quantity, color_format)
            ws.write(3, i + 1, '(In Bags)', color_format)
            ws.write(1, len(types) + i + 1, types[i].name, source_format)
            ws.write(2, len(types) + i + 1, types[i].quantity, color_format)
            ws.write(3, len(types) + i + 1, '(In Bags)', color_format)
            ws.write(1, 2 * len(types) + i + 1, types[i].name, source_format)
            ws.write(2, 2 * len(types) + i + 1, types[i].quantity, color_format)
            ws.write(3, 2 * len(types) + i + 1, '(In Bags)', color_format)
            for j, date in zip(range(day), daterange(start, end)):
                ws.write(j+4, 0, '{}'.format(date.strftime("%d/%m/%Y")))
                incoming = IncomingProductEntry.objects.filter(entry__is_deleted=False, category=category, product=types[i], entry__date=date).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0)).values('bags')
                ws.write(j+4, i + 1, incoming[0]["bags"] if len(incoming) > 0 else '', normal_format)
                outgoing = OutgoingProductEntry.objects.filter(entry__is_deleted=False, category=category, product=types[i], entry__date=date).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0)).values('bags')
                ws.write(j+4, len(types) + i + 1, abs(outgoing[0]["bags"]) if len(outgoing) > 0 else '')
                stock = ProductStock.objects.filter(entry__is_deleted=False, category=category, product=types[i], entry__date=date).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0)).values('bags')
                ws.write(j+4, 2 * len(types) + i + 1, abs(stock[0]["bags"]) if len(stock) > 0 else '')
        wb.close()
    output.seek(0)
    response = HttpResponse(output ,content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="users.xlsx"'
    return response