from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.bookings.serializers import BookingSerializer, BookingCreateSerializer
from apps.bookings.services import BookingService
from apps.listings.services import ListingService


class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Один и тот же эндпоинт GET /api/bookings/ ведёт себя ПО-РАЗНОМУ в зависимости
        # от роли пользователя - это сделано специально, чтобы у фронтенда была одна
        # универсальная "точка входа" для страницы бронирований, а какие именно данные
        # показать (свои брони или входящие заявки) - решает бэкенд по роли текущего юзера.
        if request.user.is_landlord():
            bookings = BookingService.get_incoming_bookings(request.user)
        else:
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
        # Проверка "а имеет ли ПРАВО именно этот пользователь отменить именно эту бронь"
        # происходит внутри BookingService.cancel(), а не здесь - вьюха просто передаёт
        # управление дальше
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


class BookingIncomingCountView(APIView):
    # Для бейджа-циферки над "Заявки на аренду" в навбаре арендодателя
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = BookingService.get_pending_count(request.user)
        return Response({'count': count})


class BookingNotificationsCountView(APIView):
    # Для бейджа-циферки над "Мои бронирования" в навбаре арендатора -
    # сколько заявок изменили статус (подтверждено/отклонено), а он ещё не видел
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = BookingService.get_unseen_notifications_count(request.user)
        return Response({'count': count})

    def post(self, request):
        # Один и тот же URL обслуживает и GET (узнать количество), и POST
        # (отметить как просмотренные) - логично сгруппированы в одном классе,
        # так как оба действия касаются одной и той же концепции "уведомления"
        BookingService.mark_notifications_seen(request.user)
        return Response({'detail': 'ok'})


class ListingBookedRangesView(APIView):
    # Нет permission_classes - используется дефолтная настройка (доступно всем),
    # намеренно публичный эндпоинт: даже неавторизованный посетитель, который ещё
    # не решил регистрироваться, должен видеть какие даты уже заняты, просматривая
    # объявление
    def get(self, request, listing_id):
        listing = ListingService.get_by_id(listing_id)
        ranges = BookingService.get_booked_ranges(listing)
        return Response(ranges)
