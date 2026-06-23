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
    def has_confirmed_booking(tenant, listing):
        return Booking.objects.filter(
            tenant=tenant,
            listing=listing,
            status=Booking.CONFIRMED,
        ).exists()

    @staticmethod
    def has_date_conflict(listing, date_from, date_to, exclude_booking_id=None):
        # проверяем пересечение дат с уже существующими бронированиями
        # два отрезка пересекаются если: start1 < end2 AND start2 < end1
        qs = Booking.objects.filter(
            listing=listing,
            status__in=[Booking.PENDING, Booking.CONFIRMED],
        ).filter(
            Q(date_from__lt=date_to) & Q(date_to__gt=date_from)
        )
        if exclude_booking_id:
            qs = qs.exclude(id=exclude_booking_id)
        return qs.exists()
