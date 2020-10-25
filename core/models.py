from accounts.models import User
from django.db import models

# Create your models here.
class Mill(models.Model):
    name = models.CharField(max_length=128)
    address = models.TextField()
    access = models.ManyToManyField(to=User)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str: return self.name