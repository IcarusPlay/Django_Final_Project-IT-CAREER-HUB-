from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.listings.serializers import ListingSerializer, ListingCreateSerializer
from apps.listings.services import ListingService


# Controller (views.py) - самый "тонкий" слой во всей архитектуре. Его задача:
# 1) принять HTTP-запрос и достать из него нужные данные (request.data, query_params, pk из URL)
# 2) вызвать соответствующий метод сервиса, где происходит вся реальная работа
# 3) обернуть результат в Response с правильным HTTP-статусом
# Здесь НЕТ ни проверок прав доступа, ни бизнес-логики - если понадобится поменять
# правило "кто может редактировать объявление", идём в ListingService, а не сюда.

class ListingListCreateView(APIView):
    # IsAuthenticatedOrReadOnly - непонятно на первый взгляд название, но логика простая:
    # GET-запросы (чтение) доступны ВСЕМ, включая анонимных посетителей - список объявлений
    # это публичная информация. А вот POST (создание) требует авторизации - это DRF проверяет
    # автоматически ДО того как метод post() вообще вызовется, если проверка не пройдёт -
    # клиент получит 403 Forbidden ещё до захода в код.
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # request.user всегда существует в Django (даже для анонимов - это будет
        # специальный объект AnonymousUser), но is_authenticated отличает реального
        # залогиненного пользователя от анонима
        user = request.user if request.user.is_authenticated else None
        listings = ListingService.get_list(request.query_params, user)
        # many=True - говорим сериализатору что на входе список объектов, а не один объект
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    def post(self, request):
        # ListingCreateSerializer(data=request.data) - "сырые" данные из тела запроса
        # передаются в сериализатор для валидации (проверка типов, обязательных полей,
        # кастомные validate_* методы вроде проверки что цена больше 0)
        serializer = ListingCreateSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.validated_data - уже провалидированные и приведённые к нужным
            # типам данные (например price_per_night здесь уже Decimal, а не строка)
            listing = ListingService.create(request.user, serializer.validated_data)
            # Возвращаем созданный объект через ДРУГОЙ сериализатор (ListingSerializer,
            # не CreateSerializer) - потому что в ответе клиенту нужно показать ПОЛНУЮ
            # информацию (включая id, owner, views_count), а не только те поля что
            # были нужны для создания
            return Response(ListingSerializer(listing).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListingDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        # pk (primary key) автоматически попадает сюда из URL благодаря паттерну
        # path('<int:pk>/', ...) в urls.py
        #
        # ВАЖНО: именно здесь, и только здесь, вызывается get_by_id_and_track_view(),
        # а не обычный get_by_id() - потому что реальный просмотр страницы объявления
        # происходит именно через этот GET-запрос. Во всех остальных местах ниже
        # (put/patch/delete/toggle) используется "обычный" get_by_id() без счётчика.
        listing = ListingService.get_by_id_and_track_view(pk, request)
        return Response(ListingSerializer(listing).data)

    def put(self, request, pk):
        # PUT - полное обновление объекта (нужно передать ВСЕ поля, даже если меняешь одно)
        listing = ListingService.get_by_id(pk)
        serializer = ListingCreateSerializer(listing, data=request.data)
        if serializer.is_valid():
            updated = ListingService.update(listing, request.user, serializer.validated_data)
            return Response(ListingSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        # PATCH - частичное обновление (можно передать только одно изменившееся поле).
        # partial=True в сериализаторе - говорит DRF "не требуй обязательные поля,
        # если их нет в запросе - просто оставь как было"
        listing = ListingService.get_by_id(pk)
        serializer = ListingCreateSerializer(listing, data=request.data, partial=True)
        if serializer.is_valid():
            updated = ListingService.update(listing, request.user, serializer.validated_data)
            return Response(ListingSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        listing = ListingService.get_by_id(pk)
        ListingService.delete(listing, request.user)
        # 204 No Content - стандартный ответ на успешное удаление, тело ответа пустое
        # (нет смысла что-то возвращать про объект, которого больше "нет")
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListingToggleStatusView(APIView):
    # Только для авторизованных - анонимы вообще не должны трогать этот эндпоинт
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        listing = ListingService.get_by_id(pk)
        updated = ListingService.toggle_status(listing, request.user)
        return Response(ListingSerializer(updated).data)


class MyListingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user здесь гарантированно реальный пользователь (не аноним) -
        # это обеспечивает permission_classes выше, DRF не пропустит сюда анонима
        listings = ListingService.get_my_listings(request.user)
        return Response(ListingSerializer(listings, many=True).data)


class PopularKeywordsView(APIView):
    # У этого класса НЕТ явного permission_classes - значит используется значение
    # по умолчанию из settings.py (DEFAULT_PERMISSION_CLASSES = IsAuthenticatedOrReadOnly),
    # то есть GET доступен всем без авторизации - это открытая справочная информация
    def get(self, request):
        keywords = ListingService.get_popular_keywords()
        return Response(list(keywords))


class SearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = ListingService.get_search_history(request.user)
        # Вручную формируем список словарей вместо использования сериализатора -
        # для такой простой структуры (два поля) полноценный ModelSerializer был бы избыточен
        data = [{'keyword': h.keyword, 'searched_at': h.searched_at} for h in history]
        return Response(data)


class ListingCitiesView(APIView):
    # Публичный эндпоинт (нет permission_classes - используется дефолт), не требует
    # авторизации - список городов нужен всем посетителям сайта для фильтра поиска,
    # даже тем кто ещё не зарегистрировался
    def get(self, request):
        return Response(ListingService.get_cities())
