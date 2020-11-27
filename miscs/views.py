import json
from core.models import Firm
from datetime import datetime
from millerp.utils import send_message
from django.utils.timezone import now
from millerp.settings.base import CHROME, CHROMEDRIVER, HEIGHT_RATIO, WIDTH_RATIO
import os
import random
import re, time
import string
from PIL import Image
import cv2
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse, JsonResponse
import numpy as np
import pytesseract
from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException, NoAlertPresentException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from core.decorators import set_mill_session
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from bs4 import BeautifulSoup, Tag
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from asgiref.sync import sync_to_async
from selenium.webdriver.support.select import Select
import pandas as pd

def get_random_string(length):
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


start_url = "https://khadya.cg.nic.in/paddyonline/miller/millmodify19/MillLogin.aspx"

def get_captcha(driver: WebDriver, screenshot: str, captcha: str, username: str, password: str, mobile: str):
    driver.get(start_url)
    attempts = 10
    response = {}
    total_do_lifted = 0
    total_do_pending = 0
    total_do_issued = 0
    total_do_cancelled = 0
    paddy_uplifted = 0
    rice_deposited = 0
    while True:
        if attempts <= 0:
            break
        try:
            element = driver.find_element_by_id('ImageCaptcha')
            location = element.location
            size = element.size
            driver.save_screenshot(screenshot)
            x = location['x'] * WIDTH_RATIO
            y = location['y'] * HEIGHT_RATIO
            w = size['width'] * WIDTH_RATIO
            h = size['height'] * HEIGHT_RATIO
            width = x + w
            height = y + h
            im = Image.open(screenshot)
            im = im.crop((x, y, width, height))
            im = im.convert('L')
            ret, img = cv2.threshold(np.array(im), 127, 255, cv2.THRESH_BINARY)
            im = Image.fromarray(img.astype(np.uint8))
            im.save(captcha)
            text = pytesseract.image_to_string(im, config='--psm 10', lang="eng")
            text = re.sub('[^A-Za-z0-9]+', '', text)
            driver.find_element_by_id('txtpwd').clear()
            driver.find_element_by_id('txtVerificationCode').clear()
            driver.find_element_by_id('txtVerificationCode').send_keys(text.replace('\x0C', ''))
            driver.find_element_by_id('txtpwd').send_keys('{}'.format(password))
            try:
                driver.find_element_by_id('txtUser').clear()
                driver.find_element_by_id('txtUser').send_keys('{}'.format(username))
                driver.find_element_by_name('btncon').click()
                attempts -= 1
                driver.switch_to.alert.accept()
            except UnexpectedAlertPresentException:
                pass
            except (InvalidElementStateException):
                attempts -= 1
                try:
                    driver.find_element_by_name('btnOk').click()
                except NoSuchElementException:
                    driver.find_element_by_name('btncon').click()
                continue
        except (NoAlertPresentException, NoSuchElementException, UnexpectedAlertPresentException):
            try:
                do_lifted = driver.find_element_by_id('ctl00_Miller_content1_lnkDocnt')
                do_pending = driver.find_element_by_id('ctl00_Miller_content1_lnkDopending')
                do_issued = driver.find_element_by_id('ctl00_Miller_content1_lnkDoissued')
                do_cancelled = driver.find_element_by_id('ctl00_Miller_content1_lnkDocancel')
                paddy_lifted = driver.find_element_by_id('ctl00_Miller_content1_lnkpaddylift')
                rice_deposit = driver.find_element_by_id('ctl00_Miller_content1_lnkricesubmit')
                do_location = do_issued.get_attribute('href')
                total_do_lifted = float(do_lifted.text)
                total_do_pending = float(do_pending.text)
                total_do_issued = float(do_issued.text)
                total_do_cancelled = float(do_cancelled.text)
                paddy_uplifted = float(paddy_lifted.text)
                rice_deposited = float(rice_deposit.text)
                response['total_do_lifted'] = total_do_lifted
                response['total_do_pending'] = total_do_pending
                response['total_do_issued'] = total_do_issued
                response['total_do_cancelled'] = total_do_cancelled
                response['paddy_uplifted'] = paddy_uplifted
                response['rice_deposited'] = rice_deposited
                driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/TypeSecurityCompleteReport.aspx')
                elem = driver.find_element_by_class_name('SiteText')
                HTML_DOCUMENT = elem.get_attribute('innerHTML')
                parser = BeautifulSoup(HTML_DOCUMENT, 'html.parser')
                table: Tag = parser.find_all('table')[-1]
                rows = table.find_all('tr')
                bg_secured = []
                headers = rows[0].find_all('td')
                headers = [header.get_text() for i, header in enumerate(headers) if i in [0, 2, 3, 6, 7, 11]]
                body = [row.find_all('td') for row in rows[1:-1]]
                body = [[row.get_text() for i, row in enumerate(row) if i in [0, 2, 3, 6, 7, 11]] for row in body]
                # for data in body:
                #     date = datetime.strptime(data[-1], "%d/%m/%Y")
                #     today = now().astimezone()
                #     if date > today:
                #         if (date - today).days % 5 == 0:
                #             sync_to_async(send_message, thread_sensitive=True)('Your Bank Guarantee is expiring')
                for row in body:
                    if row[4] == "सुरक्षित":
                        bg_secured.append(row)
                footer = rows[-1].find_all('td')
                bg_secured_raw = round(sum([float(data[1]) for data in bg_secured]), 2)
                bg_secured = round(sum([float(data[3]) for data in bg_secured]), 2)
                response["results"] = body
                response["bg_secured"] = bg_secured
                response["bg_secured_raw"] = bg_secured_raw
                driver.get(do_location)
                elem = driver.find_element_by_class_name('SiteText')
                HTML_DOCUMENT = elem.get_attribute('innerHTML')
                parser = BeautifulSoup(HTML_DOCUMENT, 'html.parser')
                table: Tag = parser.find_all('table')[-1]
                rows = table.find_all('tr')[1:-1]
                agreements = {}
                today = now().date().strftime("%d/%m/%Y")
                total_dos = 0
                dos = {
                    "m": 0,
                    "mm": 0,
                    "sr": 0,
                }
                for row in rows:
                    element = row.find_all('td')
                    agreements.setdefault('{}'.format(element[4].text), []).append(element[1].text)
                    if element[3].text == today:
                        total_dos += 1
                        dos["m"] += float(element[5].text)
                        dos["mm"] += float(element[6].text)
                        dos["sr"] += float(element[10].text)
                response["agreements"] = agreements
                response["dos"] = dos
                response["total_dos"] = total_dos
                break
            except NoSuchElementException:
                continue
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return response

