from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
class UserManager(BaseUserManager):

    use_in_migrations = True
    
    def _create_user(self, first_name, password=None, *args, **kwargs):
        if password is None:
            password = self.make_random_password()
        user = self.model(first_name=first_name, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, first_name, password=None, *args, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(first_name, password, *args, **kwargs)

    def create_superuser(self, first_name, password=None, *args, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self._create_user(first_name, password, *args, **kwargs)


class User(AbstractUser):
    username = None
    email = None
    mobile = models.CharField(max_length=10, unique=True)

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = [ 'first_name' ]

    objects = UserManager()

    def __str__(self) -> str: return '{} - {}'.format(self.first_name, self.mobile)