from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


# Кастомная модель пользователя. Наследуемся от AbstractUser, а не пишем с нуля -
# так мы бесплатно получаем всю систему аутентификации Django (хеширование паролей,
# permissions, is_active/is_staff и т.д.), просто расширяя её своими полями.
class User(AbstractUser):

    # TextChoices - это способ Django задать перечисление прямо в модели.
    # Внутри базы данных хранится просто строка ('landlord' или 'tenant'),
    # а в коде можно обращаться через User.Role.LANDLORD - это удобнее и безопаснее,
    # чем хардкодить строки 'landlord' по всему проекту (опечатка сломает всё молча).
    class Role(models.TextChoices):
        LANDLORD = 'landlord', 'Landlord'   # арендодатель - может создавать объявления
        TENANT = 'tenant', 'Tenant'          # арендатор - может бронировать и оставлять отзывы

    # RegexValidator проверяет номер телефона ДО того как он попадёт в базу.
    # Паттерн: необязательный "+", первая цифра не 0, дальше 7-14 цифр.
    # Если пользователь введёт "абвгд" вместо номера - Django сам вернёт понятную ошибку.
    phone_validator = RegexValidator(
        regex=r'^\+?[1-9]\d{7,14}$',
        message='Введите номер телефона в формате +49123456789 (от 8 до 15 цифр)'
    )

    # unique=True - два пользователя не могут зарегистрироваться с одним email.
    # Это же поле мы используем как логин вместо стандартного username (см. USERNAME_FIELD ниже).
    email = models.EmailField(unique=True)

    # blank=True - поле необязательное при регистрации.
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[phone_validator],
    )

    # По умолчанию каждый новый пользователь - арендатор (более безопасный вариант "по умолчанию",
    # чем сразу давать права создавать объявления).
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)

    created_at = models.DateTimeField(auto_now_add=True)

    # Говорим Django: "логинимся по email, а не по username".
    # username всё равно остаётся в модели (наследуется от AbstractUser) и обязателен
    # при создании суперпользователя через createsuperuser, поэтому он в REQUIRED_FIELDS.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        # Как объект User будет выглядеть в консоли/админке - удобнее видеть email, а не "User object (1)"
        return self.email

    # Эти два метода - простой и читаемый способ проверять роль в остальном коде.
    # Вместо user.role == 'landlord' (можно опечататься) везде пишем user.is_landlord().
    def is_landlord(self):
        return self.role == self.Role.LANDLORD

    def is_tenant(self):
        return self.role == self.Role.TENANT

    class Meta:
        db_table = 'users'  # явное имя таблицы в БД (по умолчанию было бы "users_user")
        verbose_name = 'User'
