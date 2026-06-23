from rest_framework import serializers
from apps.listings.models import Listing
from apps.users.serializers import UserSerializer


class ListingSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'owner', 'title', 'description',
            'city', 'district', 'address',
            'property_type', 'rooms', 'price_per_night',
            'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class ListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            'title', 'description',
            'city', 'district', 'address',
            'property_type', 'rooms', 'price_per_night',
        ]

    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError('Цена должна быть больше 0')
        return value

    def validate_rooms(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество комнат должно быть не менее 1')
        return value
