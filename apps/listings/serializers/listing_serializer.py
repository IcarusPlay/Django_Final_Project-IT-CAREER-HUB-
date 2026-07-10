from datetime import date
from rest_framework import serializers
from apps.listings.models import Listing
from apps.users.serializers import UserSerializer


class ListingSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    # есть ли уже подтверждённое бронирование (текущее или предстоящее) -
    # используется чтобы показать бейдж "Забронировано" на фронтенде
    is_booked = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'owner', 'title', 'description',
            'city', 'district', 'address',
            'property_type', 'rooms', 'price_per_night',
            'status', 'image', 'views_count', 'is_booked',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'views_count', 'is_booked', 'created_at', 'updated_at']

    def get_is_booked(self, obj):
        today = date.today()
        # считаем занятым если есть подтверждённая бронь, которая ещё не закончилась
        # (то есть уже идёт сейчас или начнётся в будущем)
        return obj.bookings.filter(
            status='confirmed',
            date_to__gte=today,
        ).exists()


class ListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            'title', 'description',
            'city', 'district', 'address',
            'property_type', 'rooms', 'price_per_night', 'image',
        ]

    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError('Цена должна быть больше 0')
        return value

    def validate_rooms(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество комнат должно быть не менее 1')
        return value
