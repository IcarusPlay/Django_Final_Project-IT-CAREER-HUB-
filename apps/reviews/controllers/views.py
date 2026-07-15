from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.listings.services import ListingService
from apps.reviews.serializers import ReviewSerializer, ReviewCreateSerializer, ReviewReplySerializer
from apps.reviews.services import ReviewService


class ReviewListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, listing_id):
        # ВАЖНО: используем get_by_id() (обычный, без трекинга), а НЕ
        # get_by_id_and_track_view() - загрузка списка отзывов происходит на той же
        # странице объявления, что и сам просмотр, и если бы здесь тоже увеличивался
        # счётчик просмотров - объявление засчитывало бы ДВА просмотра за одно
        # открытие страницы. Именно эта ошибка когда-то была причиной бага
        # "счётчик просмотров растёт быстрее чем должен".
        listing = ListingService.get_by_id(listing_id)
        reviews = ReviewService.get_by_listing(listing)
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request, listing_id):
        # listing_id в URL нужен только для красивого адреса вида
        # /api/reviews/5/reviews/ - реальная связь с объявлением проверяется
        # через booking, который передан в теле запроса (см. ReviewService.create)
        serializer = ReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            review = ReviewService.create(request.user, serializer.validated_data)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id, pk):
        # Импорт репозитория прямо внутри метода (а не в начале файла) - здесь это
        # сделано просто для локальности использования, встречается в паре мест проекта
        from apps.reviews.repositories import ReviewRepository
        review = ReviewRepository.get_by_id(pk)
        if not review:
            return Response({'error': 'Отзыв не найден'}, status=status.HTTP_404_NOT_FOUND)
        ReviewService.delete(review, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewReplyView(APIView):
    # Ответ владельца объявления на отзыв - отдельный узкий эндпоинт с одним полем 'reply',
    # а не часть общего "обновления" отзыва - потому что редактировать текст/рейтинг
    # самого отзыва имеет право только автор, а отвечать на него - только владелец
    # объявления. Разные права на разные действия проще держать в разных вьюхах.
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id, pk):
        from apps.reviews.repositories import ReviewRepository
        review = ReviewRepository.get_by_id(pk)
        if not review:
            return Response({'error': 'Отзыв не найден'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewReplySerializer(data=request.data)
        if serializer.is_valid():
            # Проверка "а имеет ли право именно этот пользователь отвечать на этот
            # конкретный отзыв" происходит внутри ReviewService.reply()
            updated = ReviewService.reply(review, request.user, serializer.validated_data['reply'])
            return Response(ReviewSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
