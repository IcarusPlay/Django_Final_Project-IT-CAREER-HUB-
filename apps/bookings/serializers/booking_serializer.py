from rest_framework import serializers
from apps.bookings.models import Booking


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'listing', 'tenant', 'date_from', 'date_to', 'total_price', 'status', 'created_at']
        read_only_fields = ['id', 'tenant', 'total_price', 'status', 'created_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['listing', 'date_from', 'date_to']

    def validate(self, data):
        if data['date_from'] >= data['date_to']:
            raise serializers.ValidationError('Дата начала должна быть раньше даты окончания')
        return data
