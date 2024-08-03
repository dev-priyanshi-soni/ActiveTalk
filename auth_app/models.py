from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)
        
    def create_manager_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_manager', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractUser):
   
    email = models.EmailField(null=True,blank=True)
    full_name=models.CharField(max_length=300,null=True,blank=True)
    is_manager = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.username:
            # If username is not set, set it to email or phone number
            self.username = self.email or self.phone_number
        super().save(*args, **kwargs)
