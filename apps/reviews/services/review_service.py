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

        # только арендатор этого бронирования может оставить отзыв
        if booking.tenant != author:
            raise PermissionDenied('Можно оставить отзыв только на своё бронирование')

        # бронирование должно быть подтверждённым
        if booking.status != Booking.CONFIRMED:
            raise ValidationError('Отзыв можно оставить только после подтверждённого бронирования')

        # один отзыв на одно бронирование
        if ReviewRepository.already_reviewed(booking):
            raise ValidationError('Вы уже оставили отзыв на это бронирование')

        return ReviewRepository.create(
            author=author,
            listing=booking.listing,
            booking=booking,
            rating=validated_data['rating'],
            comment=validated_data.get('comment', ''),
        )

    @staticmethod
    def delete(review, user):
        if review.author != user:
            raise PermissionDenied('Нельзя удалять чужой отзыв')
        review.delete()
