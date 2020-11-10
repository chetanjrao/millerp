from django.http.response import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from core.decorators import set_mill_session
from .models import IncomingProductEntry, ProductCategory, ProductStock, ProductionType, OutgoingProductEntry, Stock, Trading
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
            price = float(request.POST["price"])
            category: ProductCategory = ProductCategory.objects.get(id=int(request.POST.get('category')))
            product_type: ProductionType = ProductionType.objects.get(id=int(request.POST.get('type')))
            remarks = "Added {} bags of {} - {}".format(bags, product_type.name, category.name)
            entry = Stock.objects.create(bags=bags, category=category, product=product_type, date=date, remarks=remarks)
            IncomingProductEntry.objects.create(entry=entry, created_by=request.user)
            if price is not None:
                Trading.objects.create(entry=entry, price=price, created_by=request.user)
            remarks = "Sent {} bags of {} - {}".format(outgoing_bags, product_type.name, category.name)
            entry = Stock.objects.create(bags=0 - outgoing_bags, category=category, product=product_type, date=date, remarks=remarks)
            OutgoingProductEntry.objects.create(entry=entry, created_by=request.user)
            remarks = "Stock {} bags of {} - {}".format(bags - outgoing_bags, product_type.name, category.name)
            entry = Stock.objects.create(bags=0 - (bags - outgoing_bags), category=category, product=product_type, date=date, remarks=remarks)
            ProductStock.objects.create(entry=entry, created_by=request.user)
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
        obj = IncomingProductEntry.objects.get(id=id, entry__category__mill__code=request.millcode)
        if action == 1:
            try:
                obj.entry.date = request.POST.get('date')
                obj.entry.bags = float(request.POST.get('bags'))
                obj.entry.category = ProductCategory.objects.get(id=int(request.POST.get('category')))
                obj.entry.product = ProductionType.objects.get(id=int(request.POST.get('product')))
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
    production_types = ProductionType.objects.filter(
        is_deleted=False, mill=mill)
    return render(request, "products/outgoing.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types})


@login_required
@set_mill_session
def outgoingAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingProductEntry.objects.filter(entry__is_deleted=False)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        action = int(request.POST.get('action', '0'))
        id = int(id)
        obj = OutgoingProductEntry.objects.get(id=id)
        if action == 1:
            obj.entry.date = request.POST.get('date')
            obj.entry.bags = 0 - int(request.POST.get('bags'))
            obj.entry.category = ProductCategory.objects.get(id=int(request.POST.get('category')))
            obj.entry.product = ProductionType.objects.get(id=int(request.POST.get('product')))
            obj.entry.save()
            obj.save()
        elif action == 2:
            obj.entry.is_deleted = True
            obj.entry.save()
            obj.save()
            return render(request, "products/outgoing.html", {'stocks': stocks, 'categories': categories, 'production_types': production_types, 'error_message': "Entry deleted successfully"})
    return redirect("products-outgoing", millcode=request.millcode)


@login_required
@set_mill_session
def configuration(request):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(
        is_deleted=False, mill=mill)
    if request.method == 'POST':
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            ProductCategory.objects.create(
                name=name, mill=mill, created_by=request.user, created_at=datetime.now())
            return redirect("products-configuration", millcode=request.millcode)
        elif action == 2:
            try:
                name = request.POST.get('name')
                category = ProductCategory.objects.get(id=int(request.POST.get('category')))
                quantity = float(request.POST.get('quantity'))
                trade = bool(request.POST.get("trade", 0))
                mix = bool(request.POST.get("mix", 0))
                ProductionType.objects.create(name=name, category=category, include_trading=trade, is_mixture=mix, quantity=quantity, mill=mill, created_by=request.user, created_at=datetime.now())
                return redirect("products-configuration", millcode=request.millcode)
            except ValueError:
                return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types, "error_message": "Please enter valid entries"})
    return render(request, "products/configuration.html", {'categories': categories, 'production_types': production_types})

@login_required
@set_mill_session
def get_production_types(request, category: int):
    types = [{
        "id": ptype.pk,
        "text": ptype.name,
        "quantity": ptype.quantity,
        "is_trading": ptype.include_trading
    } for ptype in ProductionType.objects.filter(category=category, is_deleted=False)]
    return JsonResponse(types, safe=False)

@login_required
@set_mill_session
def configurationAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    categories = ProductCategory.objects.filter(is_deleted=False, mill=mill)
    production_types = ProductionType.objects.filter(
        is_deleted=False, mill=mill)
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
    stocks = ProductStock.objects.filter(entry__is_deleted=False, entry__category__mill__code=request.millcode)
    return render(request, "products/stocks.html", { "stocks": stocks })

@login_required
@set_mill_session
def analysis(request):
    entries = Stock.objects.filter(is_deleted=False, category__mill__code=request.millcode).order_by('-date')
    return render(request, "products/reports.html", { "entries": entries })