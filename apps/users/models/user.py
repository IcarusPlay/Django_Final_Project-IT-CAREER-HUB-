from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        LANDLORD = 'landlord', 'Landlord'   # арендодатель — может создавать объявления
        TENANT = 'tenant', 'Tenant'          # арендатор — может бронировать и оставлять отзывы

    phone_validator = RegexValidator(
        regex=r'^\+?[1-9]\d{7,14}$',
        message='Введите номер телефона в формате +49123456789 (от 8 до 15 цифр)'
    )

    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def is_landlord(self):
        return self.role == self.Role.LANDLORD

    def is_tenant(self):
        return self.role == self.Role.TENANT

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
