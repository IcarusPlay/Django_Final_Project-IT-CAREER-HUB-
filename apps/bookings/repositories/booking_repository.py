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
        # проверяем что арендатор реально снимал это жильё
        return Booking.objects.filter(
            tenant=tenant,
            listing=listing,
            status=Booking.CONFIRMED,
        ).exists()