def get_print(driver: WebDriver, screenshot: str, captcha: str, username: str, password: str, agreement: str, do: str):
    driver.get(start_url)
    attempts = 10
    pdf = ""
    while True:
        if attempts <= 0:
            break
        try:
            element = driver.find_element_by_id('ImageCaptcha')
            location = element.location
            size = element.size
            driver.save_screenshot(screenshot)
            x = location['x'] * WIDTH_RATIO
            y = location['y'] * HEIGHT_RATIO
            w = size['width'] * WIDTH_RATIO
            h = size['height'] * HEIGHT_RATIO
            width = x + w
            height = y + h
            im = Image.open(screenshot)
            im = im.crop((x, y, width, height))
            im = im.convert('L')
            ret, img = cv2.threshold(np.array(im), 127, 255, cv2.THRESH_BINARY)
            im = Image.fromarray(img.astype(np.uint8))
            im.save(captcha)
            text = pytesseract.image_to_string(im, config='--psm 10', lang="eng")
            text = re.sub('[^A-Za-z0-9]+', '', text)
            driver.find_element_by_id('txtpwd').clear()
            driver.find_element_by_id('txtVerificationCode').clear()
            driver.find_element_by_id('txtVerificationCode').send_keys(text.replace('\x0C', ''))
            driver.find_element_by_id('txtpwd').send_keys('{}'.format(password))
            try:
                driver.find_element_by_id('txtUser').clear()
                driver.find_element_by_id('txtUser').send_keys('{}'.format(username))
                driver.find_element_by_name('btncon').click()
                attempts -= 1
                driver.switch_to.alert.accept()
            except UnexpectedAlertPresentException:
                pass
            except (InvalidElementStateException):
                attempts -= 1
                try:
                    driver.find_element_by_name('btnOk').click()
                except NoSuchElementException:
                    driver.find_element_by_name('btncon').click()
                continue
        except (NoAlertPresentException, NoSuchElementException, UnexpectedAlertPresentException):
            try:
                driver.find_element_by_id('ctl00_Miller_content1_lnkDocnt')
                driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/rptDOScantext.aspx')
                agreement_element = Select(driver.find_element_by_id('ctl00_Miller_content1_ddlagr'))
                agreement_element.select_by_value(agreement)
                do_element = Select(driver.find_element_by_id('ctl00_Miller_content1_ddldo'))
                do_element.select_by_visible_text(do)
                pdf = driver.find_element_by_id('ctl00_Miller_content1_dhidden').get_attribute('value')
                break
            except NoSuchElementException:
                continue
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return pdf


