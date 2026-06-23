from apps.listings.models import Listing


class ListingRepository:
    @staticmethod
    def get_all():
        return Listing.objects.select_related('owner').all()

    @staticmethod
    def get_by_id(listing_id):
        return Listing.objects.select_related('owner').filter(id=listing_id).first()

    @staticmethod
    def get_by_owner(owner):
        return Listing.objects.filter(owner=owner)

    @staticmethod
    def create(owner, validated_data):
        return Listing.objects.create(owner=owner, **validated_data)

    @staticmethod
    def update(listing, validated_data):
        for field, value in validated_data.items():
            setattr(listing, field, value)
        listing.save()
        return listing

    @staticmethod
    def delete(listing):
        listing.delete()

    @staticmethod
    def toggle_status(listing):
        from apps.listings.choices import ListingStatus
        if listing.status == ListingStatus.ACTIVE:
            listing.status = ListingStatus.INACTIVE
        else:
            listing.status = ListingStatus.ACTIVE
        listing.save()
        return listing
