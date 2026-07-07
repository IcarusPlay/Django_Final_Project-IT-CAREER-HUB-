from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    # отзыв можно оставить только если было подтверждённое бронирование.
    # listing здесь не хранится отдельно - его всегда можно получить через booking.listing,
    # так как для 3NF нельзя хранить значение, зависящее не от PK, а от другого поля (booking)
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review by {self.author.email} on {self.booking.listing.title}'

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        verbose_name = 'Review'
