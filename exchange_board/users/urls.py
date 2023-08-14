from django.urls import path
from . import views

urlpatterns = [
    path('register/<uuid:invite_code>/', views.register, name='register_with_invite'),
    path('invite/', views.create_invite, name='create_invite'),
    path('login/', views.login_view, name='login'),
]
