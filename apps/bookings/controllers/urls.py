from django.urls import path
from .views import (
    BookingListCreateView,
    BookingDetailView,
    BookingCancelView,
    BookingConfirmView,
    BookingRejectView,
    BookingIncomingCountView,
    BookingNotificationsCountView,
    ListingBookedRangesView,
)

urlpatterns = [
    path('', BookingListCreateView.as_view()),
    path('incoming-count/', BookingIncomingCountView.as_view()),
    path('notifications-count/', BookingNotificationsCountView.as_view()),
    path('listing/<int:listing_id>/booked-ranges/', ListingBookedRangesView.as_view()),
    path('<int:pk>/', BookingDetailView.as_view()),
    path('<int:pk>/cancel/', BookingCancelView.as_view()),
    path('<int:pk>/confirm/', BookingConfirmView.as_view()),
    path('<int:pk>/reject/', BookingRejectView.as_view()),
]
