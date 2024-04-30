from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('offers.urls')),
    path('users/', include('users.urls')),
    path('rating/', include('rating.urls')),
    path('admin/', admin.site.urls),
    path('transaction/', include('transactions.urls')),
    path('request/', include('requests_for_transaction.urls')),
    path('tic-tac-toe/', include('tic_tac.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
