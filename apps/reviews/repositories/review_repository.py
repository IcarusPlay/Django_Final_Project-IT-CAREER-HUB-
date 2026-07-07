from apps.reviews.models import Review


class ReviewRepository:
    @staticmethod
    def get_by_listing(listing):
        # listing больше не хранится в Review напрямую - фильтруем через связь booking__listing
        return Review.objects.filter(booking__listing=listing).select_related('author', 'booking')

    @staticmethod
    def get_by_id(review_id):
        return Review.objects.select_related('author', 'booking', 'booking__listing').filter(id=review_id).first()

    @staticmethod
    def already_reviewed(booking):
        # проверяем что на это бронирование ещё нет отзыва
        return Review.objects.filter(booking=booking).exists()

    @staticmethod
    def create(author, booking, rating, comment):
        return Review.objects.create(
            author=author,
            booking=booking,
            rating=rating,
            comment=comment,
        )
