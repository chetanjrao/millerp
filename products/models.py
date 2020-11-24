from accounts.models import User
from core.models import Mill, Rice
from django.db import models

# Create your models here.


class ProductCategory(models.Model):
    name = models.CharField(max_length=64)
    rice = models.ForeignKey(to=Rice, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class ProductionType(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE, related_name='productiontypes')
    is_deleted = models.BooleanField(default=False)
    quantity = models.FloatField(default=0.0)
    is_mixture = models.BooleanField(default=False)
    is_external = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class Stock(models.Model):
    bags = models.IntegerField()
    remarks = models.TextField(null=True, blank=True)
    date = models.DateField()
    is_deleted = models.BooleanField(default=False)


class IncomingProductEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE)
    product = models.ForeignKey(to=ProductionType, on_delete=models.CASCADE, related_name='incomingproductentrys')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return round(self.entry.bags * self.product.quantity / 100, 2)

class OutgoingProductEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE)
    product = models.ForeignKey(to=ProductionType, on_delete=models.CASCADE, related_name='outgoingproductentrys')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return round(self.entry.bags * self.product.quantity / 100, 2)

class ProductStock(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE)
    product = models.ForeignKey(to=ProductionType, on_delete=models.CASCADE, related_name='productstocks')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return round(self.entry.bags * self.product.quantity / 100, 2)

class TradingSource(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey(to=ProductCategory, on_delete=models.CASCADE, related_name='tradingsources')
    is_deleted = models.BooleanField(default=False)
    quantity = models.FloatField(default=0.0)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class Trading(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    source = models.ForeignKey(to=TradingSource, on_delete=models.CASCADE)
    price = models.FloatField()
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return round(self.entry.bags * self.source.quantity / 100, 2)