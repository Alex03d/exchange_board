from django.urls import path

from . import views

urlpatterns = [
    path('<int:transaction_id>/',
         views.transaction_detail,
         name='transaction_detail'
         ),
    path('<int:transaction_id>/author-upload/',
         views.author_uploads_screenshot,
         name='author_uploads_screenshot'
         ),
    path('<int:transaction_id>/author-assert/',
         views.author_asserts_transfer_done,
         name='author_asserts_transfer_done'
         ),
    path('<int:transaction_id>/accepting-confirm/',
         views.accepting_user_confirms_money_received,
         name='accepting_user_confirms_money_received'
         ),
    path('<int:transaction_id>/author-confirm/',
         views.author_confirms_money_received,
         name='author_confirms_money_received'
         ),
    path('<int:transaction_id>/accepting-upload/',
         views.accepting_user_uploads_screenshot,
         name='accepting_user_uploads_screenshot'
         ),
    path('<int:transaction_id>/accepting-assert/',
         views.accepting_user_asserts_transfer_done,
         name='accepting_user_asserts_transfer_done'
         ),
]
