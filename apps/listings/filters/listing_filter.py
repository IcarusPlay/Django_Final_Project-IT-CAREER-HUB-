from django.db.models import Q
from apps.listings.choices import ListingStatus


class ListingFilter:
    def __init__(self, queryset, params):
        self.queryset = queryset
        self.params = params

    def apply(self):
        qs = self.queryset
        qs = self.add_filters(qs)
        qs = self.add_search(qs)
        qs = self.add_sorting(qs)
        return qs

    def add_filters(self, qs):
        # по умолчанию только активные
        qs = qs.filter(status=ListingStatus.ACTIVE)

        city = self.params.get('city')
        if city:
            qs = qs.filter(city__icontains=city)

        district = self.params.get('district')
        if district:
            qs = qs.filter(district__icontains=district)

        property_type = self.params.get('property_type')
        if property_type:
            qs = qs.filter(property_type=property_type)

        # диапазон комнат
        rooms_min = self.params.get('rooms_min')
        if rooms_min:
            qs = qs.filter(rooms__gte=rooms_min)

        rooms_max = self.params.get('rooms_max')
        if rooms_max:
            qs = qs.filter(rooms__lte=rooms_max)

        # точное кол-во комнат (если передали)
        rooms = self.params.get('rooms')
        if rooms:
            qs = qs.filter(rooms=rooms)

        # диапазон цены
        price_min = self.params.get('price_min')
        if price_min:
            qs = qs.filter(price_per_night__gte=price_min)

        price_max = self.params.get('price_max')
        if price_max:
            qs = qs.filter(price_per_night__lte=price_max)

        return qs

    def add_search(self, qs):
        search = self.params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        return qs

    def add_sorting(self, qs):
        ordering = self.params.get('ordering', '-created_at')
        allowed = [
            'price_per_night', '-price_per_night',
            'created_at', '-created_at',
            'rooms', '-rooms',
            'views_count', '-views_count',   # для сортировки по популярности
        ]
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs
