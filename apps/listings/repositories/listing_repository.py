from django.db.models import Count
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
        from django.db.models import F
        Listing.objects.filter(id=listing.id).update(views_count=F('views_count') + 1)
        listing.refresh_from_db()
        return listing

    @staticmethod
    def save_view(listing, user):
        ListingView.objects.create(
            listing=listing,
            user=user if user and user.is_authenticated else None
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
