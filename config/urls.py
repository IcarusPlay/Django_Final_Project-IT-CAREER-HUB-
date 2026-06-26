from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API
    path('api/auth/', include('apps.users.controllers.urls')),
    path('api/listings/', include('apps.listings.controllers.urls')),
    path('api/bookings/', include('apps.bookings.controllers.urls')),
    path('api/reviews/', include('apps.reviews.controllers.urls')),

    # Frontend страницы
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('listing/', TemplateView.as_view(template_name='listing.html'), name='listing'),
    path('auth/', TemplateView.as_view(template_name='auth.html'), name='auth'),
    path('bookings/', TemplateView.as_view(template_name='bookings.html'), name='bookings'),
]
