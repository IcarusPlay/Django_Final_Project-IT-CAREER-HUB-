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

        # защита от двойного подтверждения: если на эти же даты уже есть
        # ДРУГОЕ подтверждённое бронирование этого объявления - подтвердить нельзя
        has_conflict = BookingRepository.has_date_conflict(
            booking.listing,
            booking.date_from,
            booking.date_to,
            exclude_booking_id=booking.id,
            statuses=[Booking.CONFIRMED],
        )
        if has_conflict:
            raise ValidationError(
                'На эти даты уже подтверждено другое бронирование. '
                'Сначала отклоните или отмените конфликтующую заявку.'
            )

        booking = BookingRepository.set_status(booking, Booking.CONFIRMED)
        # арендатор ещё не видел это изменение статуса - появится уведомление
        BookingRepository.set_tenant_notified(booking, False)
        return booking

    @staticmethod
    def reject(booking, user):
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может отклонять бронирование')
        BookingService._check_transition(booking, Booking.REJECTED)
        booking = BookingRepository.set_status(booking, Booking.REJECTED)
        BookingRepository.set_tenant_notified(booking, False)
        return booking

    @staticmethod
    def get_my_bookings(tenant):
        return BookingRepository.get_by_tenant(tenant)

    @staticmethod
    def get_incoming_bookings(landlord):
        # заявки на бронирование объявлений этого арендодателя
        return BookingRepository.get_by_landlord(landlord)

    @staticmethod
    def get_pending_count(landlord):
        if not landlord.is_landlord():
            return 0
        return BookingRepository.count_pending_for_landlord(landlord)

    @staticmethod
    def get_unseen_notifications_count(tenant):
        if not tenant.is_tenant():
            return 0
        return BookingRepository.count_unseen_notifications(tenant)

    @staticmethod
    def mark_notifications_seen(tenant):
        BookingRepository.mark_all_notified(tenant)

    @staticmethod
    def get_booked_ranges(listing):
        # список занятых диапазонов дат (pending + confirmed) - для проверки на фронтенде
        # ДО отправки запроса, чтобы пользователь сразу видел что даты заняты
        return BookingRepository.get_active_date_ranges(listing)
