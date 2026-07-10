from django.urls import path
from .views import (
    ListingListCreateView,
    ListingDetailView,
    ListingToggleStatusView,
    MyListingsView,
    PopularKeywordsView,
    SearchHistoryView,
    ListingCitiesView,
)

urlpatterns = [
    path('', ListingListCreateView.as_view()),
    path('my/', MyListingsView.as_view()),
    path('cities/', ListingCitiesView.as_view()),
    path('popular-keywords/', PopularKeywordsView.as_view()),
    path('search-history/', SearchHistoryView.as_view()),
    path('<int:pk>/', ListingDetailView.as_view()),
    path('<int:pk>/toggle/', ListingToggleStatusView.as_view()),
]
