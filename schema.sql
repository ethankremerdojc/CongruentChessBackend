CREATE TABLE IF NOT EXISTS Games (
    game_id SERIAL,
    player_ids TEXT,
    usernames TEXT,
    board_state TEXT NOT NULL,
    winner TEXT,

    PRIMARY KEY (game_id)
);

CREATE TABLE IF NOT EXISTS Moves (
    move_id SERIAL PRIMARY KEY,
    game_id INT,
    is_temp BOOLEAN DEFAULT FALSE,
    val TEXT NOT NULL,

    FOREIGN KEY (game_id) REFERENCES Games(game_id)
);