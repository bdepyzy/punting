from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Suit(Enum):
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"


class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


@dataclass
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"

    def __repr__(self) -> str:
        return f"Card({self})"


@dataclass
class HoleCards:
    card1: Optional[Card] = None
    card2: Optional[Card] = None

    def __str__(self) -> str:
        c1 = str(self.card1) if self.card1 else "??"
        c2 = str(self.card2) if self.card2 else "??"
        return f"{c1} {c2}"


@dataclass
class Board:
    flop: Optional[tuple[Card, Card, Card]] = None
    turn: Optional[Card] = None
    river: Optional[Card] = None

    @property
    def street(self) -> str:
        if self.river:
            return "river"
        if self.turn:
            return "turn"
        if self.flop:
            return "flop"
        return "preflop"

    @property
    def cards(self) -> list[Card]:
        """Return all community cards currently on the board."""
        result: list[Card] = []
        if self.flop:
            result.extend(self.flop)
        if self.turn:
            result.append(self.turn)
        if self.river:
            result.append(self.river)
        return result

    def __str__(self) -> str:
        if not self.flop:
            return "[]"
        parts = [str(c) for c in self.flop]
        if self.turn:
            parts.append(str(self.turn))
        if self.river:
            parts.append(str(self.river))
        return "[" + " ".join(parts) + "]"


@dataclass
class Player:
    id: int
    hole_cards: HoleCards = field(default_factory=HoleCards)
    stack: Optional[float] = None

    def __str__(self) -> str:
        return f"Player {self.id}: {self.hole_cards}"


@dataclass
class GameState:
    players: dict[int, Player] = field(default_factory=dict)
    board: Board = field(default_factory=Board)
    pot: Optional[float] = None

    def __str__(self) -> str:
        lines = [f"Street: {self.board.street}", f"Board: {self.board}"]
        if self.pot is not None:
            lines.append(f"Pot: {self.pot}")
        for player in self.players.values():
            lines.append(str(player))
        return "\n".join(lines)
