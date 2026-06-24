from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerUIView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API
    path('api/auth/', include('apps.users.controllers.urls')),
    path('api/listings/', include('apps.listings.controllers.urls')),
    path('api/bookings/', include('apps.bookings.controllers.urls')),
    path('api/reviews/', include('apps.reviews.controllers.urls')),
]
