from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.core.handlers.wsgi import WSGIRequest
from rest_framework.views import csrf_exempt
from django.contrib.auth.decorators import login_required
from selenium.webdriver.chrome.webdriver import WebDriver
from core.decorators import set_mill_session
from core.models import Mill
from .models import IncomingStockEntry, Category, IncomingSource, OutgoingStockEntry, OutgoingSource, ProcessingSide, ProcessingSideEntry
from datetime import datetime
import os
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, InvalidElementStateException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
import pytesseract
import cv2
import numpy as np
import re
from bs4 import BeautifulSoup

def get_captcha(driver: WebDriver):
    data = []
    while True:
        try:
            captcha_fn = "abc.png"
            element = driver.find_element_by_id('ImageCaptcha')
            location = element.location
            size = element.size
            driver.save_screenshot("bcd.png")
            x = location['x'] * 2
            y = location['y'] * 2
            w = size['width']
            h = size['height']
            width = x + w * 2
            height = y + h * 2
            im = Image.open('bcd.png')
            im = im.crop((x, y, width, height))
            im = im.convert('L')
            ret, img = cv2.threshold(np.array(im), 127, 255, cv2.THRESH_BINARY)
            im = Image.fromarray(img.astype(np.uint8))
            im.save(captcha_fn)
            text = pytesseract.image_to_string(im, config='--psm 10', lang="eng")
            text = re.sub('[^A-Za-z0-9]+', '', text)
            try:
                driver.find_element_by_id('txtpwd').clear()
                driver.find_element_by_id('txtVerificationCode').clear()
                driver.find_element_by_id('txtVerificationCode').send_keys(text.replace('\x0C', ''))
                driver.find_element_by_id('txtpwd').send_keys('100141')
                try:
                    driver.find_element_by_id('txtUser').clear()
                    driver.find_element_by_id('txtUser').send_keys('MA41141')
                    driver.find_element_by_name('btncon').click()
                    try:
                        driver.switch_to.alert.accept()
                        driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/SocietyPaddyDetails.aspx')
                        select = Select(driver.find_element_by_tag_name('select'))
                        select.select_by_value('41')
                        driver.find_element_by_id('Btnreport').click()
                        elem = driver.find_element_by_tag_name('tbody')
                        soup = BeautifulSoup(elem.get_attribute('outerHTML'), 'html.parser')
                        for row in soup.find_all('tr'):
                            data.append([cell.get_text() for cell in row.find_all('td')])
                    except (NoAlertPresentException, UnexpectedAlertPresentException):
                        continue
                    break
                except InvalidElementStateException:
                    try:
                        driver.find_element_by_name('btnOk').click()
                    except NoSuchElementException:
                        driver.find_element_by_name('btncon').click()
            except NoSuchElementException:
                continue
        except:
            driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/SocietyPaddyDetails.aspx')
            select = Select(driver.find_element_by_tag_name('select'))
            select.select_by_value('41')
            driver.find_element_by_id('Btnreport').click()
            elem = driver.find_element_by_tag_name('tbody')
            soup = BeautifulSoup(elem.get_attribute('outerHTML'), 'html.parser')
            for row in soup.find_all('tr'):
                data.append([cell.get_text() for cell in row.find_all('td')])
            break
        print(data)
        os.remove(captcha_fn)
    pass

@login_required
@set_mill_session
def incoming(request):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingStockEntry.objects.filter(is_deleted=False)
    sources = IncomingSource.objects.filter(
        is_deleted=False, mill=mill)
    categories = Category.objects.filter(
        is_deleted=False, mill=mill)
    return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories})


@login_required
@set_mill_session
def incomingAdd(request):
    mill = Mill.objects.get(code=request.millcode)
    sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    if request.method == "POST":
        date = request.POST.get('date', datetime.now())
        category = Category.objects.get(id=int(request.POST.get('category')))
        source = IncomingSource.objects.get(id=request.POST.get("source"))
        try:
            bags = float(request.POST.get('bags'))
            average_weight = float(request.POST.get('avg_wt'))
        except ValueError:
            return render(request, "materials/incoming-add.html", {"sources": sources, "categories": categories, "error_message": "Number of bags and average weight must be a valid number"})

        IncomingStockEntry.objects.create(
            date=date, category=category, source=source, bags=bags, average_weight=average_weight, created_by=request.user)
        return render(request, "materials/incoming-add.html", {"sources": sources, "categories": categories, "success_message": "Incoming entry added successfully"})
    return render(request, "materials/incoming-add.html", {"sources": sources, "categories": categories})


