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
        # используем get_by_id БЕЗ трекинга - загрузка списка отзывов не является
        # "просмотром объявления" и не должна крутить счётчик views_count
        listing = ListingService.get_by_id(listing_id)
        reviews = ReviewService.get_by_listing(listing)
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request, listing_id):
        # listing_id в URL просто для красивого роута — реальный listing берётся из booking
        serializer = ReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            review = ReviewService.create(request.user, serializer.validated_data)
            return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id, pk):
        from apps.reviews.repositories import ReviewRepository
        review = ReviewRepository.get_by_id(pk)
        if not review:
            return Response({'error': 'Отзыв не найден'}, status=status.HTTP_404_NOT_FOUND)
        ReviewService.delete(review, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewReplyView(APIView):
    # ответ владельца объявления на отзыв
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id, pk):
        from apps.reviews.repositories import ReviewRepository
        review = ReviewRepository.get_by_id(pk)
        if not review:
            return Response({'error': 'Отзыв не найден'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewReplySerializer(data=request.data)
        if serializer.is_valid():
            updated = ReviewService.reply(review, request.user, serializer.validated_data['reply'])
            return Response(ReviewSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
