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

def get_random_string(length):
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


start_url = "https://khadya.cg.nic.in/paddyonline/miller/millmodify19/MillLogin.aspx"

def get_captcha(driver: WebDriver, screenshot: str, captcha: str, username: str, password: str):
    driver.get(start_url)
    response = {}
    total_do_lifted = 0
    total_do_pending = 0
    total_do_issued = 0
    total_do_cancelled = 0
    paddy_uplifted = 0
    rice_deposited = 0
    while True:
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
                driver.switch_to.alert.accept()
            except UnexpectedAlertPresentException:
                pass
            except (InvalidElementStateException):
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
                footer = rows[-1].find_all('td')
                bg_secured = round(sum([float(data[3]) for data in bg_secured]), 2)
                response["results"] = body
                response["bg_secured"] = bg_secured
                break
            except NoSuchElementException:
                continue
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return response

@cache_page(60 * 60)
@login_required
@set_mill_session
def get_guarantee(request: WSGIRequest):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.binary_location = CHROME
    driver = webdriver.Chrome(CHROMEDRIVER, options=options)
    data = get_captcha(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), 'MA41141', '100141')
    return JsonResponse(data)

@login_required
@set_mill_session
def guarantee(request: WSGIRequest):
    return render(request, "guarantee.html")


'''
ctl00_Miller_content1_lnkDocnt - Total DO Count
ctl00_Miller_content1_lnkDopending
ctl00_Miller_content1_lnkDoissued
ctl00_Miller_content1_lnkDocancel
ctl00_Miller_content1_lnkpaddylift
ctl00_Miller_content1_lnkricesubmit
'''