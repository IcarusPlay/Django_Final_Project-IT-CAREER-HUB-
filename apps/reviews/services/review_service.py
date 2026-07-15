from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from apps.bookings.models import Booking
from apps.reviews.repositories import ReviewRepository


class ReviewService:

    @staticmethod
    def get_by_listing(listing):
        return ReviewRepository.get_by_listing(listing)

    @staticmethod
    def create(author, validated_data):
        booking = validated_data['booking']

        # Отзыв можно оставить только на СВОЁ бронирование - иначе кто угодно мог бы
        # написать отзыв, подставив чужой booking_id
        if booking.tenant != author:
            raise PermissionDenied('Можно оставить отзыв только на своё бронирование')

        # Бронирование должно быть подтверждено арендодателем - на pending/rejected/cancelled
        # бронь отзыв оставить нельзя (человек ещё не заселился/не заселится вообще).
        #
        # Историческая заметка (почему тут нет проверки "дата выезда уже прошла"):
        # изначально было требование - отзыв доступен только ПОСЛЕ окончания срока проживания.
        # Но через интерфейс бронирования нельзя выбрать дату выезда в прошлом (минимальная
        # дата в календаре - сегодня), а значит такое бронирование физически невозможно
        # создать и потом протестировать функцию отзывов. Ограничение убрали - для отзыва
        # достаточно что бронь подтверждена.
        if booking.status != Booking.CONFIRMED:
            raise ValidationError('Отзыв можно оставить только после подтверждённого бронирования')

        # Проверка "один отзыв на одну бронь" - дублирует то же самое, что уже гарантирует
        # OneToOneField в модели Review, но здесь мы можем вернуть человекочитаемую ошибку
        # ДО попытки сохранения (иначе пользователь увидел бы низкоуровневую ошибку базы данных
        # про нарушение uniqueness constraint)
        if ReviewRepository.already_reviewed(booking):
            raise ValidationError('Вы уже оставили отзыв на это бронирование')

        return ReviewRepository.create(
            author=author,
            booking=booking,
            rating=validated_data['rating'],
            comment=validated_data.get('comment', ''),
        )

    @staticmethod
    def delete(review, user):
        # Удалить отзыв может только его автор
        if review.author != user:
            raise PermissionDenied('Нельзя удалять чужой отзыв')
        review.delete()

    @staticmethod
    def reply(review, user, reply_text):
        # Ответить на отзыв может только владелец объявления, к которому относится отзыв.
        # review.booking.listing.owner - вот тут снова видна цепочка связей вместо
        # прямого review.listing.owner (см. комментарий про 3NF в модели Review).
        if review.booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может отвечать на отзыв')
        return ReviewRepository.set_reply(review, reply_text)
