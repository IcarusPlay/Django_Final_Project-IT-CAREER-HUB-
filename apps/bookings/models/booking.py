from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Booking(models.Model):
    # Константы статусов вынесены отдельными переменными (а не только внутри STATUS_CHOICES),
    # чтобы в остальном коде можно было писать Booking.PENDING вместо строки 'pending' -
    # это защищает от опечаток и облегчает переименование в будущем (поменял в одном месте -
    # обновилось везде).
    PENDING = 'pending'      # заявка создана, ждёт решения арендодателя
    CONFIRMED = 'confirmed'  # арендодатель подтвердил
    CANCELLED = 'cancelled'  # отменено (арендатором или арендодателем)
    REJECTED = 'rejected'    # арендодатель отклонил заявку

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (REJECTED, 'Rejected'),
    ]

    # Здесь СПЕЦИАЛЬНО оставлен on_delete=CASCADE (в отличие от Listing.owner, где стоит SET_NULL).
    # Логика: если объявление реально удалено физически (например, суперадмином напрямую в базе,
    # в обход мягкого удаления) - оставлять "осиротевшие" бронирования без смысла, они всё равно
    # ссылаются на несуществующее жильё. Поэтому тут каскад оправдан.
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='bookings'  # listing.bookings.all() - все брони этого объявления
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'  # user.bookings.all() - все брони этого пользователя
    )

    date_from = models.DateField()
    date_to = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # считается в BookingService при создании
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    # Механизм уведомлений арендатору без отдельной таблицы "Notifications".
    # По умолчанию True - "показывать нечего". Когда BookingService.confirm()/reject()
    # меняет статус, это поле явно сбрасывается в False - значит "у арендатора есть
    # непросмотренное изменение". Фронтенд запрашивает /api/bookings/notifications-count/,
    # считает сколько таких False, и показывает бейдж-циферку. Когда арендатор заходит на
    # страницу бронирований - вызывается mark_notifications_seen(), и все такие записи
    # снова становятся True.
    tenant_notified = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Booking #{self.pk} - {self.listing.title}'

    # clean() - стандартный Django-метод валидации на уровне модели/формы.
    # Вызывается вручную через full_clean() или автоматически в ModelForm.
    # Дублирует то же самое правило что и CheckConstraint ниже, но на уровне Python -
    # полезно если валидация нужна ДО реального сохранения в базу (например в админке).
    def clean(self):
        if self.date_from and self.date_to and self.date_to <= self.date_from:
            raise ValidationError('Дата выезда должна быть позже даты заезда')

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        verbose_name = 'Booking'
        constraints = [
            # CheckConstraint - это правило ЦЕЛОСТНОСТИ ДАННЫХ на уровне самой базы данных
            # (MySQL/PostgreSQL проверит это при любой попытке вставить/обновить строку).
            # Работает даже если кто-то полезет в базу напрямую через SQL-клиент, в обход
            # всего кода Django - именно поэтому это "последний рубеж защиты", а не единственный:
            # то же самое проверяется и в clean() выше, и ещё раз в BookingCreateSerializer.validate(),
            # и в BookingService при создании (проверка пересечения дат с другими бронями).
            models.CheckConstraint(
                condition=models.Q(date_to__gt=models.F('date_from')),
                name='booking_date_to_after_date_from',
            )
        ]
