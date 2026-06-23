from decimal import Decimal
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from apps.bookings.models import Booking
from apps.bookings.repositories import BookingRepository


class BookingService:
    @staticmethod
    def create(tenant, validated_data):
        if not tenant.is_tenant():
            raise PermissionDenied('Только арендаторы могут создавать бронирования')

        listing = validated_data['listing']

        if listing.owner == tenant:
            raise ValidationError('Нельзя забронировать собственное объявление')

        date_from = validated_data['date_from']
        date_to = validated_data['date_to']

        # считаем стоимость
        days = (date_to - date_from).days
        total_price = Decimal(days) * listing.price_per_night

        return BookingRepository.create(tenant, listing, date_from, date_to, total_price)

    @staticmethod
    def get_by_id(booking_id):
        booking = BookingRepository.get_by_id(booking_id)
        if not booking:
            raise NotFound('Бронирование не найдено')
        return booking

    @staticmethod
    def cancel(booking, user):
        # отменить может только сам арендатор
        if booking.tenant != user:
            raise PermissionDenied('Нельзя отменить чужое бронирование')
        if booking.status != Booking.PENDING:
            raise ValidationError('Можно отменить только бронирование в статусе pending')
        return BookingRepository.set_status(booking, Booking.CANCELLED)

    @staticmethod
    def confirm(booking, user):
        # подтвердить/отклонить может только владелец объявления
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может подтверждать бронирование')
        return BookingRepository.set_status(booking, Booking.CONFIRMED)

    @staticmethod
    def reject(booking, user):
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может отклонять бронирование')
        return BookingRepository.set_status(booking, Booking.REJECTED)

    @staticmethod
    def get_my_bookings(tenant):
        return BookingRepository.get_by_tenant(tenant)
