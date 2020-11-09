from miscs.models import Addon, Bundle, City
from accounts.models import User
from django.db import models
from fernet_fields import EncryptedCharField

# Create your models here.

class Owner(models.Model):
    name = models.CharField(max_length=256)
    addons = models.ManyToManyField(to=Addon)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)


class Mill(models.Model):
    name = models.CharField(max_length=128)
    address = models.TextField()
    code = models.CharField(max_length=8)
    mill_username = models.CharField(null=True, max_length=64, blank=True)
    mill_password = EncryptedCharField(null=True, max_length=64, blank=True)
    is_deleted = models.BooleanField(default=False)
    city = models.ForeignKey(City, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)
    access = models.ManyToManyField(to=User)
    owner = models.ForeignKey(to=Owner, on_delete=models.PROTECT)

    def __str__(self) -> str: return self.name

class Purchase(models.Model):
    amount = models.FloatField(default=0.0)
    bundle = models.ForeignKey(to=Bundle, on_delete=models.PROTECT)
    owner = models.ForeignKey(to=Owner, on_delete=models.PROTECT)
    order_id = models.CharField(max_length=255, unique=True)
    payment_id = models.CharField(max_length=255, unique=True)
    payment_mode = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.owner.user.mobile


class AddOnPurhase(models.Model):
    amount = models.FloatField(default=0.0)
    addon = models.ForeignKey(to=Addon, on_delete=models.PROTECT)
    owner = models.ForeignKey(to=Owner, on_delete=models.PROTECT)
    order_id = models.CharField(max_length=255, unique=True)
    payment_id = models.CharField(max_length=255, unique=True)
    payment_mode = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True, null=True)