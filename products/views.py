from django.core.handlers.wsgi import WSGIRequest
from materials.models import Category
from django.db.models.aggregates import Sum
from django.db.models.expressions import F
from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
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
    return redirect("products-outgoing", millcode=request.millcode)


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
    if request.method == "POST":
        id = int(id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            if len(name) > 0:
                obj = ProductCategory.objects.get(id=id)
                obj.name = name
                obj.save()
                return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "success_message": "Category updated successfully"})
        elif action == 2:
            obj = ProductCategory.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "error_message": "Category deleted successfully"})
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
                    return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "success_message": "Production type updated successfully"})
                except ValueError:
                    return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "error_message": "Please enter valid entries"})
        elif action == 4:
            obj = ProductionType.objects.get(id=id)
            obj.is_deleted = True
            obj.save()
            return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "error_message": "Production type deleted successfully"})
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
def trading(request: WSGIRequest):
    categories = ProductCategory.objects.filter(mill__code=request.millcode, is_deleted=False)
    mill = Mill.objects.get(code=request.millcode)
    trading = Trading.objects.filter(source__category__mill__code=request.millcode, entry__is_deleted=False)
    quantity = trading.values('source__name').annotate(bags=Sum('entry__bags'))
    if request.method == "POST":
        action = int(request.POST["action"])
        if action == 1:
            price = float(request.POST["price"])
            source = TradingSource.objects.get(pk=request.POST["source"])
            bags = float(request.POST["bags"])
            entry = Stock.objects.create(bags=0 - bags, date=datetime.now().astimezone().date(), remarks='Sold {} - {} bags for \u20b9{}/-'.format(source.name, bags, price))
            Trading.objects.create(entry=entry, price=price, source=source, created_by=request.user)
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, "success_message": "Trading record created successfully" })
        elif action == 2:
            price = float(request.POST["price"])
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            trade.price = price
            trade.save()
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, "success_message": "Trading record updated successfully" })
        elif action == 3:
            trade = Trading.objects.get(pk=request.POST["trade"], entry__is_deleted=False)
            trade.entry.is_deleted = True
            trade.entry.save()
            trade.save()
            return render(request, "products/trading.html", { "trading": trading, "categories": categories, "success_message": "Trading record deleted successfully", "quantity": quantity })
    return render(request, "products/trading.html", { "trading": trading, "categories": categories, "quantity": quantity })
