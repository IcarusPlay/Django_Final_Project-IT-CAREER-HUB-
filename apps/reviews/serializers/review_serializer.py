from rest_framework import serializers
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)
    # listing больше не хранится в модели напрямую - берём его через booking.listing_id
    # только для чтения, чтобы фронтенду не пришлось делать лишний запрос
    listing = serializers.IntegerField(source='booking.listing_id', read_only=True)
    listing_owner_id = serializers.IntegerField(source='booking.listing.owner_id', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'listing', 'listing_owner_id', 'author_email', 'booking',
            'rating', 'comment', 'landlord_reply', 'replied_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'listing', 'listing_owner_id', 'author_email',
            'landlord_reply', 'replied_at', 'created_at',
        ]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['booking', 'rating', 'comment']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Рейтинг должен быть от 1 до 5')
        return value


class ReviewReplySerializer(serializers.Serializer):
    reply = serializers.CharField(max_length=2000, allow_blank=False)
