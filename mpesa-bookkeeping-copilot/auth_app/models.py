from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username or str(self.phone_number)