from db import Model
# from pprint import pprint

class Games(Model):
    TABLE_NAME = "GAMES"
    FIELDS = ("game_id", "player_ids", "usernames", "board_state", "winner")
    INSERT_VALUES = ("player_ids", "usernames", "board_state", "winner")

    @classmethod
    def get_open_games(cls):
        return cls.filter(f"""
            SELECT * FROM GAMES
            WHERE NOT player_ids LIKE '%,%;
        """) # There will be a comma if 

class Moves(Model):
    TABLE_NAME = "MOVES"
    FIELDS = ("move_id", "game_id", "is_temp", "val")
    INSERT_VALUES = ("game_id", "is_temp", "val")

# if __name__ == "__main__":
#     all_games = Games.all()

#     pprint(all_games)

#     all_moves = Moves.all()

#     pprint(all_moves)