import random
import re
import time
import argparse

def replace_char_at_index(string, index, char):
    return string[:index] + char + string[index + 1:]

def get_diagonals_both_directions(matrix):
    rows = len(matrix)
    cols = len(matrix[0]) if matrix else 0

    diags = []
    # Top-left to bottom-right diagonals (↘️)
    for d in range(rows + cols - 1):
        diag = []
        for i in range(max(0, d - cols + 1), min(rows, d + 1)):
            j = d - i
            diag.append(matrix[i][j])
        diags.append(diag)

    # Top-right to bottom-left diagonals (↙️)
    for d in range(rows + cols - 1):
        diag = []
        for i in range(max(0, d - cols + 1), min(rows, d + 1)):
            j = cols - 1 - (d - i)
            diag.append(matrix[i][j])
        diags.append(diag)

    return diags

def is_winning_strike(k, l):
    i = 0
    strike_char = None
    indices_list = []
    for char, indices in l:
        if char is None:
            i = 0
            strike_char = None
            indices_list = []
        else:
            if strike_char is None:
                strike_char = char
                i += 1
                indices_list.append(indices)
            else:
                if char == strike_char:
                    i += 1
                    indices_list.append(indices)
                # When another char spoils strike, its strike must be started
                else:
                    i = 1
                    strike_char = char
                    indices_list = [indices]
        if i == k:
            return strike_char, indices_list
    return None


def get_winner(field_cells, k):
    columns = [list() for _ in range(len(field_cells))]
    for row in field_cells:
        if (char_and_indices := is_winning_strike(k, row)) is not None:
            return char_and_indices
        for n, x in enumerate(row):
            columns[n].append(x)
    for col in columns:
        if (char_and_indices := is_winning_strike(k, col)) is not None:
            return char_and_indices

    for diag in get_diagonals_both_directions(field_cells):
        if (char_and_indices := is_winning_strike(k, diag)) is not None:
            return char_and_indices
    
    return None

def indices_to_prolong_longest_strike(l):
    # NOTE: Algorithm will return also potential strikes 
    # that are limited and can't grow to k-strike 
    # NOTE: Output lists can be later processed to look for cell with multiple 
    # possible strikes (fork) to find more optimal moves
    strike_info_list = []
    i = 0
    strike_char = None
    free_indices_before = None
    for char, indices in l:
        # Cell is free
        if char is None:
            # No strike has been started yet, but save index of current None 
            # in case it will start in next cycle
            if strike_char is None:
                free_indices_before = indices
            # Strike was ended, so save its info
            else:
                strike_info_list.append((i, strike_char, free_indices_before, indices))
                free_indices_before = indices # Middle free cell can be also beginning of new potential strike
            i = 0
            strike_char = None
        # Cell is filled
        else:
            # First char of potential strike was found
            if strike_char is None:
                strike_char = char
                i += 1
            else:
                # Strike is prolonged
                if char == strike_char:
                    i += 1
                # When another char spoils strike, its strike must be started,
                # and 
                else:
                    # Strike can't continue on end, but maybe it can on start,
                    # so save its info
                    if free_indices_before is not None:
                        strike_info_list.append((i, strike_char, free_indices_before, None))
                    i = 1
                    strike_char = char
                    free_indices_before = None # Before is just different char, no free cell

    # Case when strike is on the end of list
    if i > 0 and free_indices_before is not None:
        strike_info_list.append((i, strike_char, free_indices_before, None))

    return strike_info_list

def prolong_strike(field_cells, comp_char, player_char, k):
    potential_strikes_list = []
    columns = [list() for _ in range(len(field_cells))]
    for row in field_cells:
        potential_strikes_list += indices_to_prolong_longest_strike(row)
        for n, x in enumerate(row):
            columns[n].append(x)
    for col in columns:
        potential_strikes_list += indices_to_prolong_longest_strike(col)

    for diag in get_diagonals_both_directions(field_cells):
        potential_strikes_list += indices_to_prolong_longest_strike(diag)
    
    biggest_comp_tuple, biggest_player_tuple = None, None
    for i, char, before, after in potential_strikes_list:
        if char == comp_char:
            if biggest_comp_tuple is None:
                biggest_comp_tuple = (i, char, before, after)
            elif biggest_comp_tuple[0] < i:
                biggest_comp_tuple = (i, char, before, after)
        elif char == player_char:
            if biggest_player_tuple is None:
                biggest_player_tuple = (i, char, before, after)
            elif biggest_player_tuple[0] < i:
                biggest_player_tuple = (i, char, before, after)
    
    # Block player only if he has bigger strike than computer,
    # or on start with only player char on field,
    # else make computer biggest strike bigger
    if biggest_comp_tuple is not None:
        if biggest_player_tuple is not None and biggest_comp_tuple[0] < biggest_player_tuple[0]:
            return biggest_player_tuple[2] if biggest_player_tuple[2] is not None else biggest_player_tuple[3]
        return biggest_comp_tuple[2] if biggest_comp_tuple[2] is not None else biggest_comp_tuple[3]
    if biggest_player_tuple is not None:
        return biggest_player_tuple[2] if biggest_player_tuple[2] is not None else biggest_player_tuple[3]

