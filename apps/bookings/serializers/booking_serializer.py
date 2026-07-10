from rest_framework import serializers
from apps.bookings.models import Booking


class BookingSerializer(serializers.ModelSerializer):
    # показываем от кого пришла заявка - раньше арендодатель видел только tenant (число id)
    tenant_email = serializers.EmailField(source='tenant.email', read_only=True)
    tenant_username = serializers.CharField(source='tenant.username', read_only=True)
    # видно ли уже оставлен отзыв на это бронирование (нужно фронту чтобы не показывать форму дважды)
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'listing', 'tenant', 'tenant_email', 'tenant_username',
            'date_from', 'date_to', 'total_price', 'status', 'has_review', 'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'total_price', 'status', 'created_at']

    def get_has_review(self, obj):
        return hasattr(obj, 'review')


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['listing', 'date_from', 'date_to']

    def validate(self, data):
        if data['date_from'] >= data['date_to']:
            raise serializers.ValidationError('Дата начала должна быть раньше даты окончания')
        return data
