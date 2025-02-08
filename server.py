from fastapi import FastAPI, WebSocket
from typing import List

app = FastAPI()

# Store active WebSocket connections
active_connections: List[WebSocket] = []

from validation import *

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()

            # check if is fen
            print(data)
            # check if there are 7 slashes in the data, is fen.
            try:
                if data.count("/") == 7:
                    fen, from_pos_str, to_pos_str = data.split("|")



                    board = decode_fen_to_board(fen)
                    from_pos = (int(from_pos_str[0]), int(from_pos_str[2]))
                    to_pos = (int(to_pos_str[0]), int(to_pos_str[2]))

                    if not is_valid_move(board, from_pos, to_pos):
                        print("Invalid move!")
                        continue

                    board[to_pos[1]][to_pos[0]] = board[from_pos[1]][from_pos[0]]
                    board[from_pos[1]][from_pos[0]] = None

                    fen = encode_board_to_fen(board)
                    print(fen)
                    print("Succeed!")
                    for connection in active_connections:
                        await connection.send_text(fen)
                        # Figure out if I want some sort of success message instead

            except Exception as e:
                print(e)
                continue
            
    except Exception as e:
        print(e)
        active_connections.remove(websocket)