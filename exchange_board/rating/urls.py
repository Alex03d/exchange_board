# rating/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('rate_after_transaction/<int:transaction_id>/', views.rate_after_transaction, name='rate_after_transaction'),
]
