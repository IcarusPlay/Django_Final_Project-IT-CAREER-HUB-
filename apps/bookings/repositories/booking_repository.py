from django.db.models import Q
from apps.bookings.models import Booking


class BookingRepository:
    @staticmethod
    def get_by_id(booking_id):
        return Booking.objects.select_related('listing', 'tenant').filter(id=booking_id).first()

    @staticmethod
    def get_by_tenant(tenant):
        return Booking.objects.filter(tenant=tenant).select_related('listing')

    @staticmethod
    def get_by_listing(listing):
        return Booking.objects.filter(listing=listing).select_related('tenant')

    @staticmethod
    def get_by_landlord(landlord):
        # все бронирования на объявления, принадлежащие этому арендодателю
        return Booking.objects.filter(listing__owner=landlord).select_related('listing', 'tenant')

    @staticmethod
    def count_pending_for_landlord(landlord):
        return Booking.objects.filter(listing__owner=landlord, status=Booking.PENDING).count()

    @staticmethod
    def create(tenant, listing, date_from, date_to, total_price):
        return Booking.objects.create(
            tenant=tenant,
            listing=listing,
            date_from=date_from,
            date_to=date_to,
            total_price=total_price,
            status=Booking.PENDING,
        )

    @staticmethod
    def set_status(booking, new_status):
        booking.status = new_status
        booking.save()
        return booking

    @staticmethod
    def set_tenant_notified(booking, notified):
        booking.tenant_notified = notified
        booking.save(update_fields=['tenant_notified'])
        return booking

    @staticmethod
    def count_unseen_notifications(tenant):
        return Booking.objects.filter(
            tenant=tenant,
            tenant_notified=False,
            status__in=[Booking.CONFIRMED, Booking.REJECTED],
        ).count()

    @staticmethod
    def mark_all_notified(tenant):
        Booking.objects.filter(tenant=tenant, tenant_notified=False).update(tenant_notified=True)

    @staticmethod
    def has_confirmed_booking(tenant, listing):
        return Booking.objects.filter(
            tenant=tenant,
            listing=listing,
            status=Booking.CONFIRMED,
        ).exists()

    @staticmethod
    def has_date_conflict(listing, date_from, date_to, exclude_booking_id=None, statuses=None):
        # проверяем пересечение дат с уже существующими бронированиями
        # два отрезка пересекаются если: start1 < end2 AND start2 < end1
        if statuses is None:
            statuses = [Booking.PENDING, Booking.CONFIRMED]
        qs = Booking.objects.filter(
            listing=listing,
            status__in=statuses,
        ).filter(
            Q(date_from__lt=date_to) & Q(date_to__gt=date_from)
        )
        if exclude_booking_id:
            qs = qs.exclude(id=exclude_booking_id)
        return qs.exists()

    @staticmethod
    def get_active_date_ranges(listing):
        # занятые диапазоны дат (pending + confirmed) - чтобы фронтенд мог
        # предупредить пользователя ДО отправки запроса, а не после ошибки
        qs = Booking.objects.filter(
            listing=listing,
            status__in=[Booking.PENDING, Booking.CONFIRMED],
        ).values('date_from', 'date_to')
        return list(qs)
