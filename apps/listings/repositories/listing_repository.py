from django.db.models import Count, F
from apps.listings.models import Listing, ListingView, SearchHistory


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

    @staticmethod
    def increment_views(listing):
        # F() выражение — атомарное обновление без race condition
        Listing.objects.filter(id=listing.id).update(views_count=F('views_count') + 1)
        listing.refresh_from_db()
        return listing

    @staticmethod
    def has_viewed(listing, user, session_key):
        # проверяем не смотрел ли уже этот пользователь / анонимная сессия это объявление
        if user and user.is_authenticated:
            return ListingView.objects.filter(listing=listing, user=user).exists()
        if session_key:
            return ListingView.objects.filter(listing=listing, session_key=session_key, user__isnull=True).exists()
        return False

    @staticmethod
    def save_view(listing, user, session_key=None):
        ListingView.objects.create(
            listing=listing,
            user=user if user and user.is_authenticated else None,
            session_key=session_key if not (user and user.is_authenticated) else None,
        )

    @staticmethod
    def save_search(user, keyword):
        if user and user.is_authenticated and keyword:
            SearchHistory.objects.create(user=user, keyword=keyword)

    @staticmethod
    def get_popular_keywords(limit=10):
        # топ ключевых слов по кол-ву поисков
        return (
            SearchHistory.objects
            .values('keyword')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )

    @staticmethod
    def get_search_history(user):
        return SearchHistory.objects.filter(user=user)

    @staticmethod
    def get_distinct_cities():
        # список уникальных городов из уже существующих объявлений —
        # нужен чтобы город, который ввёл арендодатель, сразу появлялся в фильтре поиска
        return (
            Listing.objects
            .exclude(city='')
            .values_list('city', flat=True)
            .distinct()
            .order_by('city')
        )
