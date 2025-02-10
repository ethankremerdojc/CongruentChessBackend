from fastapi import FastAPI, WebSocket
from typing import List

app = FastAPI()

# Store active WebSocket connections
active_connections: List[WebSocket] = []

"""

implement a dict system so we don't need to iterate through all connections to send a message to a specific one

active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            # Send message back only to the sender
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        del active_connections[client_id]

"""

from validation import *

def is_fen(string):
    return string.count("/") == 7

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    game_requests = [] # Store active games
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                if is_fen(data):
                    fen, from_pos_str, to_pos_str = data.split("|")

                    board = decode_fen_to_board(fen)
                    from_pos = (int(from_pos_str[0]), int(from_pos_str[2]))
                    to_pos = (int(to_pos_str[0]), int(to_pos_str[2]))

                    fen = encode_board_to_fen(board)

                    for connection in active_connections:
                        await connection.send_text(fen)

                elif "NEWGAME" in data: # Game request

                    parsed_game = parse_game_request(data)

                    if parsed_game is not None:
                        game_requests.append(parsed_game)

                    game_requests_str = games_to_str(game_requests)

                    for connection in active_connections:
                        await connection.send_text(game_requests_str)

            except Exception as e:
                print(e)
                continue
            
    except Exception as e:
        print(e)
        active_connections.remove(websocket)