from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.listings.serializers import ListingSerializer, ListingCreateSerializer
from apps.listings.services import ListingService


class ListingListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        listings = ListingService.get_list(request.query_params, user)
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
        user = request.user if request.user.is_authenticated else None
        listing = ListingService.get_by_id(pk, user)
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


class MyListingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        listings = ListingService.get_my_listings(request.user)
        return Response(ListingSerializer(listings, many=True).data)


class PopularKeywordsView(APIView):
    # популярные поисковые запросы — открытый эндпоинт
    def get(self, request):
        keywords = ListingService.get_popular_keywords()
        return Response(list(keywords))


class SearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = ListingService.get_search_history(request.user)
        data = [{'keyword': h.keyword, 'searched_at': h.searched_at} for h in history]
        return Response(data)
