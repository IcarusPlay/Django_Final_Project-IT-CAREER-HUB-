from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.listings.choices import PropertyType, ListingStatus


# Кастомный менеджер модели - подменяет поведение Listing.objects.all() и всех похожих запросов.
# Как это работает: Django по умолчанию использует Listing.objects как точку входа для запросов
# к базе. Переопределив get_queryset(), мы говорим "всегда добавляй фильтр is_deleted=False",
# и это применяется АВТОМАТИЧЕСКИ везде в проекте, где используется Listing.objects - не нужно
# в каждом запросе руками дописывать .filter(is_deleted=False).
class ListingManager(models.Manager):
    """По умолчанию скрывает мягко удалённые объявления"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Listing(models.Model):
    # on_delete=SET_NULL вместо CASCADE - важное архитектурное решение.
    # Если бы стоял CASCADE, то при удалении пользователя (арендодателя) ВСЕ его объявления
    # удалились бы вместе с ним автоматически - а вместе с ними пропали бы уже существующие
    # бронирования и отзывы на эти объявления (тоже каскадно). SET_NULL говорит: если владелец
    # удалён - просто обнули поле owner, а само объявление и связанные с ним данные оставь.
    # null=True и blank=True обязательны при SET_NULL - иначе Django не даст полю стать пустым.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings'  # так можно писать user.listings.all() - все объявления пользователя
    )
    title = models.CharField(max_length=200)
    description = models.TextField()

    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)   # необязательное поле
    address = models.CharField(max_length=255, blank=True)    # необязательное поле

    # choices=PropertyType.choices - в базе хранится строка ('apartment'/'house'/...),
    # но Django Admin и DRF автоматически покажут это как выпадающий список с готовыми вариантами.
    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.APARTMENT
    )
    rooms = models.PositiveSmallIntegerField()  # PositiveSmallIntegerField - нельзя ввести отрицательное число комнат

    # MinValueValidator(1) - защита на уровне модели: даже если кто-то попытается создать
    # объект напрямую в Django-консоли (в обход сериализатора), цена меньше 1 не пройдёт валидацию.
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1, message='Цена за ночь должна быть не менее 1')]
    )

    status = models.CharField(
        max_length=20,
        choices=ListingStatus.choices,
        default=ListingStatus.ACTIVE
    )

    # upload_to='listings/' - Django сам создаст папку media/listings/ и положит туда файл
    # с уникальным именем (если имя уже занято - допишет случайный суффикс, чтобы не было конфликтов).
    image = models.ImageField(upload_to='listings/', null=True, blank=True)

    # Счётчик просмотров. Инкрементируется НЕ здесь в модели, а в сервисе (ListingService),
    # с проверкой чтобы один и тот же человек не накручивал счётчик повторными заходами.
    views_count = models.PositiveIntegerField(default=0)

    # --- Мягкое удаление ---
    # Вместо реального DELETE из базы данных, мы просто помечаем запись как удалённую.
    # Зачем: если объявление реально удалить, а на него уже есть бронирования/отзывы (ForeignKey),
    # это может сломать целостность данных или потребует каскадного удаления истории,
    # которую хотелось бы сохранить. Мягкое удаление решает это - данные остаются в базе,
    # просто скрыты из обычных запросов через ListingManager выше.
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)  # когда именно "удалили" - для истории

    created_at = models.DateTimeField(auto_now_add=True)  # проставляется один раз при создании
    updated_at = models.DateTimeField(auto_now=True)       # обновляется при каждом save()

    # Listing.objects - "обычный" менеджер, скрывает удалённые (используется везде по умолчанию).
    # Listing.all_objects - "сырой" менеджер без фильтра, показывает вообще всё, включая удалённые.
    # Используется, например, в Django Admin, чтобы администратор мог увидеть удалённые записи.
    objects = ListingManager()
    all_objects = models.Manager()

    def __str__(self):
        return self.title

    # Переопределяем стандартный метод .delete(). Теперь когда где-то в коде вызывается
    # listing.delete(), вместо реального удаления строки из таблицы просто проставляются
    # is_deleted=True и текущее время. Это и есть механизм мягкого удаления в действии.
    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        db_table = 'listings'
        ordering = ['-created_at']  # по умолчанию сортируем от новых к старым
        verbose_name = 'Listing'