@login_required
@set_mill_session
def incomingAction(request, id):
    mill = Mill.objects.get(code=request.millcode)
    stocks = IncomingStockEntry.objects.filter(is_deleted=False)
    sources = IncomingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)

    if request.method == 'POST':
        id = int(id)
        obj = IncomingStockEntry.objects.get(id=id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            try:
                obj.date = request.POST.get('date_in')
                obj.source = IncomingSource.objects.get(
                    id=int(request.POST.get('source_id')))
                obj.category = Category.objects.get(
                    id=int(request.POST.get('category_id')))
                obj.bags = float(request.POST.get('bags'))
                obj.average_weight = float(request.POST.get('avg_wt'))
            except ValueError:
                return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories, "error_message": "PLease enter valid entries to update"})
            obj.save()
            return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories, "success_message": "Entry updated successfully"})
        elif action == 2:
            obj.is_deleted = True
            obj.save()
            return render(request, "materials/incoming.html", {"stocks": stocks, "sources": sources, "categories": categories,
                                                               "error_message": "Entry deleted successfully"})
    return redirect('materials-incoming', millcode=request.millcode)


@login_required
@set_mill_session
def outgoing(request):
    # options = Options()
    # options.add_argument('--headless')
    # options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    # start_url = "https://khadya.cg.nic.in/paddyonline/miller/millmodify19/MillLogin.aspx"
    # driver = webdriver.Chrome('/Users/chethanjkulkarni/Downloads/chromedriver')
    # driver.get(start_url)
    # get_captcha(driver)
    mill = Mill.objects.get(code=request.millcode)
    stocks = OutgoingStockEntry.objects.filter(is_deleted=False)
    sources = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    incoming_stock = IncomingStockEntry.objects.filter(is_deleted=False)
    return render(request, "materials/outgoing.html", {"stocks": stocks, "sources": sources, "categories": categories, "incoming_stock": incoming_stock})


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
    stocks = OutgoingStockEntry.objects.filter(is_deleted=False)
    sources = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    incoming_stock = IncomingStockEntry.objects.filter(is_deleted=False)
    if request.method == 'POST':
        id = int(id)
        obj = OutgoingStockEntry.objects.get(id=id)
        action = int(request.POST.get('action', '0'))
        if action == 1:
            pass
        elif action == 2:
            obj.is_deleted = True
            obj.save()
            return render(request, "materials/outgoing.html", {"stocks": stocks, "sources": sources, "incoming_stock": incoming_stock, "categories": categories,
                                                               "error_message": "Entry deleted successfully"})
    return redirect('materials-incoming', millcode=request.millcode)

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
    stocks = OutgoingStockEntry.objects.filter(is_deleted=False)
    sources = OutgoingSource.objects.filter(is_deleted=False, mill=mill)
    categories = Category.objects.filter(is_deleted=False, mill=mill)
    entries = ProcessingSideEntry.objects.filter(is_deleted=False)
    return render(request, "materials/processing.html", {"stocks": stocks, "sources": sources, "categories": categories, "entries": entries})


# outgoing sources
@login_required
@set_mill_session
def godowns(request):
    mill = Mill.objects.get(code=request.millcode)
    godowns = OutgoingSource.objects.filter(mill=mill, is_deleted=False)
    if request.method == "POST":
        name = request.POST.get('name')
        OutgoingSource.objects.create(
            name=name, mill=mill, created_by=request.user, created_at=datetime.now)
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
    incoming_sources = IncomingSource.objects.filter(
        is_deleted=False, mill=mill)
    processing_sides = ProcessingSide.objects.filter(
        is_deleted=False, mill=mill)
    if request.method == 'POST':
        action = int(request.POST.get('action', '0'))
        if action == 1:
            name = request.POST.get('name')
            Category.objects.create(
                name=name, mill=mill, created_by=request.user, created_at=datetime.now())
            return redirect("materials-configuration", millcode=request.millcode)
        elif action == 2:
            name = request.POST.get('name')
            IncomingSource.objects.create(
                name=name, mill=mill, created_by=request.user, created_at=datetime.now())
            return redirect("materials-configuration", millcode=request.millcode)
        elif action == 3:
            name = request.POST.get('name')
            ProcessingSide.objects.create(
                name=name, mill=mill, created_by=request.user, created_at=datetime.now())
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
    incoming_sources = IncomingSource.objects.filter(
        is_deleted=False, mill=mill)
    processing_sides = ProcessingSide.objects.filter(
        is_deleted=False, mill=mill)
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
                obj = IncomingSource.objects.get(id=id)
                obj.name = name
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