def player_move(field):
    while True:
        move = input("Your move (row index followed by column index separated by comma): ")
        if (m := re.search(r"^(\d+),(\d+)$", move)) is None:
            continue
        x, y = m.group(1), m.group(2)
        x_int, y_int = int(x) - 1, int(y) - 1
        if x_int < 0 or x_int > field.m - 1 or y_int < 0 or y_int > field.m - 1:
            print(f"WARNING: Both values must be between 1 and {field.m}")
            continue
        if not field.is_cell_free(x_int, y_int):
            print("WARNING: Input must be one of empty fields")
            continue
        else:
            field.put_char_on_field(x_int, y_int)
            field.change_turn()
            break
            
def computer_move(field):
    if (make_strike := prolong_strike(field.cells, field.computer_char, field.player_char, field.k)):
        computer_move = make_strike
    else:
        computer_move = random.choice(field.possible_moves)
    x, y = computer_move
    field.put_char_on_field(x, y, False)
    field.change_turn()

class Field:
    def __init__(self, m = None, k = None, player_char = None):
        self._cells = []
        self._possible_moves = []

        self.m = m
        self.k = k
        self.player_char = player_char

    def generate_from_input(self):
        if self.m is None or self.k is None or self.player_char is None:
            raise(Exception("Board size, stones in row or player character were not input"))
        self._cells = []
        self._possible_moves = []
        for x in range(self.m):
            row = []
            for y in range(self.m):
                row.append([None, (x, y)])
                self._possible_moves.append((x,y))
            self._cells.append(row)
        self.computer_char, self.player_turn = ("o", True) if self.player_char == "x" else ("x", False)

    def change_turn(self):
        self.player_turn = not self.player_turn

    def is_cell_free(self, x, y):
        return self._cells[x][y][0] is None
    
    @property
    def cells(self):
        return self._cells
    
    @property
    def possible_moves(self):
        return self._possible_moves

    def put_char_on_field(self, x, y, player=True):
        char = self.player_char if player else self.computer_char
        self._cells[x][y][0] = char
        self.possible_moves.remove((x, y))

class TerminalField(Field):
    def __init__(self, m, k, player_char):
        super().__init__(m, k, player_char)
        self.generate_from_input()
        self.printable_field = self.create_printable_field()

    def put_char_on_field(self, x, y, player=True):
        char = self.player_char if player else self.computer_char
        self._cells[x][y][0] = char
        self.possible_moves.remove((x, y))
        self.update_printable_field(x, y, char)

    def update_printable_field(self, x, y, char):
        START_ROW = 3
        ROW_DISTANCE = 2
        START_CHAR = 6
        CHAR_DISTANCE = 4
        field_split = self.printable_field.split("\n")
        row = field_split[x * ROW_DISTANCE + START_ROW]
        field_split[x * ROW_DISTANCE + START_ROW] = replace_char_at_index(row, START_CHAR + y * CHAR_DISTANCE, char)
        self.printable_field = "\n".join(field_split)

    def print(self):
        print(self.printable_field)
        
    def create_printable_field(self):
        s1 = "+---+"
        s2 = "|   |"
        s3 = "---+"
        s4 = "   |"
        x = self.m + 1
        field_list = []
        n = (x * 3) - (x - 1) 
        for a in range(n):
            if a % 2 == 0:
                row = []
                for b in range(x):
                    if b == 0:
                        row.append(s1)
                    else:
                        row.append(s3)
            else:
                row = []
                for b in range(x):
                    if b == 0 and a == 1:
                        row.append(s2)
                    elif b == 0 and a > 1:
                        row.append(f"|{(a - 1) // 2:{" "}>3}|")
                    else:
                        if a == 1:
                            row.append(f"{b:{" "}>3}|")
                        else:
                            row.append(s4)
            field_list.append("".join(row))
        return "\n".join(field_list)

def get_args():
    parser = argparse.ArgumentParser(
        prog='Tictactoe',
        description='Get rect by super AI in piskvorky'
    )
    parser.add_argument('-s', choices=['x', 'o'], default="x", help='choose x (goes first) or o')
    parser.add_argument('-m', type=int, default=5, choices=range(1,16), metavar="[1-15]",  help='choose board size')
    parser.add_argument('-k', type=int, default=3, choices=range(1,6), metavar="[1-5]", help='choose stones in row needed to win')
    parser.add_argument('--term', action='store_true', help='use terminal output instead of showing graphic interface')
    return parser.parse_args()

def terminal_main(args):
    field = TerminalField(args.m, args.k, args.s)
    field.print()

    while True:
        # Game is afoot!
        if field.possible_moves:
            if field.player_turn:
                player_move(field)
            else:
                print("Computer move:")
                computer_move(field)
                # time.sleep(0.5)
            if (winner_char_and_indices := get_winner(field.cells, field.k)) is not None:
                field.print()
                print(f"Player {winner_char_and_indices[0]} has {field.k} strike and is winner!")
                break
            field.print()
        else:
            print("It's a tie!")
            break