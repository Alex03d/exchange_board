from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Game
import json


def home(request):
    games = Game.objects.all()
    return render(request, 'tic_tac/home.html', {'games': games})


def new_game(request):
    new_game = Game.objects.create()
    return redirect('tic_tac:tic-tac-toe', new_game.id)


@csrf_exempt
def game_view(request, game_id):
    game = get_object_or_404(Game, pk=game_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            move = int(data.get('move'))
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return HttpResponseBadRequest('Некорректный запрос: ' + str(e))

        if move is not None and 0 <= move < 9 and game.board[move] == ' ':
            game.make_move(move)
            winner = game.check_winner()
            old_move = int(game.x_moves[0]) if len(game.x_moves) > 3 else int(game.o_moves[0]) if len(
                game.o_moves) > 3 else None

            if not winner:
                game.current_player = 'O' if game.current_player == 'X' else 'X'

            if game.current_player == 'X' and len(game.x_moves) == 3:
                next_to_remove = int(game.x_moves[0])
            elif game.current_player == 'O' and len(game.o_moves) == 3:
                next_to_remove = int(game.o_moves[0])
            else:
                next_to_remove = None

            game.save()

            response_data = {
                'board': game.board,
                'current_player': game.current_player,
                'winner': winner,
                'old_move': old_move,
                'next_to_remove': next_to_remove
            }

            if winner:
                response_data['message'] = f'The Winner is: {winner}!'
            return JsonResponse(response_data)

        else:
            return HttpResponseBadRequest('Некорректный ход')

    return render(request, 'tic_tac/tic_tac_toe.html', {'game': game})
