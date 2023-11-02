# offers/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('offer/create/',
         views.create_offer,
         name='create_offer'),
    path('offer/<int:offer_id>/',
         views.offer_detail,
         name='offer_detail'
         )
]