def get_do_status(driver: WebDriver, screenshot: str, captcha: str, username: str, password: str, agreement: str):
    driver.get(start_url)
    attempts = 10
    response = {}
    while True:
        if attempts <= 0:
            break
        try:
            element = driver.find_element_by_id('ImageCaptcha')
            location = element.location
            size = element.size
            driver.save_screenshot(screenshot)
            x = location['x'] * WIDTH_RATIO
            y = location['y'] * HEIGHT_RATIO
            w = size['width'] * WIDTH_RATIO
            h = size['height'] * HEIGHT_RATIO
            width = x + w
            height = y + h
            im = Image.open(screenshot)
            im = im.crop((x, y, width, height))
            im = im.convert('L')
            ret, img = cv2.threshold(np.array(im), 127, 255, cv2.THRESH_BINARY)
            im = Image.fromarray(img.astype(np.uint8))
            im.save(captcha)
            text = pytesseract.image_to_string(im, config='--psm 10', lang="eng")
            text = re.sub('[^A-Za-z0-9]+', '', text)
            driver.find_element_by_id('txtpwd').clear()
            driver.find_element_by_id('txtVerificationCode').clear()
            driver.find_element_by_id('txtVerificationCode').send_keys(text.replace('\x0C', ''))
            driver.find_element_by_id('txtpwd').send_keys('{}'.format(password))
            try:
                driver.find_element_by_id('txtUser').clear()
                driver.find_element_by_id('txtUser').send_keys('{}'.format(username))
                driver.find_element_by_name('btncon').click()
                attempts -= 1
                driver.switch_to.alert.accept()
            except UnexpectedAlertPresentException:
                pass
            except (InvalidElementStateException):
                attempts -= 1
                try:
                    driver.find_element_by_name('btnOk').click()
                except NoSuchElementException:
                    driver.find_element_by_name('btncon').click()
                continue
        except (NoAlertPresentException, NoSuchElementException, UnexpectedAlertPresentException):
            try:
                driver.find_element_by_id('ctl00_Miller_content1_lnkDocnt')
                driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/AgreementReconciliation.aspx')
                agreement_element = Select(driver.find_element_by_id('DDAgreementNo'))
                agreement_element.select_by_value(agreement)
                driver.find_element_by_id('btnshow').click()
                table = driver.find_elements_by_tag_name('table')[2]
                HTML_DOCUMENT = table.get_attribute('outerHTML')
                parser = BeautifulSoup(HTML_DOCUMENT, 'html.parser')
                table: Tag = parser.find_all('table')[0]
                rows = table.find_all('tr')[1:-1]
                do = {}
                remaining = []
                summary = {}
                for i, row in enumerate(rows):
                    if i % 2 == 0:
                        element = row.find_all('td')
                        if float(element[22].text) > 0 or ((float(element[5].text) - float(element[13].text)) > 0) or ((float(element[6].text) - float(element[14].text)) > 0) or ((float(element[10].text) - float(element[18].text)) > 0):
                            remaining.append([elem.text for elem in element])
                        do.setdefault('{}'.format(element[1].find_all('td')[0].text), []).append({
                            "date": element[4].text,
                            "mu": float(element[5].text),
                            "mm": float(element[6].text),
                            "sr": float(element[10].text),
                            "tu": float(element[5].text) + float(element[6].text) + float(element[10].text),
                            "mud": float(element[13].text),
                            "mmd": float(element[14].text),
                            "srd": float(element[18].text),
                            "tud": float(element[13].text) + float(element[14].text) + float(element[18].text),
                            "mus": float(element[5].text) - float(element[13].text),
                            "mms": float(element[6].text) - float(element[14].text),
                            "srs": float(element[10].text) - float(element[18].text),
                            "s": float(element[22].text)
                        })
                for k, v in do.items():
                    df = pd.DataFrame(v)
                    groups = df.groupby('date').sum()
                    do[k] = groups.to_json(orient='index')
                    gps = df[["mu", "mm", "sr", "mud", "mmd", "srd", "mus", "mms", "srs", "s"]].sum()
                    summary[k] = gps.to_json(orient='index')
                response["total"] = do
                response["summary"] = summary
                response["remaining"] = remaining
                break
            except NoSuchElementException:
                continue
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return response


