from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from validation import *
from utils import *
import random
from typing import List, Dict

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

active_connections: List[tuple[WebSocket, str]] = []
games: List[Dict] = []

def get_game_by_game_id(game_id):
    for game in games:
        if game['game_id'] == game_id:
            return game

    return None

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
        # Remove pawns
        # If pieces are both not pawns remove both

        both_are_pawns = first_move['piece'].lower() == "p" and second_move['piece'].lower() == "p"
        both_are_not_pawns = first_move['piece'].lower() != "p" and second_move['piece'].lower() != "p"

        if both_are_pawns or both_are_not_pawns:
            game['board_state'][first_move['to'][1]][first_move['to'][0]] = None
        else:
            # Whichever is not a pawn, set that one.
            non_pawn = first_move['piece'] if first_move['piece'].lower() != "p" else second_move['piece']
            game['board_state'][first_move['to'][1]][first_move['to'][0]] = non_pawn
    else:
        # First move
        if first_move['piece'].lower() == "p" and first_move['from'][0] != first_move['to'][0]:
            # Pawn moving diagonally
            if game['board_state'][first_move['to'][1]][first_move['to'][0]] is not None: # A piece is there
                game['board_state'][first_move['to'][1]][first_move['to'][0]] = first_move['piece']
            else: # Cheating!
                game['board_state'][first_move['to'][1]][first_move['to'][0]] = None
        else:
            game['board_state'][first_move['to'][1]][first_move['to'][0]] = first_move['piece']

        # Second Move
        if second_move['piece'].lower() == "p" and second_move['from'][0] != second_move['to'][0]:
            # Pawn moving diagonally
            if game['board_state'][second_move['to'][1]][second_move['to'][0]] is not None: # A piece is there
                game['board_state'][second_move['to'][1]][second_move['to'][0]] = second_move['piece']
            else: # Cheating!
                game['board_state'][second_move['to'][1]][second_move['to'][0]] = None            
        else:
            game['board_state'][second_move['to'][1]][second_move['to'][0]] = second_move['piece']

    for move in moves:
        game['moves'].append(move)

def get_previous_selections(moves):
    result = []

    for move in moves:
        result.append(move['from'])
        result.append(move['to'])

    return result

def get_connections_by_game_id(game_id):
    return [connection for connection in active_connections if connection[1] == game_id]

#? App routes

@app.get("/games")
async def get_open_games():
    return [game for game in games if len(game['player_ids']) == 1]

@app.post("/start_game")
async def create_game(data: Dict):
    user_id = data['user_id']
    game_id = str(random.randint(1000000000, 9999999999))

    game = {
        "game_id": game_id,
        "player_ids": [int(user_id)],
        "game_state": "NOT_STARTED",
        "board_state": decode_fen_to_board(STARTING_FEN),
        "winner": None,
        "moves": [],
        "temp_moves": []
    }

    games.append(game)

    return game

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    active_connections.append((websocket, game_id))

    try:
        while True:
            str_data = await websocket.receive_text()
            data = json.loads(str_data)
            print("Received data: ", data)

            #* Game logic

            game = get_game_by_game_id(game_id)
            user_id = int(data['user_id'])

            #! Join game
            if len(game['player_ids']) == 1 and user_id not in game['player_ids']:
                game['player_ids'].append(user_id)

            connections = get_connections_by_game_id(game_id)

            if data['request_type'] == "join":
                print("User attempting to join")
                for connection in connections:
                    await connection[0].send_text(to_json_string({
                        "message": "Player joined game",
                        "user_id": user_id,
                        "assigned_colors": {
                            game['player_ids'][0]: "white",
                            game['player_ids'][1]: "black"
                        }
                    }))

            if data['request_type'] == "move":

                piece = game['board_state'][data['from'][1]][data['from'][0]]
                data['piece'] = piece

                is_valid = check_validity(data, game)

                if is_valid:

                    connections = get_connections_by_game_id(game_id)

                    
                    if len(game['temp_moves']) == 0:
                        game['temp_moves'].append(data)

                        for connection in connections:
                            await connection[0].send_text(
                                to_json_string({
                                    "message": "User submitted move", 
                                    "user_id": user_id
                                })
                            )

                    else:
                        game['temp_moves'].append(data)

                        handle_piece_moves(game['temp_moves'], game)

                        game['previous_selections'] = get_previous_selections(game['temp_moves'])
                        game['temp_moves'] = []
                
                        for connection in connections:
                            await connection[0].send_text(
                                to_json_string(game)
                            )
                else:
                    await websocket.send_text(to_json_string(
                        {"error": "Invalid move"})
                    )
                    continue

    except Exception as e:
        print("Websockets error, killing connection: ", e)
        active_connections.remove((websocket, game_id))