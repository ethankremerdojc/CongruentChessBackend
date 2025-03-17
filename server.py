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
    piece = game['board_state'][from_pos[1]][from_pos[0]]

    return is_valid_move(game['board_state'], from_pos, to_pos, piece)

def handle_piece_move(from_pos, to_pos, game):

    piece = game['board_state'][from_pos[1]][from_pos[0]]
    
    game['board_state'][from_pos[1]][from_pos[0]] = None
    game['board_state'][to_pos[1]][to_pos[0]] = piece

    game['moves'].append({
        "from": from_pos,
        "to": to_pos,
        "piece": piece
    })

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

                is_valid = check_validity(data, game)
                # if valid and the user is first to submit, add to the temp_moves
                # if valid and the user is second to submit, apply both moves
                # if invalid, send error message to just the user who sent invalid move

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

                        for move in game['temp_moves']:
                            handle_piece_move(move['from'], move['to'], game)

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