from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.
class UserManager(BaseUserManager):

    use_in_migrations = True
    
    def _create_user(self, first_name, password, *args, **kwargs):
        user = self.model(first_name=first_name, *args, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, first_name, password, *args, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(first_name, password, *args, **kwargs)

    def create_superuser(self, first_name, password, *args, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self._create_user(first_name, password, *args, **kwargs)


class User(AbstractUser):
    username = None
    email = None
    mobile = models.CharField(max_length=16, unique=True)
    ROLES = (
        (1, 'Staff'),
        (2, 'Mill Manager'),
        (3, 'Owner'),
        (4, 'Support Staff'),
        (5, 'Administrator')
    )
    role = models.IntegerField(choices=ROLES, default=3)
    is_mobile_verified = models.BooleanField(default=False)
    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = [ 'first_name', 'password' ]

    objects = UserManager()

    def __str__(self) -> str: return '{} - {}'.format(self.first_name, self.mobile)

class OTP(models.Model):
    mobile = models.CharField(max_length=16)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now=True, null=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return self.otp

    class Meta:
        verbose_name = "OTP"