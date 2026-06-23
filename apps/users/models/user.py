from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    LANDLORD = 'landlord'
    TENANT = 'tenant'

    ROLE_CHOICES = [
        (LANDLORD, 'Landlord'),   # арендодатель — может создавать объявления
        (TENANT, 'Tenant'),        # арендатор — может бронировать и оставлять отзывы
    ]

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=TENANT)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def is_landlord(self):
        return self.role == self.LANDLORD

    def is_tenant(self):
        return self.role == self.TENANT

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
