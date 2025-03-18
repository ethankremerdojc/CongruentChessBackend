import json
from copy import deepcopy
from validation import is_valid_move

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

def parse_game_request(data):
    try:
        game = {}

        _, time, username = data.split("|")

        game["username"] = username
        game["timePerMove"] = time

        return game
    except Exception as e:
        print(e)
        return

def games_to_str(games):
    return ",".join([f"{game['username']}|{game['timePerMove']}" for game in games])

def encode_board_to_fen(board):
    fen = []
    for row in board:
        empty = 0
        fen_row = ""
        for cell in row:
            if cell is None:
                empty += 1
            else:
                if empty > 0:
                    fen_row += str(empty)
                    empty = 0
                fen_row += cell
        if empty > 0:
            fen_row += str(empty)
        fen.append(fen_row)
    return "/".join(fen)

def to_json_string(data):
    copied = deepcopy(data)

    if copied.get('board_state'):
        copied['board_state'] = encode_board_to_fen(copied['board_state'])

    return json.dumps(copied)

def check_validity(data, game):
    from_pos = data['from']
    to_pos = data['to']

    return is_valid_move(game['board_state'], from_pos, to_pos, data['piece'])

def handle_piece_moves(moves, game):

    if len(moves) != 2:
        raise Exception("Invalid number of moves")
    
    first_move = moves[0]
    second_move = moves[1]

    game['board_state'][first_move['from'][1]][first_move['from'][0]] = None
    game['board_state'][second_move['from'][1]][second_move['from'][0]] = None

    if first_move['to'] == second_move['to']: # Both players are going to the same space.
        both_are_pawns = first_move['piece'].lower() == "p" and second_move['piece'].lower() == "p"
        both_are_not_pawns = first_move['piece'].lower() != "p" and second_move['piece'].lower() != "p"

        if both_are_pawns or both_are_not_pawns:
            game['board_state'][first_move['to'][1]][first_move['to'][0]] = None
        else:
            # Whichever is not a pawn, set that one.
            non_pawn = first_move['piece'] if first_move['piece'].lower() != "p" else second_move['piece']
            game['board_state'][first_move['to'][1]][first_move['to'][0]] = non_pawn
    else:
        for move in moves:
            if move['piece'].lower() == "p":
                if move['from'][0] != move['to'][0]:
                    # Pawn moving diagonally
                    if game['board_state'][move['to'][1]][move['to'][0]] is not None: # A piece is there

                        fm_cond = move == first_move and second_move['from'] != first_move['to']
                        sm_cond = move == second_move and first_move['from'] != second_move['to']

                        if fm_cond or sm_cond : # other piece moved
                            game['board_state'][move['to'][1]][move['to'][0]] = move['piece']

                    else: # Cheating!
                        game['board_state'][move['to'][1]][move['to'][0]] = None
                
                elif game['board_state'][move['to'][1]][move['to'][0]] is None:
                    game['board_state'][move['to'][1]][move['to'][0]] = move['piece']

            else:
                game['board_state'][move['to'][1]][move['to'][0]] = move['piece']

    for move in moves:
        game['moves'].append(move)

def get_previous_selections(moves):
    result = []

    for move in moves:
        result.append(move['from'])
        result.append(move['to'])

    return result

def get_game_state(board):
    white_exists = False
    black_exists = False

    for y in board:
        for x in y:
            if x == "K":
                white_exists = True
            if x == "k":
                black_exists = True

    if not white_exists and not black_exists:
        return "DRAW"
    
    if not black_exists:
        return "WHITE WINS"
    
    if not white_exists:
        return "BLACK WINS"

    return "INCOMPLETE"
    
    