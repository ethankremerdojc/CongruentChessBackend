from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from validation import *
from utils import *
import random
from typing import List, Dict
import json
from copy import deepcopy

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

active_connections: List[tuple[WebSocket, str]] = []
games: List[Dict] = []

# Create an api to return the list of available games to display on the front end menu

def to_json_string(data):

    copied = deepcopy(data)

    if copied.get('board_state'):
        copied['board_state'] = encode_board_to_fen(copied['board_state'])

    return json.dumps(copied)

@app.get("/games")
async def get_games():
    return [game for game in games if len(game['player_ids']) == 1]

@app.post("/start_game")
async def create_game(data: Dict):

    user_id = data['user_id']

    game_id = str(random.randint(1000000000, 9999999999))

    # Todo store moves
    game = {
        "game_id": game_id,
        "player_ids": [int(user_id)],
        "game_state": "NOT_STARTED",
        "board_state": decode_fen_to_board(STARTING_FEN),
        "winner": None,
        "turn": "white"
    }

    games.append(game)

    return game

def get_game_by_game_id(game_id):
    for game in games:
        if game['game_id'] == game_id:
            return game

    return None

def handle_piece_move(data, game):
    from_pos = data['from']
    to_pos = data['to']

    piece = game['board_state'][from_pos[1]][from_pos[0]]
    color = "white" if piece.isupper() else "black"

    if color != game['turn']:
        return "INVALID"

    if is_valid_move(game['board_state'], from_pos, to_pos, piece):
        game['board_state'][from_pos[1]][from_pos[0]] = None
        game['board_state'][to_pos[1]][to_pos[0]] = piece

        game['turn'] = "black" if game['turn'] == "white" else "white"
        return encode_board_to_fen(game['board_state'])

    return "INVALID"

def get_connections_by_game_id(game_id):
    return [connection for connection in active_connections if connection[1] == game_id]

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    active_connections.append((websocket, game_id))

    try:
        while True:
            str_data = await websocket.receive_text()
            data = json.loads(str_data)

            print("Received data: ", data)

            game = get_game_by_game_id(game_id)
            print(game)
            user_id = int(data['user_id'])


            if len(game['player_ids']) == 1 and user_id not in game['player_ids']:

                # if len(game['player_ids']) != 1:
                #     await websocket.send_text(to_json_string(
                #         {"error": "Game is full"})
                #     )
                #     continue

                game['player_ids'].append(user_id)

                # if len(game['player_ids']) == 2:
                #     game['game_state'] = "IN_PROGRESS"
                #     await websocket.send_text(to_json_string(game))
                #     continue
            
            # if int(data['user_id']) not in game['player_ids']:
            #     await websocket.send_text(to_json_string(
            #         {"error": "Invalid player"})
            #     )
            #     continue

            new_fen = handle_piece_move(data, game)
            connections = get_connections_by_game_id(game_id)
            
            if new_fen == "INVALID":
                for connection in connections:
                    await connection[0].send_text(to_json_string(
                        {"error": "Invalid move"})
                    )
            else:
                for connection in connections:
                    await connection[0].send_text(
                        to_json_string(game)
                    )

    except Exception as e:
        print("Failed to connect, or unintended disconnection: ", e)
        active_connections.remove((websocket, game_id))