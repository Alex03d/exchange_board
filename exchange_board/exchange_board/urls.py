from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', include('offers.urls')),
    path('users/', include('users.urls')),
    path('rating/', include('rating.urls')),
    path('admin/', admin.site.urls),
    path('transaction/', include('transactions.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
