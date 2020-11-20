from django.db import models

# Create your models here.
class Addon(models.Model):
    name = models.CharField(max_length=256)
    amount = models.FloatField()
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name 


class Package(models.Model):
    name = models.CharField(max_length=64)
    amount = models.FloatField()
    duration = models.IntegerField(help_text="Months this package will work")

    def __str__(self):
        return '{} - \u20b9{}'.format(self.name, self.amount)


class Bundle(models.Model):
    name = models.CharField(max_length=64)
    addons = models.ManyToManyField(to=Addon)
    mills = models.IntegerField(default=1)
    amount = models.FloatField()
    is_deleted = models.BooleanField(default=False)
    icon = models.CharField(max_length=16)

    def __str__(self):
        return '{} - \u20b9{}'.format(self.name, self.amount)


class Country(models.Model):
    name = models.CharField(max_length=64)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class State(models.Model):
    name = models.CharField(max_length=64)
    country = models.ForeignKey(to=Country, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class CountryCode(models.Model):
    name = models.CharField(max_length=128)
    abbr = models.CharField(max_length=64)
    code = models.CharField(max_length=16)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.abbr, self.code)

class City(models.Model):
    name = models.CharField(max_length=64)
    state = models.ForeignKey(to=State, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name