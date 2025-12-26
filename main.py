# 2 handed game

import i3ipc
import time
import numpy as np
from PIL import Image, ImageGrab
import os

import tensorflow
from tensorflow.keras.utils import load_img, img_to_array
from tensorflow.keras.models import load_model

from models import Card, Rank, Suit, HoleCards, Board, Player, GameState

model = load_model("models/model_1.h5")
labels = ['ace of clubs', 'ace of diamonds', 'ace of hearts', 'ace of spades', 'eight of clubs', 'eight of diamonds', 'eight of hearts', 'eight of spades', 'five of clubs', 'five of diamonds', 'five of hearts', 'five of spades', 'four of clubs', 'four of diamonds', 'four of hearts', 'four of spades', 'jack of clubs', 'jack of diamonds', 'jack of hearts', 'jack of spades', 'joker', 'king of clubs', 'king of diamonds', 'king of hearts', 'king of spades', 'nine of clubs', 'nine of diamonds', 'nine of hearts', 'nine of spades', 'queen of clubs', 'queen of diamonds', 'queen of hearts', 'queen of spades', 'seven of clubs', 'seven of diamonds', 'seven of hearts', 'seven of spades', 'six of clubs', 'six of diamonds', 'six of hearts', 'six of spades', 'ten of clubs', 'ten of diamonds', 'ten of hearts', 'ten of spades', 'three of clubs', 'three of diamonds', 'three of hearts', 'three of spades', 'two of clubs', 'two of diamonds', 'two of hearts', 'two of spades']

# COORDS are (X_of_top_left_first_card, X_of_top_left_second_card,Y_of_top_cards, Width, Height )
COORDS_PLAYERS = {
    "1": (155, 215, 380, 60, 85),
    "2": (1325, 1388, 380, 60, 85),
}

COORDS_COMMUNITY = {
    "flop": (592, 680, 770, 426, 75, 110),
    "turn": (850, 0, 0, 426, 75, 110),
    "river": (940, 0, 0, 426, 75, 110),
}

WS_POKER = 6
WS_ORIG = 2

i3: i3ipc.Connection | None = None

def ws_i3(num: int) -> None:
    if i3:
        i3.command(f"workspace {num}")


def get_image(left: int, top: int, width: int, height: int, title: str) -> None:
    ws_i3(WS_POKER)
    time.sleep(0.5)

    printscreen_pil = ImageGrab.grab(bbox=(left, top, left + width, top + height))
    printscreen_pil.save(f"board/{title}.png")

    ws_i3(WS_ORIG)



def recognize_card(image_path: str) -> Card | None:
    path = os.path.join(image_path)

    ## Loading and converting image to array.
    img = load_img(path, target_size = (224, 224))
    img_arr = img_to_array(img)
    img_arr = img_arr/224.0

    ## Expanding array dimension and arragement.
    img_arr = np.expand_dims(img_arr, axis = 0)
    img_arr = np.vstack([img_arr])

    ## Make prediction. 
    pred = model.predict(img_arr)
    pred_value = np.argmax(pred[0])
    card_name = labels[pred_value]
    print(f"Model prediction ---> {pred_value}")
    print(f"The card is a: {card_name}")
    print(f"Img path is {image_path}")
    return None


def capture_all_images() -> None:
    """Capture all card images from the poker table."""
    # Player cards
    (x1, x2, y, w, h) = COORDS_PLAYERS["1"]
    get_image(x1, y, w, h, "player1L")
    get_image(x2, y, w, h, "player1R")

    (x1, x2, y, w, h) = COORDS_PLAYERS["2"]
    get_image(x1, y, w, h, "player2L")
    get_image(x2, y, w, h, "player2R")

    # Community cards
    (x1, x2, x3, y, w, h) = COORDS_COMMUNITY["flop"]
    get_image(x1, y, w, h, "flop1")
    get_image(x2, y, w, h, "flop2")
    get_image(x3, y, w, h, "flop3")

    (x1, x2, x3, y, w, h) = COORDS_COMMUNITY["turn"]
    get_image(x1, y, w, h, "turn")

    (x1, x2, x3, y, w, h) = COORDS_COMMUNITY["river"]
    get_image(x1, y, w, h, "river")


def scrape_game() -> GameState:
    """Scrape the current game state from captured images."""
    game = GameState()

    # Scrape player 1
    card1 = recognize_card("board/player1L.png")
    card2 = recognize_card("board/player1R.png")
    game.players[1] = Player(id=1, hole_cards=HoleCards(card1, card2))

    # Scrape player 2
    card1 = recognize_card("board/player2L.png")
    card2 = recognize_card("board/player2R.png")
    game.players[2] = Player(id=2, hole_cards=HoleCards(card1, card2))

    # Scrape flop
    f1 = recognize_card("board/flop1.png")
    f2 = recognize_card("board/flop2.png")
    f3 = recognize_card("board/flop3.png")
    if f1 and f2 and f3:
        game.board.flop = (f1, f2, f3)

    # Scrape turn
    game.board.turn = recognize_card("board/turn.png")

    # Scrape river
    game.board.river = recognize_card("board/river.png")

    return game


if __name__ == "__main__":
    i3 = i3ipc.Connection()

    # Capture images
    capture_all_images()

    # Build game state from captured images
    game = scrape_game()
    print(game)
