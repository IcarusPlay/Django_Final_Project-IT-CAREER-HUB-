from django.urls import path
from .views import ReviewListCreateView, ReviewDeleteView

urlpatterns = [
    path('<int:listing_id>/reviews/', ReviewListCreateView.as_view()),
    path('<int:listing_id>/reviews/<int:pk>/', ReviewDeleteView.as_view()),
]
