from django.urls import path
from .views import (
    BookingListCreateView,
    BookingDetailView,
    BookingCancelView,
    BookingConfirmView,
    BookingRejectView,
)

urlpatterns = [
    path('', BookingListCreateView.as_view()),
    path('<int:pk>/', BookingDetailView.as_view()),
    path('<int:pk>/cancel/', BookingCancelView.as_view()),
    path('<int:pk>/confirm/', BookingConfirmView.as_view()),
    path('<int:pk>/reject/', BookingRejectView.as_view()),
]
