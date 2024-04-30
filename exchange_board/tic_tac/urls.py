from django.urls import path
from .views import game_view, new_game, home

app_name = 'tic_tac'

urlpatterns = [
    path('', home, name='home'),
    path('game/new/', new_game, name='new_game'),
    path('game/<int:game_id>/', game_view, name='tic-tac-toe'),
]
