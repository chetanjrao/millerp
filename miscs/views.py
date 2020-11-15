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
                break
            except NoSuchElementException:
                continue
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return response


@login_required
@set_mill_session
def get_guarantee(request: WSGIRequest):
    options = Options()
    firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
    cached_response = cache.get("{}".format(firm.username))
    if cached_response is None or cached_response is {}:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.binary_location = CHROME
        driver = webdriver.Chrome(CHROMEDRIVER, options=options)
        data = get_captcha(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), '{}'.format(firm.username), '{}'.format(firm.password), request.user.mobile)
        cache.set("{}".format(firm.username), data, 60 * 45)
    else:
        data = cached_response
    return JsonResponse(data)

@login_required
@set_mill_session
def guarantee(request: WSGIRequest):
    firm = Firm.objects.get(pk=request.COOKIES["MERP_FIRM"], is_deleted=False, mill=request.mill)
    return render(request, "guarantee.html")