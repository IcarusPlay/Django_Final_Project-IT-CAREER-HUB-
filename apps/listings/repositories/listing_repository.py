from django.db.models import Count, F
from apps.listings.models import Listing, ListingView, SearchHistory


# Repository - это слой ТОЛЬКО прямых запросов к базе данных, без бизнес-логики и без
# проверок прав доступа (это задача Service). Здесь просто "дай мне такие-то данные"
# или "сохрани вот это" - максимально простой и предсказуемый код.
class ListingRepository:

    @staticmethod
    def get_all():
        # select_related('owner') - оптимизация: без неё Django сделал бы ОТДЕЛЬНЫЙ запрос
        # к базе на каждое объявление, чтобы получить данные его владельца (это называется
        # "проблема N+1 запросов" - при 50 объявлениях было бы 50 лишних запросов).
        # select_related сразу делает один JOIN-запрос и подтягивает владельца вместе
        # с объявлением - вместо 51 запроса к базе получаем всего 1.
        return Listing.objects.select_related('owner').all()

    @staticmethod
    def get_by_id(listing_id):
        return Listing.objects.select_related('owner').filter(id=listing_id).first()
        # .first() вместо .get() - если объявления с таким id нет, вернётся None
        # (а не будет выброшено исключение DoesNotExist) - дальше в сервисе это
        # аккуратно превращается в понятную ошибку 404 NotFound

    @staticmethod
    def get_by_owner(owner):
        return Listing.objects.filter(owner=owner)

    @staticmethod
    def create(owner, validated_data):
        # **validated_data - это "распаковка" словаря в именованные аргументы.
        # Если validated_data = {'title': 'Квартира', 'city': 'Berlin'}, то вызов
        # Listing.objects.create(owner=owner, **validated_data) равносилен
        # Listing.objects.create(owner=owner, title='Квартира', city='Berlin')
        return Listing.objects.create(owner=owner, **validated_data)

    @staticmethod
    def update(listing, validated_data):
        # Обновляем только те поля, что реально пришли в validated_data (например,
        # при PATCH-запросе может прийти только одно поле, а не всё объявление целиком)
        for field, value in validated_data.items():
            setattr(listing, field, value)
        listing.save()
        return listing

    @staticmethod
    def delete(listing):
        # Вызывает listing.delete() - а этот метод ПЕРЕОПРЕДЕЛЁН в самой модели Listing,
        # поэтому реального удаления строки из базы не произойдёт, сработает мягкое удаление
        listing.delete()

    @staticmethod
    def toggle_status(listing):
        from apps.listings.choices import ListingStatus
        # Простое переключение "туда-обратно": если сейчас активно - делаем скрытым,
        # и наоборот. Импорт ListingStatus внутри метода (а не в начале файла) сделан
        # чтобы избежать потенциальных циклических импортов между модулями choices и repository.
        if listing.status == ListingStatus.ACTIVE:
            listing.status = ListingStatus.INACTIVE
        else:
            listing.status = ListingStatus.ACTIVE
        listing.save()
        return listing

    @staticmethod
    def increment_views(listing):
        # F() выражение - это способ сказать базе данных "увеличь текущее значение поля
        # на 1", не читая его сначала в Python и не записывая обратно. Разница критична
        # при одновременных запросах: если бы мы сделали listing.views_count += 1;
        # listing.save() - и два разных пользователя открыли страницу ОДНОВРЕМЕННО,
        # оба могли бы прочитать одно и то же старое значение (например 10), оба прибавили
        # бы единицу и оба сохранили 11 - в итоге просмотр потерялся бы (должно было
        # стать 12). F('views_count') + 1 выполняется как часть самого SQL-запроса
        # (UPDATE listings SET views_count = views_count + 1), и база данных гарантирует
        # атомарность такой операции - потерянных обновлений не будет.
        Listing.objects.filter(id=listing.id).update(views_count=F('views_count') + 1)
        # После UPDATE наш Python-объект listing всё ещё хранит СТАРОЕ значение в памяти -
        # refresh_from_db() перечитывает актуальные данные из базы
        listing.refresh_from_db()
        return listing

    @staticmethod
    def has_viewed(listing, user, session_key):
        # Проверка "уже смотрел или нет" для дедупликации счётчика просмотров.
        # Для авторизованных пользователей ищем запись ListingView с конкретным user.
        if user and user.is_authenticated:
            return ListingView.objects.filter(listing=listing, user=user).exists()
        # Для анонимных - по session_key (уникальный идентификатор именно этого браузера/сессии).
        # user__isnull=True - явно ищем именно "анонимные" записи просмотра, чтобы не спутать
        # с ситуацией когда тот же самый session_key случайно совпал бы с чужой авторизованной записью
        if session_key:
            return ListingView.objects.filter(listing=listing, session_key=session_key, user__isnull=True).exists()
        return False

    @staticmethod
    def save_view(listing, user, session_key=None):
        # Создаём запись в журнале просмотров - либо с привязкой к user (если залогинен),
        # либо с привязкой к session_key (если анонимный посетитель), но не к обоим сразу
        ListingView.objects.create(
            listing=listing,
            user=user if user and user.is_authenticated else None,
            session_key=session_key if not (user and user.is_authenticated) else None,
        )

    @staticmethod
    def save_search(user, keyword):
        if user and user.is_authenticated and keyword:
            SearchHistory.objects.create(user=user, keyword=keyword)

    @staticmethod
    def get_popular_keywords(limit=10):
        # .values('keyword') - группируем результаты по значению keyword (а не по id,
        # как было бы по умолчанию). .annotate(count=Count('id')) - для каждой такой
        # группы считаем сколько раз это слово встретилось. order_by('-count') -
        # сортируем от самых частых запросов к редким, [:limit] - берём только топ-10.
        # Это классический SQL "GROUP BY keyword ORDER BY COUNT(*) DESC LIMIT 10",
        # но выраженный через Django ORM без единой строчки сырого SQL.
        return (
            SearchHistory.objects
            .values('keyword')
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )

    @staticmethod
    def get_search_history(user):
        return SearchHistory.objects.filter(user=user)

    @staticmethod
    def get_distinct_cities():
        # .exclude(city='') - убираем пустые значения (на случай если где-то город
        # не заполнен). .values_list('city', flat=True) - вместо списка объектов Listing
        # возвращает просто список строк с названиями городов. .distinct() - убирает
        # повторы (если 10 объявлений в Berlin, город "Berlin" попадёт в список 1 раз).
        # .order_by('city') - сортируем по алфавиту для удобного отображения в select на фронте.
        return (
            Listing.objects
            .exclude(city='')
            .values_list('city', flat=True)
            .distinct()
            .order_by('city')
        )
