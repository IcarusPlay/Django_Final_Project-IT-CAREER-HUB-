from apps.reviews.models import Review


class ReviewRepository:
    @staticmethod
    def get_by_listing(listing):
        return Review.objects.filter(listing=listing).select_related('author', 'booking')

    @staticmethod
    def get_by_id(review_id):
        return Review.objects.select_related('author', 'listing', 'booking').filter(id=review_id).first()

    @staticmethod
    def already_reviewed(booking):
        # проверяем что на это бронирование ещё нет отзыва
        return Review.objects.filter(booking=booking).exists()

    @staticmethod
    def create(author, listing, booking, rating, comment):
        return Review.objects.create(
            author=author,
            listing=listing,
            booking=booking,
            rating=rating,
            comment=comment,
        )
