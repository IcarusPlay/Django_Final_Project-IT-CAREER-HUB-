from decimal import Decimal
from datetime import date
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from apps.bookings.models import Booking
from apps.bookings.repositories import BookingRepository
from apps.listings.choices import ListingStatus


# Словарь "конечного автомата" (state machine) для статусов бронирования.
# Ключ - текущий статус, значение - список статусов, в которые МОЖНО перейти из него.
# Например, из PENDING можно уйти в CONFIRMED, REJECTED или CANCELLED,
# а вот из CONFIRMED - только в CANCELLED (нельзя "передумать" и вернуть в PENDING,
# и нельзя подтверждённую бронь вдруг отклонить - это нелогично с точки зрения бизнеса).
# REJECTED и CANCELLED - финальные состояния, из них вообще никуда перейти нельзя.
# Такой подход явно документирует всю логику переходов в одном месте, вместо того чтобы
# раскидывать проверки if по разным методам - сразу видно всю "карту" допустимых состояний.
ALLOWED_TRANSITIONS = {
    Booking.PENDING: [Booking.CONFIRMED, Booking.REJECTED, Booking.CANCELLED],
    Booking.CONFIRMED: [Booking.CANCELLED],
    Booking.REJECTED: [],
    Booking.CANCELLED: [],
}


class BookingService:

    @staticmethod
    def create(tenant, validated_data):
        # Только пользователь с ролью "арендатор" может создавать бронирования -
        # арендодатель не должен бронировать чужое (или своё) жильё через этот же механизм.
        if not tenant.is_tenant():
            raise PermissionDenied('Только арендаторы могут создавать бронирования')

        listing = validated_data['listing']

        # БАГ КОТОРЫЙ ЧИНИМ: раньше здесь не было проверки статуса объявления вообще -
        # можно было забронировать даже объявление, которое арендодатель выключил
        # через toggle (status=inactive), то есть намеренно скрыл с публикации.
        # Скрытое объявление не должно быть доступно для бронирования вообще -
        # оно не показывается даже в общем списке (см. ListingFilter.add_filters,
        # там тоже фильтр status=ACTIVE), значит и создать бронь на него нельзя.
        if listing.status != ListingStatus.ACTIVE:
            raise ValidationError('Это объявление сейчас недоступно для бронирования')

        # Защита от абсурдной ситуации: арендодатель по ошибке бронирует своё же объявление
        if listing.owner == tenant:
            raise ValidationError('Нельзя забронировать собственное объявление')

        date_from = validated_data['date_from']
        date_to = validated_data['date_to']

        # Нельзя бронировать "задним числом"
        if date_from < date.today():
            raise ValidationError('Дата начала не может быть в прошлом')

        # Главная защита от двойного бронирования - проверяем что на выбранные даты
        # ещё нет ни одной чужой заявки в статусе pending ИЛИ confirmed для этого же
        # объявления (см. BookingRepository.has_date_conflict). Если конфликт есть -
        # создание бронирования вообще не происходит, пользователь сразу получает ошибку.
        if BookingRepository.has_date_conflict(listing, date_from, date_to):
            raise ValidationError('Выбранные даты уже заняты')

        # Считаем итоговую стоимость: количество ночей * цена за ночь.
        # (date_to - date_from) в Python для дат возвращает timedelta, .days - число дней.
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
        # Метод с подчёркиванием в начале - соглашение Python "это внутренний метод класса,
        # снаружи его вызывать не предполагается". Проверяем текущий статус брони против
        # словаря ALLOWED_TRANSITIONS выше - если перехода в new_status там нет, значит
        # он запрещён бизнес-логикой (например, попытка подтвердить уже отклонённую заявку).
        allowed = ALLOWED_TRANSITIONS.get(booking.status, [])
        if new_status not in allowed:
            raise ValidationError(
                f'Нельзя перевести бронирование из статуса "{booking.status}" в "{new_status}"'
            )

    @staticmethod
    def cancel(booking, user):
        # Отменить бронирование могут ОБА участника сделки - и арендатор (передумал),
        # и арендодатель (не может больше сдать жильё). А вот confirm/reject - только
        # арендодатель, это видно ниже по разным проверкам прав в каждом методе.
        if booking.tenant != user and booking.listing.owner != user:
            raise PermissionDenied('Нет прав для отмены этого бронирования')
        BookingService._check_transition(booking, Booking.CANCELLED)
        return BookingRepository.set_status(booking, Booking.CANCELLED)

    @staticmethod
    def confirm(booking, user):
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может подтверждать бронирование')
        BookingService._check_transition(booking, Booking.CONFIRMED)

        # Дополнительная (вторая) линия защиты от двойного бронирования - помимо проверки
        # при создании (см. create() выше). Зачем нужна ещё одна проверка именно здесь:
        # теоретически могут существовать ДВЕ разные заявки с ПЕРЕСЕКАЮЩИМИСЯ, но не полностью
        # одинаковыми датами (обе прошли проверку при создании, если создавались до того как
        # первая стала confirmed). Перед тем как реально подтвердить бронь, ещё раз проверяем -
        # не появилось ли за это время ДРУГОЕ уже подтверждённое бронирование с пересекающимися
        # датами. exclude_booking_id=booking.id - исключаем саму эту бронь из проверки,
        # иначе она бы "конфликтовала сама с собой".
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
        # Сбрасываем tenant_notified в False - арендатор ещё не видел что его заявку
        # подтвердили, фронтенд покажет ему уведомление при следующей загрузке страницы
        BookingRepository.set_tenant_notified(booking, False)
        return booking

    @staticmethod
    def reject(booking, user):
        if booking.listing.owner != user:
            raise PermissionDenied('Только владелец объявления может отклонять бронирование')
        BookingService._check_transition(booking, Booking.REJECTED)
        booking = BookingRepository.set_status(booking, Booking.REJECTED)
        # Так же как и при confirm() - уведомляем арендатора об изменении статуса
        BookingRepository.set_tenant_notified(booking, False)
        return booking

    @staticmethod
    def get_my_bookings(tenant):
        return BookingRepository.get_by_tenant(tenant)

    @staticmethod
    def get_incoming_bookings(landlord):
        # Заявки НА объявления этого арендодателя (а не его собственные брони - арендодатель
        # сам не бронирует, он получает заявки от арендаторов)
        return BookingRepository.get_by_landlord(landlord)

    @staticmethod
    def get_pending_count(landlord):
        # Если вызвать этот метод для арендатора по ошибке - вернём просто 0, а не будем
        # падать с ошибкой. Проверка is_landlord() тут скорее защита "на всякий случай".
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
        # Вызывается когда арендатор открывает страницу "Мои бронирования" -
        # все непросмотренные уведомления (tenant_notified=False) помечаются просмотренными
        BookingRepository.mark_all_notified(tenant)

    @staticmethod
    def get_booked_ranges(listing):
        # Отдаёт список занятых диапазонов дат ДО того как пользователь попытается
        # отправить запрос на бронирование - фронтенд может сразу предупредить
        # "эти даты уже заняты", не дожидаясь ответа сервера с ошибкой
        return BookingRepository.get_active_date_ranges(listing)
