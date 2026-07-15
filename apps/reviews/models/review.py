from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'  # user.reviews.all() - все отзывы, оставленные этим пользователем
    )

    # OneToOneField, а не ForeignKey - потому что на ОДНО бронирование может быть
    # максимум ОДИН отзыв (проверяется дополнительно в ReviewService.create() через
    # already_reviewed(), но OneToOneField даёт эту же гарантию и на уровне базы данных:
    # два Review с одинаковым booking_id физически не смогут существовать одновременно).
    #
    # Важный архитектурный момент про 3NF (третью нормальную форму):
    # поле listing здесь СПЕЦИАЛЬНО не хранится напрямую, хотя было бы удобнее для запросов
    # (например Review.objects.filter(listing=x) вместо Review.objects.filter(booking__listing=x)).
    # Причина: listing уже однозначно определяется через booking.listing - то есть если бы
    # мы хранили ещё и listing_id в Review, это было бы дублирование данных, зависящее не от
    # первичного ключа Review, а от другого поля (booking) - это и есть транзитивная зависимость,
    # нарушение 3NF. Чтобы не терять удобство API, listing всё равно виден в JSON-ответе -
    # но это ВЫЧИСЛЯЕМОЕ поле сериализатора (см. ReviewSerializer), а не колонка в базе данных.
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review'  # booking.review - отзыв на конкретную бронь (или ошибка, если его нет)
    )

    # PositiveSmallIntegerField + два валидатора - рейтинг гарантированно от 1 до 5,
    # ни 0, ни 6, ни отрицательное число не пройдут валидацию.
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)  # можно оставить отзыв без текста, только с оценкой

    # Ответ арендодателя на отзыв - реализовано прямо в этой же модели (не отдельной таблицей),
    # потому что на один отзыв возможен максимум один ответ - усложнять схему отдельной моделью
    # ReviewReply было бы избыточно для такого простого случая "один к одному".
    landlord_reply = models.TextField(blank=True, default='')
    replied_at = models.DateTimeField(null=True, blank=True)  # когда был дан ответ (или null, если ответа ещё нет)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # booking.listing.title - вот тут как раз используется цепочка через booking,
        # о которой шла речь выше в комментарии про 3NF
        return f'Review by {self.author.email} on {self.booking.listing.title}'

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']  # сначала свежие отзывы
        verbose_name = 'Review'
