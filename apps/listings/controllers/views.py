from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.listings.serializers import ListingSerializer, ListingCreateSerializer
from apps.listings.services import ListingService


class ListingListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # передаём все query params в сервис — там фильтрация
        listings = ListingService.get_list(request.query_params)
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ListingCreateSerializer(data=request.data)
        if serializer.is_valid():
            listing = ListingService.create(request.user, serializer.validated_data)
            return Response(ListingSerializer(listing).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListingDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        listing = ListingService.get_by_id(pk)
        return Response(ListingSerializer(listing).data)

    def put(self, request, pk):
        listing = ListingService.get_by_id(pk)
        serializer = ListingCreateSerializer(listing, data=request.data)
        if serializer.is_valid():
            updated = ListingService.update(listing, request.user, serializer.validated_data)
            return Response(ListingSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        listing = ListingService.get_by_id(pk)
        serializer = ListingCreateSerializer(listing, data=request.data, partial=True)
        if serializer.is_valid():
            updated = ListingService.update(listing, request.user, serializer.validated_data)
            return Response(ListingSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        listing = ListingService.get_by_id(pk)
        ListingService.delete(listing, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListingToggleStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        listing = ListingService.get_by_id(pk)
        updated = ListingService.toggle_status(listing, request.user)
        return Response(ListingSerializer(updated).data)
