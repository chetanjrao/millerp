from accounts.models import User
from core.models import Mill
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)


class IncomingSource(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)


class OutgoingSource(models.Model):
    name = models.CharField(max_length=64)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)


class ProcessingSide(models.Model):
    name = models.CharField(max_length=64)
    mill = models.ForeignKey(to=Mill, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)


class IncomingStockEntry(models.Model):
    date = models.DateField()
    category = models.ForeignKey(
        to=Category, on_delete=models.CASCADE, related_name='incomingstockentrys')
    source = models.ForeignKey(
        to=IncomingSource, on_delete=models.CASCADE, related_name='incomingstockentrys')
    bags = models.FloatField()
    average_weight = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def to_quintal(self):
        return self.bags * 40/100


class OutgoingStockEntry(models.Model):
    stock = models.ForeignKey(to=IncomingStockEntry, on_delete=models.PROTECT)
    category = models.ForeignKey(
        to=Category, on_delete=models.CASCADE, related_name='outgoingstockentrys')
    source = models.ForeignKey(
        to=OutgoingSource, on_delete=models.CASCADE, related_name='outgoingstockentrys')
    bags = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)

    @property
    def to_quintal(self):
        return self.bags * 40/100


class ProcessingSideEntry(models.Model):
    stock = models.ForeignKey(to=IncomingStockEntry, on_delete=models.PROTECT)
    category = models.ForeignKey(
        to=Category, on_delete=models.CASCADE, related_name='processingstockentrys')
    source = models.ForeignKey(
        to=ProcessingSide, on_delete=models.CASCADE, related_name='processingstockentrys')
    bags = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(to=User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)
