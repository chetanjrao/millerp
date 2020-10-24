from django.db import models

# Create your models here.
class Mill(models.Model):
    name = models.CharField(max_length=128)
    address = models.TextField()