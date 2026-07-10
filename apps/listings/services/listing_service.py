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
    def get_by_id(listing_id):
        # просто получить объявление, БЕЗ побочных эффектов -
        # используется для редактирования/удаления/отзывов, где счётчик просмотров
        # increment-иться не должен (раньше это было главной причиной бага со скачущими просмотрами)
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise NotFound('Объявление не найдено')
        return listing

    @staticmethod
    def get_by_id_and_track_view(listing_id, request):
        # именно этот метод нужно вызывать только при реальном открытии страницы объявления
        listing = ListingService.get_by_id(listing_id)

        user = request.user if request.user.is_authenticated else None

        # не считаем просмотры самого владельца - он не "посетитель"
        if user and listing.owner_id == user.id:
            return listing

        # дедупликация: один и тот же пользователь / анонимная сессия
        # не накручивает счётчик повторными заходами
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key

        already_viewed = ListingRepository.has_viewed(listing, user, session_key)
        if not already_viewed:
            ListingRepository.save_view(listing, user, session_key)
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

    @staticmethod
    def get_cities():
        return list(ListingRepository.get_distinct_cities())
