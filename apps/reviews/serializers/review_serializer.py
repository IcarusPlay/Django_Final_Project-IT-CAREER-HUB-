from rest_framework import serializers
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source='author.email', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'listing', 'author_email', 'booking', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'author_email', 'created_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['booking', 'rating', 'comment']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Рейтинг должен быть от 1 до 5')
        return value
