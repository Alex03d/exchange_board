from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path(
        'register/<uuid:invite_code>/',
        views.register,
        name='register_with_invite'),
    path('invite/', views.create_invite, name='create_invite'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('follow/', views.follow_index, name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
]