def get_cmr(driver: WebDriver, screenshot: str, captcha: str, username: str, password: str, agreement: str):
    driver.get(start_url)
    attempts = 10
    response = {}
    while True:
        if attempts <= 0:
            break
        try:
            element = driver.find_element_by_id('ImageCaptcha')
            location = element.location
            size = element.size
            driver.save_screenshot(screenshot)
            x = location['x'] * WIDTH_RATIO
            y = location['y'] * HEIGHT_RATIO
            w = size['width'] * WIDTH_RATIO
            h = size['height'] * HEIGHT_RATIO
            width = x + w
            height = y + h
            im = Image.open(screenshot)
            im = im.crop((x, y, width, height))
            im = im.convert('L')
            ret, img = cv2.threshold(np.array(im), 127, 255, cv2.THRESH_BINARY)
            im = Image.fromarray(img.astype(np.uint8))
            im.save(captcha)
            text = pytesseract.image_to_string(im, config='--psm 10', lang="eng")
            text = re.sub('[^A-Za-z0-9]+', '', text)
            driver.find_element_by_id('txtpwd').clear()
            driver.find_element_by_id('txtVerificationCode').clear()
            driver.find_element_by_id('txtVerificationCode').send_keys(text.replace('\x0C', ''))
            driver.find_element_by_id('txtpwd').send_keys('{}'.format(password))
            try:
                driver.find_element_by_id('txtUser').clear()
                driver.find_element_by_id('txtUser').send_keys('{}'.format(username))
                driver.find_element_by_name('btncon').click()
                attempts -= 1
                driver.switch_to.alert.accept()
            except UnexpectedAlertPresentException:
                pass
            except (InvalidElementStateException):
                attempts -= 1
                try:
                    driver.find_element_by_name('btnOk').click()
                except NoSuchElementException:
                    driver.find_element_by_name('btncon').click()
                continue
        except (NoAlertPresentException, NoSuchElementException, UnexpectedAlertPresentException):
            try:
                driver.find_element_by_id('ctl00_Miller_content1_lnkDocnt')
                driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/AgreementReconciliation.aspx')
                agreement_element = Select(driver.find_element_by_id('DDAgreementNo'))
                agreement_element.select_by_value(agreement)
                driver.find_element_by_id('btnshow').click()
                table = driver.find_elements_by_tag_name('table')[374]
                HTML_DOCUMENT = table.get_attribute('outerHTML')
                parser = BeautifulSoup(HTML_DOCUMENT, 'html.parser')
                table: Tag = parser.find_all('table')[0]
                rows = table.find_all('tr')[2:-1]
                cmr = []
                for row in rows:
                    data = row.find_all('td')
                    cmr.append([
                        data[1].text,
                        data[2].text,
                        data[3].text,
                        data[4].text,
                        data[5].text,
                        data[7].text,
                        data[8].text,
                        ''
                    ])
                response = cmr
                break
            except NoSuchElementException:
                continue
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return response

