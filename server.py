from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from validation import *
from utils import *
import random
from typing import List, Dict

from orm import Games, Moves

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

active_connections: List[tuple[WebSocket, str]] = []
# games: List[Dict] = []

def get_game_by_game_id(game_id):
    return Games.get_by_id(int(game_id))

def get_connections_by_game_id(game_id):
    return [connection for connection in active_connections if connection[1] == game_id]

#? App routes

@app.get("/games")
async def get_open_games():
    open_games = Games.get_open_games()
    return open_games

@app.post("/start_game")
async def create_game(data: Dict):
    user_id = data['user_id']
    username = data['username']

    new_row = (
        str(user_id),
        username,
        STARTING_FEN,
        "NONE"
    )

    Games.add(new_row)

    game = {
        "game_id": game_id,
        "player_ids": [int(user_id)],
        "usernames": {
            int(user_id): username
        },
        "game_state": "NOT STARTED",
        "board_state": decode_fen_to_board(STARTING_FEN),
        "winner": None,
        "moves": [],
        "temp_moves": []
    }

    return game

"""

TODO Another:
If there are no connections alive for some game, kill it.

"""

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

            if game['game_state'] not in ["INCOMPLETE", "NOT STARTED"]:
                print("Game already complete.")
                websocket.send_text(to_json_string({
                    "message": "Game already complete."
                }))
                continue

            user_id = int(data['user_id'])
            username = data['username']

            #! Join game
            if len(game['player_ids']) == 1 and user_id not in game['player_ids']:
                game['player_ids'].append(user_id)
                game['usernames'][user_id] = username

            connections = get_connections_by_game_id(game_id)

            if data['request_type'] == "join":
                print("User attempting to join")

                game['game_state'] = "INCOMPLETE"

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

                        game['game_state'] = get_game_state(game['board_state'])

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