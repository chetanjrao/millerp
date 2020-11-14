from core.decorators import set_mill_session
from miscs.models import Addon, Bundle, City
from core.models import Mill, Owner, Purchase
from django.shortcuts import render
from millerp.decorators import check_owner_role
from razorpay import Client
from django.shortcuts import render, redirect, resolve_url
from accounts.models import User, OTP
from django.utils.timezone import datetime, now, timedelta, timezone
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from millerp.utils import send_message
from random import randint

# Create your views here.
client = Client(auth=('rzp_test_PUQZgR1zUzYchX', 'TLtW0LE0p8WGJyCYlZxAeDU5'))

@login_required
def home(request):
    return redirect(resolve_url('index'))

@login_required
@check_owner_role
def index(request):
    success = request.GET.get("success", 0)
    mill_success = request.GET.get("done", 0)
    owner = Owner.objects.get(user=request.user)
    addons = Addon.objects.filter(is_deleted=False)
    purchase = Purchase.objects.filter(owner=owner)
    bundles = Bundle.objects.filter(is_deleted=False)
    mills = Mill.objects.filter(owner=owner, is_deleted=False)
    cities = City.objects.all()
    if request.method == "POST":
        name = request.POST["name"]
        city = City.objects.get(pk=request.POST["city"])
        address = request.POST["address"]
        owner = Owner.objects.get(user=request.user)
        while True:
            code = randint(100000, 999999)
            try:
                Mill.objects.get(code=code)
                return
            except Mill.DoesNotExist:
                break
        mill = Mill(name=name, city=city, address=address, owner=owner, code=code)
        mill.save()
        mill.access.add(request.user)
        mill.save()
        return redirect(resolve_url('index') + '?done=1')
    return render(request, "home/index.html", { "owner": owner, "bundles": bundles, "addons": addons, "purchase": len(purchase) > 0, "mills": mills, "success": success, "cities": cities, "mill_success": mill_success })

@login_required
def payment_process(request, bundle: int):
    bundle = Bundle.objects.get(pk=bundle, is_deleted=False)
    owner = Owner.objects.get(user=request.user)
    order = client.order.create(dict(amount=bundle.amount * 100, currency='INR', payment_capture='1'))
    if request.method == "POST":
        payment_id = request.POST["payment_id"]
        order_id = request.POST["order_id"]
        Purchase.objects.create(amount=bundle.amount, payment_id=payment_id, order_id=order_id, bundle=bundle, owner=owner)
        return redirect(resolve_url('index') + '?success=1')
    return render(request, "home/paymentprocess.html", { "order_id": order["id"], "bundle": bundle, "owner": owner })

def register(request):
    if request.method == "POST":
        mobile = request.POST["mobile"]
        name = request.POST["name"]
        firm_name = request.POST["firm_name"]
        mobile_check = User.objects.filter(mobile='+91{}'.format(mobile))
        if len(mobile_check) > 0:
            return render(request, "home/register.html", { "error_message": "User already exists with this mobile number" })
        user = User.objects.create(mobile='+91{}'.format(mobile), first_name=name)
        Owner.objects.create(user=user, name=firm_name)
        current_time = now()
        expiry = current_time + timedelta(minutes=5)
        otp = randint(1000, 9999)
        OTP.objects.create(mobile='+91{}'.format(mobile), otp=otp, expires_at=expiry)
        send_message('Your MillERP verification code is {}'.format(otp), mobile[-10:])
        return redirect(resolve_url('verify') + '?access={}'.format(mobile))
    return render(request, "home/register.html")


def handler404(request, exception):
    return render(request, 'notfound.html', status=404)


def handler500(request):
    return render(request, 'error.html', status=500)


def mlogin(request):
    if request.method == "POST":
        mobile = request.POST["mobile"]
        mobile_check = User.objects.filter(mobile='+91{}'.format(mobile))
        if len(mobile_check) == 0:
            return render(request, "home/login.html", { "error_message": "User does not exist" })
        user = User.objects.get(mobile='+91{}'.format(mobile))
        owner_check = Owner.objects.filter(user=user)
        if len(owner_check) == 0:
            return render(request, "home/login.html", { "error_message": "Owner does not exist" })
        current_time = now()
        expiry = current_time + timedelta(minutes=5)
        otp = randint(1000, 9999)
        OTP.objects.create(mobile='+91{}'.format(mobile), otp=otp, expires_at=expiry)
        send_message('Your MillERP verification code is {}'.format(otp), mobile[-10:])
        return redirect(resolve_url('login_verify') + '?access={}'.format(mobile))
    return render(request, "home/login.html")

def login_verify(request):
    mobile = request.GET.get("access", None)
    if mobile is None:
        return redirect('login')
    if request.method == "POST":
        otp = request.POST["otp"]
        current_time = now()
        otp_doc = OTP.objects.filter(mobile='+91{}'.format(mobile), otp=otp, expires_at__gt=current_time, is_used=False)
        if len(otp_doc) > 0:
            otp_doc.update(is_used=True)
            user = User.objects.get(mobile='+91{}'.format(mobile))
            login(request, user)
            return redirect('index')
        else:
            return render(request, "home/login_verify.html", { "error_message": "Invalid verification code" })
    return render(request, "home/login_verify.html", { "success_message": "Verification code sent to your mobile" })

def mlogout(request):
    logout(request)
    return redirect(resolve_url('login'))

def verify(request):
    mobile = request.GET.get("access", None)
    if mobile is None:
        return redirect('register')
    if request.method == "POST":
        otp = request.POST["otp"]
        current_time = now()
        otp_doc = OTP.objects.filter(mobile='+91{}'.format(mobile), otp=otp, expires_at__gt=current_time, is_used=False)
        if len(otp_doc) > 0:
            otp_doc.update(is_used=True)
            user = User.objects.get(mobile='+91{}'.format(mobile))
            user.is_mobile_verified = True
            user.save()
            login(request, user)
            return redirect('index')
        else:
            return render(request, "home/verify.html", { "error_message": "Invalid verification code" })
    return render(request, "home/verify.html", { "success_message": "Verification code sent to your mobile" })

@login_required
@set_mill_session
def profile(request):
    user = User.objects.get(pk=request.user.pk, is_active=True)
    if request.method == "POST":
        user: User = User.objects.get(pk=request.user.pk, is_active=True)
        first_name = request.POST["first_name"]
        last_name = request.POST.get("last_name", '')
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return render(request, "profile.html", { "user": user, "success_message": "Profile updated successfully" })    
    return render(request, "profile.html", { "user": user })