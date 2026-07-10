from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Booking(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (REJECTED, 'Rejected'),
    ]

    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    date_from = models.DateField()
    date_to = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    # видел ли арендатор уведомление об изменении статуса этой заявки
    # (True по умолчанию - "нечего показывать"; сбрасывается в False при confirm/reject,
    # чтобы арендатор увидел уведомление один раз, потом отметится как просмотренное)
    tenant_notified = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Booking #{self.pk} - {self.listing.title}'

    def clean(self):
        # проверка на уровне модели/формы — сработает при full_clean()
        if self.date_from and self.date_to and self.date_to <= self.date_from:
            raise ValidationError('Дата выезда должна быть позже даты заезда')

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        verbose_name = 'Booking'
        constraints = [
            # проверка на уровне БД — сработает при любом INSERT/UPDATE, даже в обход Django
            models.CheckConstraint(
                condition=models.Q(date_to__gt=models.F('date_from')),
                name='booking_date_to_after_date_from',
            )
        ]
