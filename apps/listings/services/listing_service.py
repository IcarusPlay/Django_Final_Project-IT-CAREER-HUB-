from rest_framework.exceptions import PermissionDenied, NotFound
from apps.listings.repositories import ListingRepository
from apps.listings.filters import ListingFilter


class ListingService:
    @staticmethod
    def get_list(params):
        qs = ListingRepository.get_all()
        listing_filter = ListingFilter(qs, params)
        return listing_filter.apply()

    @staticmethod
    def get_by_id(listing_id):
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise NotFound('Объявление не найдено')
        return listing

    @staticmethod
    def create(owner, validated_data):
        if not owner.is_landlord():
            raise PermissionDenied('Только арендодатели могут создавать объявления')
        return ListingRepository.create(owner, validated_data)

    @staticmethod
    def update(listing, user, validated_data):
        if listing.owner != user:
            raise PermissionDenied('Нельзя редактировать чужое объявление')
        return ListingRepository.update(listing, validated_data)

    @staticmethod
    def delete(listing, user):
        if listing.owner != user:
            raise PermissionDenied('Нельзя удалять чужое объявление')
        ListingRepository.delete(listing)

    @staticmethod
    def toggle_status(listing, user):
        if listing.owner != user:
            raise PermissionDenied('Нельзя менять статус чужого объявления')
        return ListingRepository.toggle_status(listing)
