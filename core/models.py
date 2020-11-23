from fernet_fields.fields import EncryptedField
from miscs.models import Addon, Bundle, City
from accounts.models import User
from django.db import models
from fernet_fields import EncryptedCharField

# Create your models here.

class Owner(models.Model):
    name = models.CharField(max_length=256)
    addons = models.ManyToManyField(to=Addon)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    
    def __str__(self) -> str: return '{} - {}'.format(self.user.first_name, self.user.mobile)


class Mill(models.Model):
    name = models.CharField(max_length=128)
    address = models.TextField()
    code = models.CharField(max_length=8)
    is_deleted = models.BooleanField(default=False)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    access = models.ManyToManyField(to=User)
    factor = models.FloatField(default=2271)
    ppq = models.FloatField(default=1400)
    owner = models.ForeignKey(to=Owner, on_delete=models.CASCADE)

    def __str__(self) -> str: return self.name

class Firm(models.Model):
    name = models.CharField(max_length=128)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    conversion = models.FloatField(default=67.0)
    username = EncryptedCharField(max_length=64)
    password = EncryptedCharField(max_length=64)
    is_deleted = models.BooleanField(default=False)


class Purchase(models.Model):
    amount = models.FloatField(default=0.0)
    bundle = models.ForeignKey(to=Bundle, on_delete=models.CASCADE)
    owner = models.ForeignKey(to=Owner, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    payment_id = models.CharField(max_length=255, unique=True)
    payment_mode = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.owner.user.mobile


class AddOnPurhase(models.Model):
    amount = models.FloatField(default=0.0)
    addon = models.ForeignKey(to=Addon, on_delete=models.CASCADE)
    owner = models.ForeignKey(to=Owner, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    payment_id = models.CharField(max_length=255, unique=True)
    payment_mode = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

class Transporter(models.Model):
    name = models.CharField(max_length=256)
    mobile = models.CharField(max_length=64)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str: return self.name

class Truck(models.Model):
    number = models.CharField(max_length=256)
    transporter = models.ForeignKey(to=Transporter, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def __str__(self) -> str: return self.number

class cmr(models.Model):
    cmr_no = models.CharField(max_length=36)
    cmr_date = models.DateField()
    center = models.CharField(max_length=256)
    rice = models.FloatField()
    bora = models.FloatField()
    lot_no = models.IntegerField()
    commodity = models.CharField(max_length=512)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

class cmr_entry(models.Model):
    cmr = models.ForeignKey(to=cmr, on_delete=models.PROTECT)
    truck = models.ForeignKey(to=Truck, on_delete=models.CASCADE)
    bags = models.FloatField()
    price = models.FloatField()
    is_deleted = models.BooleanField(default=False)
