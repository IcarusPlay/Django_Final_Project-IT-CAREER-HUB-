from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.controllers.urls')),
    path('api/listings/', include('apps.listings.controllers.urls')),
    path('api/bookings/', include('apps.bookings.controllers.urls')),
    path('api/reviews/', include('apps.reviews.controllers.urls')),
]
