from rest_framework.exceptions import PermissionDenied, NotFound
from apps.listings.repositories import ListingRepository
from apps.listings.filters import ListingFilter


# Service - это слой БИЗНЕС-ЛОГИКИ. Здесь решается "МОЖНО ли это сделать" (права доступа,
# правила, проверки), а конкретные запросы к базе делегируются в Repository ("КАК получить
# данные из базы"). Такое разделение позволяет: (1) вьюхе оставаться тонкой - она просто
# вызывает нужный метод сервиса и оборачивает результат в Response; (2) логику легко
# переиспользовать - например, из другого сервиса или из management-команды, без дублирования кода.
class ListingService:

    @staticmethod
    def get_list(params, user=None):
        # Получаем весь queryset объявлений (уже без мягко удалённых - это гарантирует
        # ListingManager в самой модели), и передаём его в ListingFilter вместе с параметрами
        # запроса (?city=, ?price_min= и т.д.) - вся логика фильтрации/поиска/сортировки
        # инкапсулирована именно там, а не размазана здесь.
        qs = ListingRepository.get_all()
        listing_filter = ListingFilter(qs, params)
        result = listing_filter.apply()

        # Побочный эффект: если пользователь искал что-то через ?search=, запоминаем
        # этот запрос в историю поиска (но только если пользователь залогинен -
        # анонимную историю поиска сохранять некому и незачем).
        search = params.get('search')
        if search and user:
            ListingRepository.save_search(user, search)

        return result

    @staticmethod
    def get_by_id(listing_id):
        # ВАЖНО: этот метод НЕ увеличивает счётчик просмотров - используется когда нам нужно
        # просто достать объект из базы (редактирование, удаление, toggle статуса, отображение
        # списка отзывов). Раньше здесь по ошибке использовался один и тот же метод и для
        # реального просмотра, и для служебных операций - из-за этого счётчик просмотров
        # рос при каждом сохранении/удалении объявления, что было главной причиной бага
        # "просмотры скачут непонятным образом". Разделение на два метода это исправило.
        listing = ListingRepository.get_by_id(listing_id)
        if not listing:
            raise NotFound('Объявление не найдено')
        return listing

    @staticmethod
    def get_by_id_and_track_view(listing_id, request):
        # Этот метод вызывается ТОЛЬКО из ListingDetailView.get() - то есть только когда
        # пользователь реально открыл страницу конкретного объявления. Именно здесь и только
        # здесь корректно увеличивать счётчик просмотров.
        listing = ListingService.get_by_id(listing_id)

        user = request.user if request.user.is_authenticated else None

        # Владелец объявления не считается "посетителем" - когда арендодатель заходит
        # на своё же объявление (например чтобы проверить как оно выглядит), это не должно
        # накручивать статистику просмотров.
        if user and listing.owner_id == user.id:
            return listing

        # Дедупликация просмотров: чтобы один и тот же человек, обновляя страницу 20 раз,
        # не накрутил 20 "просмотров" - используем таблицу ListingView как журнал того,
        # кто уже смотрел это объявление. Для авторизованных - привязка по user,
        # для анонимных - по session_key (уникальный идентификатор браузерной сессии,
        # который Django хранит в cookies).
        #
        # request.session.session_key может быть пустым, если это самый первый запрос
        # анонимного пользователя за сессию (сессия ещё не создана физически) -
        # тогда принудительно создаём её через .save(), чтобы получить реальный ключ.
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
        # Проверка прав прямо здесь, а не полагаемся только на permission_classes во view -
        # так правило "кто может создавать объявления" видно в одном месте и легко читается,
        # а не размазано между DRF-пермишенами и бизнес-логикой.
        if not owner.is_landlord():
            raise PermissionDenied('Только арендодатели могут создавать объявления')
        return ListingRepository.create(owner, validated_data)

    @staticmethod
    def update(listing, user, validated_data):
        # Владелец объявления - единственный кто может его редактировать.
        # Сравниваем listing.owner (объект User) с user (текущий залогиненный пользователь).
        if listing.owner != user:
            raise PermissionDenied('Нельзя редактировать чужое объявление')
        return ListingRepository.update(listing, validated_data)

    @staticmethod
    def delete(listing, user):
        if listing.owner != user:
            raise PermissionDenied('Нельзя удалять чужое объявление')
        # ListingRepository.delete() вызовет listing.delete(), а он переопределён в модели -
        # реального удаления из базы не произойдёт, сработает мягкое удаление (is_deleted=True)
        ListingRepository.delete(listing)

    @staticmethod
    def toggle_status(listing, user):
        # Переключить объявление между "активно" и "скрыто" (не показывается в поиске,
        # но и не удалено - арендодатель может временно снять жильё с публикации)
        if listing.owner != user:
            raise PermissionDenied('Нельзя менять статус чужого объявления')
        return ListingRepository.toggle_status(listing)

    @staticmethod
    def get_my_listings(user):
        # Для страницы "Мои объявления" - в отличие от get_list(), здесь НЕ фильтруем
        # только активные объявления, арендодатель должен видеть и свои скрытые тоже.
        return ListingRepository.get_by_owner(user)

    @staticmethod
    def get_popular_keywords():
        return ListingRepository.get_popular_keywords()

    @staticmethod
    def get_search_history(user):
        return ListingRepository.get_search_history(user)

    @staticmethod
    def get_cities():
        # Список уникальных городов из уже существующих объявлений - используется фронтендом
        # чтобы наполнить выпадающий список фильтра. Если арендодатель создаст объявление
        # в новом городе, которого раньше не было - он сразу появится в этом списке,
        # без необходимости хардкодить города где-либо в коде.
        return list(ListingRepository.get_distinct_cities())