@login_required
@set_mill_session
def get_cmr_status(request: WSGIRequest):
    if request.method == "POST":
        options = Options()
        agreement = request.POST["agreement"]
        firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
        cached_response = cache.get("{}cmr".format(agreement.strip()))
        if cached_response is None or json.loads(cached_response) == {}:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.binary_location = CHROME
            driver = webdriver.Chrome(CHROMEDRIVER, options=options)
            data = get_cmr(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), '{}'.format(firm.username), '{}'.format(firm.password), '{}'.format(agreement))
            cache.set("{}cmr".format(agreement.strip()), json.dumps(data), 60 * 60 * 12)
            return JsonResponse(data, safe=False)
        else:
            data = json.loads(cached_response)
            return JsonResponse(data, safe=False)
    return JsonResponse({
        "error": "Invalid request"
    }, status=500)


@login_required
@set_mill_session
def get_guarantee(request: WSGIRequest):
    options = Options()
    firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
    cached_response = cache.get("{}".format(firm.username))
    if cached_response is None or json.loads(cached_response) == {}:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.binary_location = CHROME
        driver = webdriver.Chrome(CHROMEDRIVER, options=options)
        data = get_captcha(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), '{}'.format(firm.username), '{}'.format(firm.password), request.user.mobile)
        data["conversion"] = firm.conversion
        cache.set("{}".format(firm.username), data, 60 * 60 * 24 * 7)
    else:
        data = cached_response
    return JsonResponse(data)

@login_required
@set_mill_session
def get_print_url(request: WSGIRequest):
    if request.method == "POST":
        options = Options()
        agreement = request.POST["agreement"]
        do = request.POST["do"]
        firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
        cached_response = cache.get("{}-{}".format(agreement.strip(), do))
        if cached_response is None or cached_response == "":
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.binary_location = CHROME
            driver = webdriver.Chrome(CHROMEDRIVER, options=options)
            data = get_print(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), '{}'.format(firm.username), '{}'.format(firm.password), '{}'.format(agreement), '{}'.format(do))
            cache.set("{}-{}".format(agreement.strip(), do), data, 60 * 60 * 24 * 15)
            return HttpResponse(data)
        else:
            data = cached_response
            return HttpResponse(data)
    return HttpResponse("Invalid request data", status=500)

@login_required
@set_mill_session
def get_do_stats(request: WSGIRequest):
    if request.method == "POST":
        options = Options()
        agreement = request.POST["agreement"]
        firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
        cached_response = cache.get("{}-do".format(agreement.strip()))
        if cached_response is None or json.loads(cached_response) == {}:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.binary_location = CHROME
            driver = webdriver.Chrome(CHROMEDRIVER, options=options)
            data = get_do_status(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), '{}'.format(firm.username), '{}'.format(firm.password), '{}'.format(agreement))
            cache.set("{}-do".format(agreement.strip()), data, 60 * 60 * 24 * 1)
            return JsonResponse(data)
        else:
           data = cached_response
           return JsonResponse(data)
    return JsonResponse({
        "error": "Invalid request"
    }, status=500)

@login_required
@set_mill_session
def get_print_view(request: WSGIRequest):
    return render(request, "printer.html")

@login_required
@set_mill_session
def get_do_view(request: WSGIRequest):
    return render(request, "do_stats.html")

@login_required
@set_mill_session
def get_cmr_view(request: WSGIRequest):
    return render(request, "cmr_status.html")

@login_required
@set_mill_session
def guarantee(request: WSGIRequest):
    firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
    return render(request, "guarantee.html")