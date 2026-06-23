from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.bookings.serializers import BookingSerializer, BookingCreateSerializer
from apps.bookings.services import BookingService


class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # возвращаем бронирования текущего пользователя
        bookings = BookingService.get_my_bookings(request.user)
        return Response(BookingSerializer(bookings, many=True).data)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        if serializer.is_valid():
            booking = BookingService.create(request.user, serializer.validated_data)
            return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        booking = BookingService.get_by_id(pk)
        return Response(BookingSerializer(booking).data)


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = BookingService.get_by_id(pk)
        updated = BookingService.cancel(booking, request.user)
        return Response(BookingSerializer(updated).data)


class BookingConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = BookingService.get_by_id(pk)
        updated = BookingService.confirm(booking, request.user)
        return Response(BookingSerializer(updated).data)


class BookingRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = BookingService.get_by_id(pk)
        updated = BookingService.reject(booking, request.user)
        return Response(BookingSerializer(updated).data)
