PIECE_FOR_LETTER = {
    "p": "pawn",
    "r": "rook",
    "n": "knight",
    "b": "bishop",
    "q": "queen",
    "k": "king"
}

def decode_fen_to_board(fen):
    board = []
    rows = fen.split("/")
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                board_row.extend([None] * int(char))
            else:
                board_row.append(char)
        board.append(board_row)
    return board

def get_legal_moves(piece_type, color, position):
    if piece_type == "pawn":
        return get_legal_pawn_moves(color, position)
    elif piece_type == "rook":
        return get_legal_rook_moves(position)
    elif piece_type == "knight":
        return get_legal_knight_moves(position)
    elif piece_type == "bishop":
        return get_legal_bishop_moves(position)
    elif piece_type == "queen":
        return get_legal_queen_moves(position)
    elif piece_type == "king":
        return get_legal_king_moves(position)
    else:
        raise ValueError("Invalid piece type")

def get_legal_pawn_moves(color, position):
    x, y = position
    direction = -1 if color == "white" else 1

    legal_moves = []
    legal_moves.append((x, y + direction))

    if (y == 1 and color == "black") or (y == 6 and color == "white"):
        legal_moves.append((x, y + 2 * direction))

    if x > 0:
        legal_moves.append((x - 1, y + direction))
    if x < 7:
        legal_moves.append((x + 1, y + direction))

    return legal_moves

def get_legal_rook_moves(position):
    x, y = position
    legal_moves = []

    for i in range(8):
        if i != x:
            legal_moves.append((i, y))
        if i != y:
            legal_moves.append((x, i))

    return legal_moves

def get_legal_knight_moves(position):
    x, y = position
    legal_moves = []

    possible_moves = [
        (x + 1, y + 2), (x + 2, y + 1), (x + 2, y - 1), (x + 1, y - 2),
        (x - 1, y - 2), (x - 2, y - 1), (x - 2, y + 1), (x - 1, y + 2)
    ]

    for move in possible_moves:
        mx, my = move
        if 0 <= mx < 8 and 0 <= my < 8:
            legal_moves.append(move)

    return legal_moves

def get_legal_bishop_moves(position):
    x, y = position
    legal_moves = []

    for i in range(1, 8):
        if x + i < 8 and y + i < 8:
            legal_moves.append((x + i, y + i))
        if x + i < 8 and y - i >= 0:
            legal_moves.append((x + i, y - i))
        if x - i >= 0 and y + i < 8:
            legal_moves.append((x - i, y + i))
        if x - i >= 0 and y - i >= 0:
            legal_moves.append((x - i, y - i))

    return legal_moves

def get_legal_queen_moves(position):
    return get_legal_rook_moves(position) + get_legal_bishop_moves(position)

def get_legal_king_moves(position):
    x, y = position
    legal_moves = []

    possible_moves = [
        (x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1),
        (x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1)
    ]

    for move in possible_moves:
        mx, my = move
        if 0 <= mx < 8 and 0 <= my < 8:
            legal_moves.append(move)

    return legal_moves

def is_valid_move(board, from_pos, to_pos, piece):
    print(from_pos, to_pos, piece)

    if piece is None:
        return False

    color = "white" if piece.isupper() else "black"
                    
    piece_type = PIECE_FOR_LETTER[piece.lower()]
    legal_moves = get_legal_moves(piece_type, color, from_pos)

    if (to_pos[0], to_pos[1]) not in legal_moves:
        return False

    return True