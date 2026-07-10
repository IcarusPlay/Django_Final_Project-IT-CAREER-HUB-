from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.listings.choices import PropertyType, ListingStatus


class ListingManager(models.Manager):
    """По умолчанию скрывает мягко удалённые объявления"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Listing(models.Model):
    # owner на SET_NULL — при удалении пользователя объявления не удаляются каскадно,
    # просто теряют владельца. Сами объявления удаляются мягко (is_deleted), а не физически.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()

    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    property_type = models.CharField(
        max_length=20,
        choices=PropertyType.choices,
        default=PropertyType.APARTMENT
    )
    rooms = models.PositiveSmallIntegerField()

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

    # фото объявления — необязательное поле
    image = models.ImageField(upload_to='listings/', null=True, blank=True)

    # счётчик просмотров — обновляется при каждом GET запросе
    views_count = models.PositiveIntegerField(default=0)

    # мягкое удаление
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ListingManager()
    all_objects = models.Manager()  # включая удалённые — для админки/отладки

    def __str__(self):
        return self.title

    def delete(self, using=None, keep_parents=False):
        # переопределяем — вместо реального удаления просто помечаем
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        db_table = 'listings'
        ordering = ['-created_at']
        verbose_name = 'Listing'
