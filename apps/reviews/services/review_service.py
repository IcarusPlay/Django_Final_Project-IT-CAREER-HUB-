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

        # только арендатор этого бронирования
        if booking.tenant != author:
            raise PermissionDenied('Можно оставить отзыв только на своё бронирование')

        # бронирование должно быть подтверждённым владельцем -
        # раньше тут ещё требовалось чтобы дата выезда уже прошла, но через интерфейс
        # нельзя выбрать прошедшую дату при бронировании (мин. дата - сегодня), из-за чего
        # отзыв было физически невозможно протестировать/оставить. Убрали это ограничение.
        if booking.status != Booking.CONFIRMED:
            raise ValidationError('Отзыв можно оставить только после подтверждённого бронирования')

        # один отзыв на одно бронирование
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
        if review.author != user:
            raise PermissionDenied('Нельзя удалять чужой отзыв')
        review.delete()

    @staticmethod
    def reply(review, user, reply_text):
        # ответить может только владелец объявления, к которому относится отзыв
        if review.booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может отвечать на отзыв')
        return ReviewRepository.set_reply(review, reply_text)
