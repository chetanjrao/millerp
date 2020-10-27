from accounts.models import User
from core.models import Mill
from django.db import models

# Create your models here.


class ProductCategory(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)


class ProductionType(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey(
        to=ProductCategory, on_delete=models.CASCADE, related_name='productiontypes')
    is_deleted = models.BooleanField(default=False)
    quantity = models.FloatField(default=0.0)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)


class IncomingProductEntry(models.Model):
    date = models.DateField()
    category = models.ForeignKey(
        to=ProductCategory, on_delete=models.CASCADE, related_name='incomingproductentrys')
    product_type = models.ForeignKey(
        to=ProductionType, on_delete=models.CASCADE, related_name='incomingproductentrys')
    bags = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def to_quintal(self):
        return (self.bags*self.product_type.quantity)/100


class OutgoingProductEntry(models.Model):
    date = models.DateField(auto_now=True)
    product = models.ForeignKey(
        to=IncomingProductEntry, on_delete=models.PROTECT)
    category = models.ForeignKey(
        to=ProductCategory, on_delete=models.CASCADE, related_name='outgoingproductentrys')
    product_type = models.ForeignKey(
        to=ProductionType, on_delete=models.CASCADE, related_name='outgoingproductentrys')
    bags = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def to_quintal(self):
        return (self.bags*self.product_type.quantity)/100
