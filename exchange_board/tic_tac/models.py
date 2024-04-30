from django.db import models


class Game(models.Model):
    board = models.CharField(max_length=9, default=" " * 9)
    current_player = models.CharField(max_length=1, default='X')
    x_moves = models.CharField(max_length=9, default='')
    o_moves = models.CharField(max_length=9, default='')

    def make_move(self, move):

        moves = self.x_moves if self.current_player == 'X' else self.o_moves
        moves = moves + str(move) if moves else str(move)
        board_list = list(self.board)
        if len(moves) > 3:
            oldest_move = int(moves[0])
            board_list[oldest_move] = ' '
            moves = moves[1:]
        board_list[move] = self.current_player
        self.board = ''.join(board_list)

        if self.current_player == 'X':
            self.x_moves = moves
        else:
            self.o_moves = moves

    def check_winner(self):
        lines = [
            self.board[0:3], self.board[3:6], self.board[6:9],
            self.board[0::3], self.board[1::3], self.board[2::3],
            self.board[0::4], self.board[2:7:2]
        ]
        for line in lines:
            if line.count(line[0]) == 3 and line[0] != ' ':
                return line[0]
        return None

    def __str__(self):
        return f"Game {self.id}"
