from decimal import Decimal
from datetime import date
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from apps.bookings.models import Booking
from apps.bookings.repositories import BookingRepository


# допустимые переходы статусов:
# pending -> confirmed, rejected, cancelled
# confirmed -> cancelled
# rejected и cancelled — финальные статусы, менять нельзя
ALLOWED_TRANSITIONS = {
    Booking.PENDING: [Booking.CONFIRMED, Booking.REJECTED, Booking.CANCELLED],
    Booking.CONFIRMED: [Booking.CANCELLED],
    Booking.REJECTED: [],
    Booking.CANCELLED: [],
}


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

        # проверка что даты не в прошлом
        if date_from < date.today():
            raise ValidationError('Дата начала не может быть в прошлом')

        # проверка пересечения дат с другими бронированиями
        if BookingRepository.has_date_conflict(listing, date_from, date_to):
            raise ValidationError('Выбранные даты уже заняты')

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
    def _check_transition(booking, new_status):
        allowed = ALLOWED_TRANSITIONS.get(booking.status, [])
        if new_status not in allowed:
            raise ValidationError(
                f'Нельзя перевести бронирование из статуса "{booking.status}" в "{new_status}"'
            )

    @staticmethod
    def cancel(booking, user):
        # отменить может арендатор или арендодатель
        if booking.tenant != user and booking.listing.owner != user:
            raise PermissionDenied('Нет прав для отмены этого бронирования')
        BookingService._check_transition(booking, Booking.CANCELLED)
        return BookingRepository.set_status(booking, Booking.CANCELLED)

    @staticmethod
    def confirm(booking, user):
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может подтверждать бронирование')
        BookingService._check_transition(booking, Booking.CONFIRMED)
        return BookingRepository.set_status(booking, Booking.CONFIRMED)

    @staticmethod
    def reject(booking, user):
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может отклонять бронирование')
        BookingService._check_transition(booking, Booking.REJECTED)
        return BookingRepository.set_status(booking, Booking.REJECTED)

    @staticmethod
    def get_my_bookings(tenant):
        return BookingRepository.get_by_tenant(tenant)
