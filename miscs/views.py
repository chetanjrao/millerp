import os
import random
import re
import string
from PIL import Image
import cv2
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
import numpy as np
import pytesseract
from selenium import webdriver
from selenium.common.exceptions import InvalidElementStateException, NoAlertPresentException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from core.decorators import set_mill_session
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def get_random_string(length):
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

# Create your views here.
start_url = "https://khadya.cg.nic.in/paddyonline/miller/millmodify19/MillLogin.aspx"
def get_captcha(driver: WebDriver, screenshot: str, captcha: str, username: str, password: str):
    driver.get(start_url)
    data = ''
    while True:
        try:
            element = driver.find_element_by_id('ImageCaptcha')
            location = element.location
            size = element.size
            driver.save_screenshot(screenshot)
            x = location['x'] * 1
            y = location['y'] * 1
            w = size['width'] * 1
            h = size['height'] * 1
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
            try:
                driver.find_element_by_id('txtpwd').clear()
                driver.find_element_by_id('txtVerificationCode').clear()
                driver.find_element_by_id('txtVerificationCode').send_keys(text.replace('\x0C', ''))
                driver.find_element_by_id('txtpwd').send_keys('{}'.format(password))
                try:
                    driver.find_element_by_id('txtUser').clear()
                    driver.find_element_by_id('txtUser').send_keys('{}'.format(username))
                    driver.find_element_by_name('btncon').click()
                    try:
                        driver.switch_to.alert.accept()
                        driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/TypeSecurityCompleteReport.aspx')
                        elem = driver.find_element_by_class_name('SiteText')
                        data = elem.get_attribute('innerHTML')
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
            driver.get('https://khadya.cg.nic.in/paddyonline/miller/millmodify19/TypeSecurityCompleteReport.aspx')
            elem = driver.find_element_by_class_name('SiteText')
            data = elem.get_attribute('innerHTML')
            break
    driver.close()
    os.remove(captcha)
    os.remove(screenshot)
    return data

@login_required
@set_mill_session
def get_guarantee(request: WSGIRequest):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    driver = webdriver.Chrome('/Users/chethanjkulkarni/Downloads/chromedriver', options=options)
    data = get_captcha(driver, '{}.png'.format(get_random_string(8)), '{}.png'.format(get_random_string(8)), 'MA41141', '100141')
    return HttpResponse(data)

@login_required
@set_mill_session
def guarantee(request: WSGIRequest):
    return render(request, "guarantee.html")