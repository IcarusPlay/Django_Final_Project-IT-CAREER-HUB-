from django.db.models import Q
from apps.listings.choices import ListingStatus


# Отдельный класс для фильтрации, поиска и сортировки объявлений - не смешан с view
# и не встроен прямо в сериализатор. Идея: queryset (ещё не выполненный запрос к базе,
# просто "черновик" запроса) поочерёдно "обрастает" условиями через .filter()/.order_by(),
# и только в самом конце, когда Django реально обращается к базе (например через
# сериализацию списка), выполняется ОДИН финальный SQL-запрос со всеми условиями сразу -
# это эффективно, лишних обращений к базе не происходит.
class ListingFilter:
    def __init__(self, queryset, params):
        self.queryset = queryset  # исходный набор объявлений (например Listing.objects.all())
        self.params = params      # query-параметры из URL, вида {'city': 'Berlin', 'price_min': '50', ...}

    def apply(self):
        # Единая точка входа - вызывается снаружи (из ListingService.get_list()).
        # Последовательно применяем три группы правил: обычные фильтры, полнотекстовый
        # поиск, и в конце сортировку (порядок важен - сортировку логично применять
        # к уже отфильтрованному набору, а не наоборот).
        qs = self.queryset
        qs = self.add_filters(qs)
        qs = self.add_search(qs)
        qs = self.add_sorting(qs)
        return qs

    def add_filters(self, qs):
        # По умолчанию в общем поиске показываем только активные объявления - скрытые
        # арендодателем (status=inactive) не должны "случайно" всплывать в общей выдаче.
        qs = qs.filter(status=ListingStatus.ACTIVE)

        # Каждый фильтр применяется, ТОЛЬКО если соответствующий параметр реально передан
        # в запросе (params.get() вернёт None/пустую строку, если его нет - тогда просто
        # пропускаем этот if и не меняем qs). Так один и тот же класс одинаково хорошо
        # работает и для "покажи вообще все объявления", и для "покажи только в Берлине
        # дешевле 100 евро с 2 комнатами" - в зависимости от того что реально прислал фронтенд.

        city = self.params.get('city')
        if city:
            # icontains - "содержит, регистронезависимо". Например, city='berlin' найдёт
            # и "Berlin", и "BERLIN" - более дружелюбно к пользователю, чем точное совпадение.
            qs = qs.filter(city__icontains=city)

        district = self.params.get('district')
        if district:
            qs = qs.filter(district__icontains=district)

        property_type = self.params.get('property_type')
        if property_type:
            # Тут точное совпадение (не icontains) - тип жилья это конкретное значение
            # из ограниченного списка (apartment/house/room/studio), а не свободный текст.
            qs = qs.filter(property_type=property_type)

        # Диапазон количества комнат - можно передать только rooms_min, только rooms_max,
        # оба сразу, или ни одного (тогда фильтр по комнатам вообще не применяется)
        rooms_min = self.params.get('rooms_min')
        if rooms_min:
            qs = qs.filter(rooms__gte=rooms_min)  # gte = greater than or equal, "больше или равно"

        rooms_max = self.params.get('rooms_max')
        if rooms_max:
            qs = qs.filter(rooms__lte=rooms_max)  # lte = less than or equal, "меньше или равно"

        # Точное количество комнат - отдельный параметр для случая "хочу ровно 2 комнаты",
        # а не диапазон
        rooms = self.params.get('rooms')
        if rooms:
            qs = qs.filter(rooms=rooms)

        # Диапазон цены за ночь - аналогично комнатам
        price_min = self.params.get('price_min')
        if price_min:
            qs = qs.filter(price_per_night__gte=price_min)

        price_max = self.params.get('price_max')
        if price_max:
            qs = qs.filter(price_per_night__lte=price_max)

        return qs

    def add_search(self, qs):
        # Полнотекстовый поиск по ключевому слову - ищем совпадение и в названии,
        # и в описании одновременно. Q() позволяет объединить два условия через ИЛИ (|) -
        # обычная цепочка .filter(title__icontains=x).filter(description__icontains=x)
        # означала бы "И" (совпадение в обоих полях сразу), а нам нужно "ИЛИ".
        search = self.params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        return qs

    def add_sorting(self, qs):
        # Список ЯВНО разрешённых вариантов сортировки - защита от того, чтобы кто-то
        # передал произвольную строку в ?ordering= и получил сортировку по секретному
        # полю (например password_hash) или вызвал ошибку. Если пришедшее значение
        # не входит в allowed - используется значение по умолчанию (сначала новые).
        ordering = self.params.get('ordering', '-created_at')
        allowed = [
            'price_per_night', '-price_per_night',   # цена по возрастанию / убыванию
            'created_at', '-created_at',              # дата создания (старые сначала / новые сначала)
            'rooms', '-rooms',                        # количество комнат
            'views_count', '-views_count',             # сортировка по популярности (просмотрам)
        ]
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs
