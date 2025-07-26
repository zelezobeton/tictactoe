import random
import re
import time
import argparse

def replace_char_at_index(string, index, char):
    return string[:index] + char + string[index + 1:]

def create_field_template(n):
    s1 = "+---+"
    s2 = "|   |"
    s3 = "---+"
    s4 = "   |"
    x = n + 1
    field_list = []
    m = (x * 3) - (x - 1) 
    for a in range(m):
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

def put_char_on_field(field, char, indexes):
    START_ROW = 3
    ROW_DISTANCE = 2
    START_CHAR = 6
    CHAR_DISTANCE = 4
    x, y = indexes # indexed from 0
    field_split = field.split("\n")
    row = field_split[x * ROW_DISTANCE + START_ROW]
    field_split[x * ROW_DISTANCE + START_ROW] = replace_char_at_index(row, START_CHAR + y * CHAR_DISTANCE, char)
    return "\n".join(field_split)


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


def player_move(field_cells, char, field, n_int, possible_moves):
    while True:
        move = input("Your move (row index followed by column index separated by comma): ")
        if (m := re.search(r"^(\d+),(\d+)$", move)) is None:
            continue
        x, y = m.group(1), m.group(2)
        x_int, y_int = int(x) - 1, int(y) - 1
        if x_int < 0 or x_int > n_int - 1 or y_int < 0 or y_int > n_int - 1:
            print(f"WARNING: Both values must be between 1 and {n_int}")
            continue
        if field_cells[x_int][y_int][0] is not None:
            print("WARNING: Input must be one of empty fields")
            continue
        else:
            field_cells[x_int][y_int][0] = char
            possible_moves.remove((x_int, y_int))
            return put_char_on_field(field, "x", [x_int, y_int])
            
def computer_move(possible_moves, char, field_cells, player_char, board_size, k, field = None):
    # time.sleep(1)
    # print("Computer move:")
    if (make_strike := prolong_strike(field_cells, char, player_char, k)):
        computer_move = make_strike
    else:
        computer_move = random.choice(possible_moves)
    x, y = computer_move
    field_cells[x][y][0] = char
    possible_moves.remove(computer_move)
    if field is not None:
        return put_char_on_field(field, "o", computer_move)

def generate_field(grid_size):
    field_cells = []
    possible_moves = []
    for x in range(grid_size):
        row = []
        for y in range(grid_size):
            row.append([None, (x, y)])
            possible_moves.append((x,y))
        field_cells.append(row)
    return field_cells, possible_moves

def get_args():
    parser = argparse.ArgumentParser(
                    prog='Tictactoe',
                    description='Get rect by super AI in piskvorky')
    parser.add_argument('-s', choices=['x', 'o'], default="x", help='choose x (goes first) or o')
    parser.add_argument('-m', type=int, default=5, choices=range(1,16), metavar="[1-15]",  help='choose board size')
    parser.add_argument('-k', type=int, default=3, choices=range(1,6), metavar="[1-5]", help='choose stones in row needed to win')
    parser.add_argument('--term', action='store_true', help='use terminal output instead of showing graphic interface')
    return parser.parse_args()


def terminal_main(args):
    k = args.k
    n_int = args.m
    player_char = args.s
    computer_char, player_round = ("o", True) if player_char == "x" else ("x", False)

    # k = None
    # n_int = None
    # player_round = None
    # while True:
    #     input_info = input("Choose board size (1-15), number in row to win (1-15 and smaller or same as board size) and x (goes first) or o, separated by comma: ")
    #     if (m := re.search(r"^(\d+),(\d+),([x|o])$", input_info)) is None:
    #         continue
    #     else:
    #         n_int = int(m.group(1))
    #         k = int(m.group(2))
    #         player_round = True if m.group(3) == "x" else False
    #         if k < 1 or k > 15 or n_int < 1 or n_int > 15 or k > n_int:
    #             continue
    #         break
    
    field = create_field_template(n_int)
    print(field)
    
    field_cells, possible_moves = generate_field(n_int)

    # player_char, computer_char = ("x", "o") if player_round else ("o", "x")
    while True:
        if possible_moves:
            if player_round:
                field = player_move(field_cells, player_char, field, n_int, possible_moves)
                player_round = not player_round
            else:
                field = computer_move(possible_moves, computer_char, field_cells, player_char, n_int, k, field)
                player_round = not player_round
            if (winner_char_and_indices := get_winner(field_cells, k)) is not None:
                print(field)
                print(f"Player {winner_char_and_indices[0]} has {k} strike and is winner!")
                break
            print(field)
        else:
            print("It's a tie!")
            break