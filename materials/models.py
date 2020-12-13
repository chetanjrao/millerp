from accounts.models import User
from core.models import Mill, Rice
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)


class Bag(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)


class IncomingSource(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    include_trading = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)


class OutgoingSource(models.Model):
    name = models.CharField(max_length=64)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)


class ProcessingSide(models.Model):
    name = models.CharField(max_length=64)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    rice = models.ForeignKey(to=Rice, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class Customer(models.Model):
    name = models.CharField(max_length=64)
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class Stock(models.Model):
    bags = models.IntegerField()
    quantity = models.FloatField()
    remarks = models.TextField(null=True, blank=True)
    date = models.DateField()
    is_deleted = models.BooleanField(default=False)

    @property
    def average_weight(self):
        return 0 if self.bags == 0 else round(self.quantity * 100 / self.bags, 2)

class IncomingStockEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, related_name='stocks')
    dmo_weight = models.FloatField(default=0)
    bag = models.ForeignKey(to=Bag, null=True, on_delete=models.CASCADE)
    source = models.ForeignKey(to=IncomingSource, on_delete=models.CASCADE, related_name='incomingstockentrys')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def difference(self):
        return round(self.dmo_weight - self.entry.quantity, 2)

class OutgoingStockEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, related_name='outgoingstockentrys')
    source = models.ForeignKey(to=OutgoingSource, on_delete=models.CASCADE, related_name='outgoingstockentrys')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class ProcessingSideEntry(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE, related_name='processingsideentrys')
    source = models.ForeignKey(to=ProcessingSide, on_delete=models.CASCADE, related_name='processingsideentrys')
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

class Trading(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    price = models.FloatField()
    mill = models.ForeignKey(to=Mill, on_delete=models.CASCADE)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='materials')
    created_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return round(self.price * self.entry.quantity, 2)

class Sale(models.Model):
    entry = models.ForeignKey(to=Stock, on_delete=models.CASCADE)
    customer = models.ForeignKey(to=Customer, on_delete=models.CASCADE)
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE)
    source = models.ForeignKey(to=OutgoingSource, on_delete=models.CASCADE)
    price = models.FloatField()
    ppq = models.FloatField()
    gst = models.FloatField(default=0)
    created_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def taxable_amount(self):
        return round(self.ppq * self.entry.quantity, 2)

    @property
    def tax(self):
        return self.taxable_amount * self.gst / 100

    @property
    def total(self):
        return self.taxable_amount + self.tax