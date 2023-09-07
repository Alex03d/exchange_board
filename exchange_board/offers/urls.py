# offers/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('offer/create/', views.create_offer, name='create_offer'),
    path('request-transaction/<int:offer_id>/',
             views.create_request_for_transaction,
             name='request_transaction'),
    path('view-request/<int:request_id>/',
         views.view_requests_for_transaction,
         name='view_requests_for_transaction'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('start-transaction/<int:offer_id>/',
         views.start_transaction,
         name='start_transaction'
         ),
    path('transaction/<int:transaction_id>/',
         views.transaction_detail,
         name='transaction_detail'
         ),
    path('offer/<int:offer_id>/',
         views.offer_detail,
         name='offer_detail'
         ),
    path('transaction/<int:transaction_id>/author-upload/',
         views.author_uploads_screenshot,
         name='author_uploads_screenshot'
         ),
    path('transaction/<int:transaction_id>/author-assert/',
         views.author_asserts_transfer_done,
         name='author_asserts_transfer_done'
         ),
    path('transaction/<int:transaction_id>/accepting-confirm/',
         views.accepting_user_confirms_money_received,
         name='accepting_user_confirms_money_received'
         ),
    path('transaction/<int:transaction_id>/author-confirm/',
         views.author_confirms_money_received,
         name='author_confirms_money_received'
         ),
    path('transaction/<int:transaction_id>/accepting-upload/',
         views.accepting_user_uploads_screenshot,
         name='accepting_user_uploads_screenshot'
         ),
    path('transaction/<int:transaction_id>/accepting-assert/',
         views.accepting_user_asserts_transfer_done,
         name='accepting_user_asserts_transfer_done'
         ),
]
