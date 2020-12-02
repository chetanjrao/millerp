import io
import re
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.fields import FloatField, IntegerField
from django.db.models.functions.comparison import Coalesce
import xlsxwriter
from materials.models import Category, ProcessingSide, ProcessingSideEntry
from django.db.models.aggregates import Sum
from django.db.models.expressions import F, Func
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from core.decorators import set_mill_session
from .models import IncomingProductEntry, ProductCategory, ProductStock, ProductionType, OutgoingProductEntry, Stock, Trading, TradingSource
from core.models import Mill, Rice


@login_required
@set_mill_session
def incoming(request):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__mill=request.mill, category__rice=request.rice)
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, category__rice=request.rice, mill=mill)
    return render(request, "products/incoming.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})


@login_required
@set_mill_session
def incomingAdd(request):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
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
    stocks = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__mill=request.mill, category__rice=request.rice)
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, category__rice=request.rice,  mill=mill)
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
    stocks = OutgoingProductEntry.objects.filter(entry__is_deleted=False, category__rice=request.rice, product__mill=mill, entry__bags__lte=0)
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    return render(request, "products/outgoing.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})

@login_required
@set_mill_session
def outgoing_data(request):
    if request.method == "POST":
        mill = Mill.objects.get(code=request.millcode)
        stocks = OutgoingProductEntry.objects.filter(entry__is_deleted=False,  category__rice=request.rice)
        categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
        production_types = ProductionType.objects.filter(is_deleted=False,  category__rice=request.rice, mill=mill)
        return render(request, "products/outgoing.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})
    return redirect('materials-outgoing', millcode=request.millcode)


@login_required
@set_mill_session
def max_stock(request, category: int):
    stocks = ProductStock.objects.filter(category__pk=category, category__mill=request.mill, category__rice=request.rice, entry__is_deleted=False).values(name=F('product__pk')).annotate(max=Sum('entry__bags'))
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
    return redirect("products-outgoing", millcode=request.millcode)


@login_required
@set_mill_session
def configuration(request):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, category__rice=request.rice, mill=mill)
    trading_sources = TradingSource.objects.filter(is_deleted=False, category__rice=request.rice, category__mill=mill)
    if request.method == 'POST':
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            biproduct = request.POST.get("biproduct", False)
            print(biproduct)
            ProductCategory.objects.create(name=name, is_biproduct=biproduct, mill=mill, rice=request.rice, created_by=request.user, created_at=datetime.now())
            return redirect("products-configuration", millcode=request.millcode)
        elif action == 2:
            try:
                name = request.POST.get('name')
                category = ProductCategory.objects.get(id=int(request.POST.get('category')))
                quantity = float(request.POST.get('quantity'))
                is_mixture = request.POST.get("mix", False)
                is_external = request.POST.get("external", False)
                ProductionType.objects.create(name=name, category=category, is_mixture=is_mixture, is_external=is_external, quantity=quantity, mill=mill, created_by=request.user, created_at=datetime.now())
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
        elif action == 4:
            name = request.POST["name"]
            Customer.objects.create(name=name, mill=request.mill)
            return redirect("products-configuration", millcode=request.millcode)
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
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, category__rice=request.rice, mill=mill)
    trading_sources = TradingSource.objects.filter(is_deleted=False, category__rice=request.rice, category__mill=mill)
    if request.method == "POST":
        id = int(id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            if len(name) > 0:
                obj = ProductCategory.objects.get(id=id)
                biproduct = request.POST.get("biproduct", False)
                obj.is_biproduct = biproduct
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
                    obj.is_mixture = request.POST.get("mix", False)
                    obj.is_external = request.POST.get("external", False)
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
    categories = ProductCategory.objects.filter(mill__code=request.millcode, rice=request.rice, is_deleted=False)
    stocks = ProductStock.objects.filter(entry__is_deleted=False, product__category__in=categories, category__rice=request.rice, entry__bags__lte=0, category__mill__code=request.millcode)
    production_types = ProductionType.objects.filter(is_deleted=False, category__in=categories, category__rice=request.rice, mill=request.mill)
    entries = ProductStock.objects.filter(entry__is_deleted=False, product__category__in=categories, category__in=categories, category__rice=request.rice, category__mill__code=request.millcode).values('product', 'category__name', name=F('product__name')).annotate(total=Sum('entry__bags'))
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            product = ProductionType.objects.get(pk=request.POST["product"])
            bags = int(request.POST["bags"])
            date = datetime.strptime(request.POST["date"], "%d-%m-%Y")
            remarks = "Removed {} bags of {} - {}".format(bags , product.name, product.category.name)
            entry = Stock.objects.create(bags=bags, date=date, remarks=remarks)
            ProductStock.objects.create(entry=entry, category=product.category, product=product, created_by=request.user)
            remarks = "Sent {} bags of {} - {}".format(bags, product.name, product.category.name)
            entry = Stock.objects.create(bags=0 - bags, date=date, remarks=remarks)
            OutgoingProductEntry.objects.create(entry=entry, category=product.category, product=product, created_by=request.user)
            return render(request, "products/stocks.html", { "stocks": stocks, "categories": categories, "success_message": "Stock sent successfully", "entries": entries })
        elif action == 2:
            stock = ProductStock.objects.get(pk=request.POST["stock"], entry__is_deleted=False)
            stock.entry.bags = 0 - int(request.POST["bags"])
            stock.category = ProductCategory.objects.get(pk=request.POST["category"])
            stock.product = ProductionType.objects.get(pk=request.POST["product"])
            stock.entry.date = datetime.strptime(request.POST["date"], "%Y-%m-%d")
            stock.entry.save()
            stock.save()
            return render(request, "products/stocks.html", { "stocks": stocks, "production_types": production_types, "categories": categories, "success_message": "Stock updated successfully", "entries": entries })
        elif action == 3:
            stock = ProductStock.objects.get(pk=request.POST["stock"], entry__is_deleted=False)
            stock.entry.is_deleted = True
            stock.entry.save()
            stock.save()
        return render(request, "products/stocks.html", { "stocks": stocks, "production_types": production_types, "categories": categories, "success_message": "Stock deleted successfully", "entries": entries })
    return render(request, "products/stocks.html", { "stocks": stocks, "production_types": production_types, "categories": categories, "entries": entries })

@login_required
@set_mill_session
def analysis(request):
    mill = Mill.objects.get(code=request.millcode)
    entries = Stock.objects.filter(is_deleted=False, category__mill__code=request.millcode).order_by('-date')
    categories = ProductCategory.objects.filter(is_deleted=False, rice=request.rice, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False,  category__rice=request.rice, mill=mill)
    return render(request, "products/reports.html", { "entries": entries, "categories": categories, "production_types": production_types })

@login_required
@set_mill_session
def max_trading_stock(request, category):
    entries = Trading.objects.filter(entry__is_deleted=False, source__category__rice=request.rice, source__category=category, source__is_deleted=False).values(name=F('source__id')).annotate(max=Sum("entry__bags"))
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
    sources = [{
        "id": source.pk,
        "text": source.name
    } for source in sources]
    return JsonResponse(sources, safe=False)

@login_required
@set_mill_session
def trading(request: WSGIRequest):
    categories = ProductCategory.objects.filter(mill__code=request.millcode, rice=request.rice, is_deleted=False)
    trading = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False)
    quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
    average_price = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))
    total_price = average_price["price"]
    total_quantity = average_price["total"]
    average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            price = float(request.POST["price"])
            source = TradingSource.objects.get(pk=request.POST["source"])
            bags = int(request.POST["bags"])
            entry = Stock.objects.create(bags=bags, date=datetime.now().astimezone().date(), remarks='Added {} - {} bags for \u20b9{}/-'.format(source.name, bags, price))
            Trading.objects.create(entry=entry, price=price, source=source, created_by=request.user)
            trading = Trading.objects.filter(source__category__mill__code=request.millcode,  source__category__rice=request.rice, entry__is_deleted=False)
            quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
            average_price = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))
            total_price = average_price["price"]
            total_quantity = average_price["total"]
            average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
            return render(request, "products/trading.html", { "trading": trading, "total_price": total_price, "total_quantity":total_quantity, "categories": categories, 'average_price': average_price, "success_message": "Trading stock added successfully" })
        elif action == 2:
            price = 0 - float(request.POST["price"])
            source = TradingSource.objects.get(pk=request.POST["source"])
            bags = 0 - int(request.POST["bags"])
            entry = Stock.objects.create(bags=bags, date=datetime.now().astimezone().date(), remarks='Added {} - {} bags for \u20b9{}/-'.format(source.name, bags, price))
            Trading.objects.create(entry=entry, price=price, source=source, created_by=request.user)
            trading = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False)
            quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
            average_price = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))
            total_price = average_price["price"]
            total_quantity = average_price["total"]
            average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
            return render(request, "products/trading.html", { "trading": trading, "total_price": total_price, "total_quantity":total_quantity, "categories": categories, 'average_price': average_price, "success_message": "Trading stock added successfully" })
        elif action == 3:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            price = float(request.POST["price"])
            trade.price = price
            trade.entry.save()
            trade.save()
            trading = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False)
            quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
            average_price = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))
            total_price = average_price["price"]
            total_quantity = average_price["total"]
            average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
            return render(request, "products/trading.html", { "trading": trading, "total_price": total_price, "total_quantity":total_quantity, "categories": categories, 'average_price': average_price, "success_message": "Trading record updated successfully" })
        elif action == 4:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            price = float(request.POST["price"])
            trade.price = 0 - price
            trade.entry.save()
            trade.save()
            trading = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False)
            quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
            average_price = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))
            total_price = average_price["price"]
            total_quantity = average_price["total"]
            average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
            return render(request, "products/trading.html", { "trading": trading, "total_price": total_price, "total_quantity":total_quantity, "categories": categories, 'average_price': average_price, "success_message": "Trading record updated successfully" })
        elif action == 5:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            trade.entry.is_deleted = True
            trade.entry.save()
            trade.save()
            trading = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False)
            quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
            average_price = Trading.objects.filter(source__category__mill__code=request.millcode, source__category__rice=request.rice, entry__is_deleted=False).aggregate(total=Sum(F('entry__bags') * F('source__quantity') / 100, output_field=FloatField()), price=Sum((Func('entry__bags', function='ABS') * F('source__quantity') / 100) * F('price'), output_field=FloatField()))            
            total_price = average_price["price"]
            total_quantity = average_price["total"]
            average_price = round((0 if average_price["price"] is None else average_price["price"]) / (1 if average_price["total"] is None or average_price["total"] == 0 else average_price["total"]), 2)
            return render(request, "products/trading.html", { "trading": trading, "total_price": total_price, "total_quantity":total_quantity, "categories": categories, 'average_price': average_price, "success_message": "Trading record deleted successfully", "quantity": quantity })
    return render(request, "products/trading.html", { "trading": trading, "total_price": total_price, "total_quantity":total_quantity, "categories": categories, "quantity": quantity, 'average_price': average_price })


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
    categories = ProductCategory.objects.filter(mill__code=request.millcode, rice=request.rice, is_deleted=False)
    title_format = wb.add_format({ "font_size": 16, "underline": True, "bold": True, "align": 'center' })
    source_format = wb.add_format({ "bold": True, "font_size": 10, "align": 'center' })
    source_format.set_bold()
    source_format.set_border()
    source_format.set_text_wrap()
    color_format = wb.add_format({ "align": 'center', "bold": True })
    color_format.set_text_wrap()
    color_format.set_border()
    normal_format = wb.add_format({ "align": 'center' })
    for category in categories:
        ws = wb.add_worksheet(category.name)
        types = ProductionType.objects.filter(is_deleted=False, category__rice=request.rice, category=category)
        ws.set_row(1, height=48)
        ws.set_row(2, height=24)
        length = len(types)
        ws.merge_range(0, 1, 0, length + 2, "INCOMING + PRODUCTION", title_format)
        ws.merge_range(1, length + 1, 1, length + 2, 'Total', source_format)
        ws.write(3, length + 1, '(In Bags)', color_format)
        ws.write(3, length + 2, '(In Qtls)', color_format)
        ws.merge_range(0, length + 4, 0, 2 * length + 5, "OUTGOING", title_format)
        ws.merge_range(1, 2 * length + 4, 1, 2 * length + 5, "Total", source_format)
        ws.write(3, 2 * length + 4, '(In Bags)', color_format)
        ws.write(3, 2 * length + 5, '(In Qtls)', color_format)
        ws.merge_range(0, 2 * length + 7, 0, 3 * length + 8, "STOCK", title_format)
        ws.merge_range(1, 3 * length + 7, 1, 3 * length + 8, 'Total', source_format)
        ws.write(3, 3 * length + 7, '(In Bags)', color_format)
        ws.write(3, 3 * length + 8, '(In Qtls)', color_format)
        for i in range(0, length, 1):
            ws.write(1, i + 1, types[i].name, source_format)
            ws.write(2, i + 1, types[i].quantity, color_format)
            ws.write(3, i + 1, '(In Bags)', color_format)
            ws.write(1, length + i + 4, types[i].name, source_format)
            ws.write(2, length + i + 4, types[i].quantity, color_format)
            ws.write(3, length + i + 4, '(In Bags)', color_format)
            ws.write(1, 2 * length + i + 7, types[i].name, source_format)
            ws.write(2, 2 * length + i + 7, types[i].quantity, color_format)
            ws.write(3, 2 * length + i + 7, '(In Bags)', color_format)
            incoming_overall = IncomingProductEntry.objects.filter(entry__is_deleted=False, category=category, entry__date__gte=start, entry__date__lte=end).aggregate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity'), output_field=FloatField()), 0))
            outgoing_overall = OutgoingProductEntry.objects.filter(entry__is_deleted=False,  category=category, entry__bags__lte=0, entry__date__gte=start, entry__date__lte=end).aggregate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity'), output_field=FloatField()), 0))
            stock_overall = ProductStock.objects.filter(entry__is_deleted=False, category=category, entry__date__gte=start,entry__bags__lte=0, entry__date__lte=end).aggregate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity'), output_field=FloatField()), 0))
            for j, date in zip(range(day), daterange(start, end)):
                ws.set_column(0, 0, len(date.strftime("%d/%m/%Y")))
                ws.write(j+4, 0, '{}'.format(date.strftime("%d/%m/%Y")))
                incoming = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__rice=request.rice, category=category, product=types[i], entry__date=date).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0)).values('bags')
                total = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__rice=request.rice, category=category, entry__date=date).values('category').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity') / 100, output_field=FloatField()), 0)).values('bags', 'quantity')
                total_source = IncomingProductEntry.objects.filter(entry__is_deleted=False, category__rice=request.rice, category=category, product=types[i], entry__date__gte=start, entry__date__lte=end).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity') / 100, output_field=FloatField()), 0)).values('bags', 'quantity')
                ws.write(j+4, i + 1, incoming[0]["bags"] if len(incoming) > 0 else '', normal_format)
                ws.write(j+4, length + 1, total[0]["bags"] if len(total) > 0 else '', normal_format)
                ws.write(j+4, length + 2, round(total[0]["quantity"], 2) if len(total) > 0 else '', normal_format)
                ws.write(day + 4, i + 1, total_source[0]["bags"] if len(total_source) > 0 else '', source_format)
                outgoing = OutgoingProductEntry.objects.filter(entry__is_deleted=False, entry__bags__lte=0, category=category, product=types[i], entry__date=date).values('product').annotate(bags=Coalesce(Sum(Func('entry__bags', function='ABS')), 0)).values('bags')
                total = OutgoingProductEntry.objects.filter(entry__is_deleted=False, entry__bags__lte=0, category__rice=request.rice, category=category, entry__date=date).values('category').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(Func('entry__bags', function='ABS') * Func('product__quantity', function='ABS') / 100, output_field=FloatField()), 0)).values('bags', 'quantity')
                total_source = OutgoingProductEntry.objects.filter(entry__is_deleted=False, category__rice=request.rice, category=category, product=types[i], entry__date__gte=start, entry__date__lte=end).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity') / 100, output_field=FloatField()), 0)).values('bags', 'quantity')
                ws.write(j+4, length + i + 4, abs(outgoing[0]["bags"]) if len(outgoing) > 0 else '')
                ws.write(j+4, 2 * length + 4, abs(total[0]["bags"]) if len(total) > 0 else '', normal_format)
                ws.write(j+4, 2 * length + 5, round(total[0]["quantity"], 2) if len(total) > 0 else '', normal_format)
                ws.write(day + 4, length + i + 4, abs(total_source[0]["bags"]) if len(total_source) > 0 else '', source_format)
                stock = ProductStock.objects.filter(entry__is_deleted=False,  category__rice=request.rice, category=category, product=types[i], entry__date=date).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0)).values('bags')
                ws.write(j+4, 2 * length + i + 7, abs(stock[0]["bags"]) if len(stock) > 0 else '')
                total = ProductStock.objects.filter(entry__is_deleted=False, entry__bags__lte=0, category__rice=request.rice, category=category, entry__date=date).values('category').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(Func('entry__bags', function='ABS') * Func('product__quantity', function='ABS') / 100, output_field=FloatField()), 0)).values('bags', 'quantity')
                total_source = ProductStock.objects.filter(entry__is_deleted=False, category__rice=request.rice, category=category, product=types[i], entry__date__gte=start, entry__date__lte=end).values('product').annotate(bags=Coalesce(Sum('entry__bags'), 0), quantity=Coalesce(Sum(F('entry__bags') * F('product__quantity') / 100, output_field=FloatField()), 0)).values('bags', 'quantity')
                ws.write(j+4, 3 * length + 7, abs(total[0]["bags"]) if len(total) > 0 else '', normal_format)
                ws.write(j+4, 3 * length + 8, round(total[0]["quantity"], 2) if len(total) > 0 else '', normal_format)
                ws.write(day + 4, 2 * length + i + 7, abs(total_source[0]["bags"]) if len(total_source) > 0 else '', source_format)
            ws.write(day + 4, 0, 'Total', source_format)
            ws.write(day + 4, 2 * length + 4, abs(outgoing_overall["bags"]) if outgoing_overall["bags"] is not None or outgoing_overall["bags"] != 0 else '', source_format)
            ws.write(day + 4, 2 * length + 5, abs(round(outgoing_overall["quantity"] / 100, 2)) if abs(outgoing_overall["quantity"]) is not None or outgoing_overall["quantity"] != 0 else '', source_format)
            ws.write(day + 4, 3 * length + 7, abs(stock_overall["bags"]) if stock_overall["bags"] is not None or stock_overall["bags"] != 0 else '', source_format)
            ws.write(day + 4, 3 * length + 8, abs(round(stock_overall["quantity"] / 100, 2)) if stock_overall["quantity"] is not None or stock_overall["quantity"] != 0 else '', source_format)
            ws.write(day + 4, length + 1, incoming_overall["bags"] if incoming_overall["bags"] is not None or incoming_overall["bags"] != 0 else '', source_format)
            ws.write(day + 4, length + 2, abs(round(incoming_overall["quantity"], 2)) if incoming_overall["quantity"] / 100 is not None or incoming_overall["quantity"] != 0 else '', source_format)
    wb.close()
    output.seek(0)
    response = HttpResponse(output ,content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Rice Stock Details - {} - {}.xlsx"'.format(start.date(), end.date())
    return response



@login_required
@set_mill_session
def analysis(request):
    output = io.BytesIO()
    start = datetime.strptime(request.GET["from"], "%Y-%m-%d")
    end = datetime.strptime(request.GET["to"], "%Y-%m-%d")
    gross = 0
    rice = request.GET["rice"]
    rice = Rice.objects.get(pk=rice)
    paddy_categories = Category.objects.filter(mill=request.mill, is_deleted=False)
    paddy_gross = []
    wb = xlsxwriter.Workbook(output)
    ws = wb.add_worksheet("{} Analysis".format(rice.name))
    source_format = wb.add_format({ "bold": True,  "font_size": 11, "align": 'center' })
    source_format.set_bold()
    source_format.set_border()
    source_format.set_text_wrap()
    normal_format = wb.add_format({ "align": 'center' })
    bold_format = wb.add_format({ "align": 'center' })
    bold_format.set_bold()
    ws.set_column(0, 0, width=len('Purchased from outside'))
    ws.write(1, 0, 'Particulars', source_format)
    ws.write(4, 0, 'Total Production', bold_format)
    ws.write(5, 0, 'Closing Stock', bold_format)
    ws.write(6, 0, 'Opening Stock', bold_format)
    ws.write(7, 0, 'Purchased from outside', bold_format)
    ws.write(9, 0, 'Net Production', bold_format)
    ws.write(10, 0, 'Gross Total', bold_format)
    for i, paddy in enumerate(paddy_categories):
        ws.set_column(i+1, i+1, width=len('{} processed'.format(paddy.name)))
        ws.write(1, i + 1, '{} processed'.format(paddy.name), source_format)
        ws.write(2, i + 1, '(in Qtls)', bold_format)
        stock = ProcessingSideEntry.objects.filter(source__rice=rice, category=paddy, entry__is_deleted=False, entry__date__gte=start, entry__date__lte=end).aggregate(bags=Func(Coalesce(Sum('entry__quantity'), 0), function='ABS'))["bags"]
        closing_stock = float(request.GET.get("paddy{}".format(paddy.pk), 0))
        ws.write(4, i + 1, round(stock, 2), normal_format)
        ws.write(5, i + 1, round(closing_stock, 2), normal_format)
        ws.write(6, i + 1, '-', normal_format)
        ws.write(7, i + 1, '-', normal_format)
        ws.write(9, i + 1, round(stock - closing_stock, 2), source_format)
        paddy_gross.append(round(stock - closing_stock, 2))
    ws.merge_range(10, 1, 10, len(paddy_categories), round(sum(paddy_gross), 2), source_format)
    avgs = []
    rice_categories = ProductCategory.objects.filter(rice=rice, is_biproduct=False, mill=request.mill, is_deleted=False)
    gross = round(sum(paddy_gross), 2)
    for i, _rice in enumerate(rice_categories):
        ws.set_column(len(paddy_categories) + i + 2, len(paddy_categories) + i + 3, width=36)
        ws.write(1, len(paddy_categories) + i + 2, '{}'.format(_rice.name), source_format)
        ws.write(2, len(paddy_categories) + i + 2, '(in Qtls)', bold_format)
        ws.write(1, len(paddy_categories) + i + 3, 'PDS', source_format)
        ws.write(2, len(paddy_categories) + i + 3, '(in Qtls)', bold_format)
        stock = IncomingProductEntry.objects.filter(category__rice=rice, category=_rice, entry__date__gte=start, entry__is_deleted=False, entry__date__lte=end).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        opening_stock = IncomingProductEntry.objects.filter(category__rice=rice, category=_rice, entry__is_deleted=False, entry__date__lt=start).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        outside_stock = Trading.objects.filter(source__category__rice=rice, source__category=_rice, entry__is_deleted=False, entry__bags__gt=0).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('source__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        closing_stock = float(request.GET.get("product{}".format(_rice.pk), 0))
        ws.write(4, len(paddy_categories) + i + 2, round(stock, 2), normal_format)
        ws.write(5, len(paddy_categories) + i + 2, round(closing_stock, 2), normal_format)
        ws.write(6, len(paddy_categories) + i + 2, round(opening_stock, 2), normal_format)
        ws.write(7, len(paddy_categories) + i + 2, round(outside_stock, 2), normal_format)
        calc = stock + closing_stock - opening_stock - outside_stock
        ws.write(9, len(paddy_categories) + i + 2, round(calc, 2), source_format)
        pds_stock = IncomingProductEntry.objects.filter(category__rice=rice, category__is_biproduct=False, product__is_external=True, category=_rice, entry__is_deleted=False, entry__date__gte=start, entry__date__lte=end).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        proper_stock = IncomingProductEntry.objects.filter(category__rice=rice, category__is_biproduct=False, category=_rice, entry__date__gte=start, entry__is_deleted=False, entry__date__lte=end).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        pds_opening_stock = IncomingProductEntry.objects.filter(category__rice=rice, category=_rice, entry__is_deleted=False, entry__date__lt=start).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        pds_closing_stock = float(request.GET.get("pds{}".format(_rice.pk), 0))
        ws.write(5, len(paddy_categories) + i + 3, round(pds_closing_stock, 2), normal_format)
        ws.write(6, len(paddy_categories) + i + 3, round(pds_opening_stock, 2), normal_format)
        ws.write(7, len(paddy_categories) + i + 3, round(0, 2), normal_format)
        ws.write(4, len(paddy_categories) + i + 3, round(pds_stock, 2), normal_format)
        average = round((proper_stock - pds_stock) * 100 / (gross if gross > 0 else 1), 2)
        avgs.append(average)
        pds_calc = pds_stock + pds_closing_stock - pds_opening_stock
        ws.write(9, len(paddy_categories) + i + 3, round(pds_calc, 2), source_format)
        ws.write(11, len(paddy_categories) + i + 2, '{}%'.format(average), source_format)
    biproducts = ProductCategory.objects.filter(rice=rice, is_biproduct=True, mill=request.mill, is_deleted=False)
    for i, _rice in enumerate(biproducts):
        ws.set_column(len(paddy_categories) + len(rice_categories) + i + 2, len(paddy_categories) + len(rice_categories) + i + 3, width=36)
        ws.write(1, len(paddy_categories) + len(rice_categories) + i + 2, '{}'.format(_rice.name), source_format)
        ws.write(2, len(paddy_categories) + len(rice_categories) + i + 2, '(in Qtls)', bold_format)
        stock = IncomingProductEntry.objects.filter(category__rice=rice, category=_rice, entry__date__gte=start, entry__is_deleted=False, entry__date__lte=end).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        opening_stock = IncomingProductEntry.objects.filter(category__rice=rice, category=_rice, entry__is_deleted=False, entry__date__lt=start).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('product__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        outside_stock = Trading.objects.filter(source__category__rice=rice, source__category=_rice, entry__is_deleted=False, entry__bags__gt=0).aggregate(bags=Func(Coalesce(Sum(Coalesce(F('entry__bags'), 0) * Coalesce(F('source__quantity'), 0) / 100, output_field=FloatField()), 0), function='ABS'))["bags"]
        closing_stock = float(request.GET.get("product{}".format(_rice.pk), 0))
        ws.write(4, len(paddy_categories) + len(rice_categories) + i + 2, round(stock, 2), normal_format)
        ws.write(5, len(paddy_categories) + len(rice_categories) + i + 2, round(closing_stock, 2), normal_format)
        ws.write(6, len(paddy_categories) + len(rice_categories) + i + 2, round(opening_stock, 2), normal_format)
        ws.write(7, len(paddy_categories) + len(rice_categories) + i + 2, round(outside_stock, 2), normal_format)
        calc = stock + closing_stock - opening_stock - outside_stock
        average = round(calc * 100 / gross, 2)
        avgs.append(average)
        ws.write(9, len(paddy_categories) + len(rice_categories) + i + 2, round(calc, 2), source_format)
        ws.write(11, len(paddy_categories) + len(rice_categories) + i + 2, '{}%'.format(avgs), source_format)
    ws.write(13, len(paddy_categories) + len(rice_categories), '{}%'.format(sum(avgs)))
    wb.close()
    output.seek(0)
    response = HttpResponse(output ,content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Analysis - {} - {}.xlsx"'.format(start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y"))
    return response