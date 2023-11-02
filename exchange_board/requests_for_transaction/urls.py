# requests_for_transaction/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('request-transaction/<int:offer_id>/',
         views.create_request_for_transaction,
         name='request_transaction'),
    path('<int:offer_id>/request_transaction/',
         views.create_request_for_transaction,
         name='create_request_for_transaction'),
    path('view-request/<int:request_id>/',
         views.view_requests_for_transaction,
         name='view_requests_for_transaction'),
    path('accept-request/<int:request_id>/',
         views.accept_request,
         name='accept_request'),
    path('reject-request/<int:request_id>/',
         views.reject_request,
         name='reject_request'),
    path('start-transaction/<int:offer_id>/',
         views.start_transaction,
         name='start_transaction'
         ),
]
