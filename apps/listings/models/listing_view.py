from django.db import models
from django.conf import settings


class ListingView(models.Model):
    """История просмотров — кто и когда смотрел объявление"""
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # аноним тоже может смотреть
        related_name='listing_views'
    )
    # для анонимных пользователей дедуплицируем по session_key,
    # чтобы один и тот же посетитель не накручивал счётчик за одну сессию
    session_key = models.CharField(max_length=40, null=True, blank=True)

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'listing_views'
        ordering = ['-viewed_at']
