from rest_framework.exceptions import PermissionDenied, NotFound
from apps.listings.repositories import ListingRepository
from apps.listings.filters import ListingFilter
from apps.listings.choices import ListingStatus


class ListingService:

    @staticmethod
    def get_list(params, user=None):
        qs = ListingRepository.get_all()
        listing_filter = ListingFilter(qs, params)
        result = listing_filter.apply()

        search = params.get('search')
        if search and user:
            ListingRepository.save_search(user, search)

        return result

    @staticmethod
    def get_by_id(listing_id):
        # ВАЖНО: этот метод НЕ увеличивает счётчик просмотров и НЕ проверяет права
        # доступа - используется для служебных внутренних операций (редактирование,
        # удаление, toggle статуса), где вызывающий код сам уже знает, что имеет право
        # работать с этим объявлением (например владелец меняет своё же объявление).
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise NotFound('Объявление не найдено')
        return listing

    @staticmethod
    def get_by_id_and_track_view(listing_id, request):
        # Этот метод вызывается из ListingDetailView.get() - то есть когда кто угодно
        # (включая анонима) открывает страницу конкретного объявления по прямой ссылке.
        listing = ListingService.get_by_id(listing_id)

        user = request.user if request.user.is_authenticated else None
        is_owner = user and listing.owner_id == user.id

        # ИСПРАВЛЕНИЕ ЗАМЕЧАНИЯ: раньше здесь не было никакой проверки статуса -
        # скрытое (inactive) объявление, хотя и не появлялось в общем списке
        # (см. ListingFilter, там фильтр status=ACTIVE), было всё равно доступно
        # ЛЮБОМУ, кто знал или подобрал прямой ID вида /api/listings/42/. Это утечка -
        # арендодатель "выключил" объявление намеренно (например убрал с публикации,
        # пока ремонтирует квартиру), и оно не должно быть видно посторонним ни в каком
        # виде, включая прямую ссылку. Исключение - сам владелец должен видеть своё
        # скрытое объявление (например чтобы отредактировать его или включить обратно).
        if listing.status != ListingStatus.ACTIVE and not is_owner:
            raise NotFound('Объявление не найдено')

        # Владелец объявления не считается "посетителем" - не накручиваем ему просмотры
        if is_owner:
            return listing

        # Дедупликация просмотров - не даём одному и тому же человеку/сессии
        # накручивать счётчик повторными заходами
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key

        already_viewed = ListingRepository.has_viewed(listing, user, session_key)
        if not already_viewed:
            ListingRepository.save_view(listing, user, session_key)
            listing = ListingRepository.increment_views(listing)

        return listing

    @staticmethod
    def create(owner, validated_data):
        if not owner.is_landlord():
            raise PermissionDenied('Только арендодатели могут создавать объявления')
        return ListingRepository.create(owner, validated_data)

    @staticmethod
    def update(listing, user, validated_data):
        if listing.owner != user:
            raise PermissionDenied('Нельзя редактировать чужое объявление')
        return ListingRepository.update(listing, validated_data)

    @staticmethod
    def delete(listing, user):
        if listing.owner != user:
            raise PermissionDenied('Нельзя удалять чужое объявление')
        ListingRepository.delete(listing)

    @staticmethod
    def toggle_status(listing, user):
        if listing.owner != user:
            raise PermissionDenied('Нельзя менять статус чужого объявления')
        return ListingRepository.toggle_status(listing)

    @staticmethod
    def get_my_listings(user):
        return ListingRepository.get_by_owner(user)

    @staticmethod
    def get_popular_keywords():
        return ListingRepository.get_popular_keywords()

    @staticmethod
    def get_search_history(user):
        return ListingRepository.get_search_history(user)

    @staticmethod
    def get_cities():
        return list(ListingRepository.get_distinct_cities())
