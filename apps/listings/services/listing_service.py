from rest_framework.exceptions import PermissionDenied, NotFound
from apps.listings.repositories import ListingRepository
from apps.listings.filters import ListingFilter


class ListingService:
    @staticmethod
    def get_list(params, user=None):
        qs = ListingRepository.get_all()
        listing_filter = ListingFilter(qs, params)
        result = listing_filter.apply()

        # сохраняем поисковый запрос в историю
        search = params.get('search')
        if search and user:
            ListingRepository.save_search(user, search)

        return result

    @staticmethod
    def get_by_id(listing_id, user=None):
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise NotFound('Объявление не найдено')

        # записываем просмотр и увеличиваем счётчик
        ListingRepository.save_view(listing, user)
        listing = ListingRepository.increment_views(listing)

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

    @staticmethod
    def get_my_listings(user):
        return ListingRepository.get_by_owner(user)

    @staticmethod
    def get_popular_keywords():
        return ListingRepository.get_popular_keywords()

    @staticmethod
    def get_search_history(user):
        return ListingRepository.get_search_history(user)
