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
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE, related_name='productiontypes')
    is_deleted = models.BooleanField(default=False)
    quantity = models.FloatField(default=0.0)
    include_trading = models.BooleanField(default=False)
    is_mixture = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

class Stock(models.Model):
    bags = models.IntegerField()
    remarks = models.TextField(null=True, blank=True)
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE)
    product = models.ForeignKey(to=ProductionType, on_delete=models.CASCADE, related_name='outgoingproductentrys')
    date = models.DateField()
    is_deleted = models.BooleanField(default=False)

    @property
    def total(self):
        return round(self.bags * self.product.quantity / 100, 2)


class IncomingProductEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.entry.total

class OutgoingProductEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.entry.total

class ProductStock(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.entry.total

class Trading(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.PROTECT)
    price = models.FloatField()
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name='products')
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.entry.total