from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
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
    path('listings/', TemplateView.as_view(template_name='listings.html'), name='listings'),
    path('listings/create/', TemplateView.as_view(template_name='listing_create.html'), name='listing-create'),
    path('listings/my/', TemplateView.as_view(template_name='my_listings.html'), name='my-listings'),
    path('listing/', TemplateView.as_view(template_name='listing.html'), name='listing'),
    path('auth/', TemplateView.as_view(template_name='auth.html'), name='auth'),
    path('bookings/', TemplateView.as_view(template_name='bookings.html'), name='bookings'),
]

# в режиме разработки Django сам отдаёт загруженные файлы (картинки объявлений)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
