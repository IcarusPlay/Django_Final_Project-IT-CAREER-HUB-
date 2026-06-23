from django.urls import path
from .views import ListingListCreateView, ListingDetailView, ListingToggleStatusView

urlpatterns = [
    path('', ListingListCreateView.as_view()),
    path('<int:pk>/', ListingDetailView.as_view()),
    path('<int:pk>/toggle/', ListingToggleStatusView.as_view()),
]
