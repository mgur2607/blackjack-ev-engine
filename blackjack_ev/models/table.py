from typing import List, Tuple
from blackjack_ev.models.player import Player
from blackjack_ev.models.shoe import Shoe
from blackjack_ev.models.rules import Rules
from blackjack_ev.models.hand import Hand

class Table:
    def __init__(self, rules: Rules, num_players: int = 1, decks: int = 8):
        self.rules = rules
        self.players: List[Player] = [Player() for _ in range(num_players)]
        self.dealer_cards: List[int] = []
        self.shoe = Shoe(decks)
        self.turn_index: int = 0
        self.log_level: str = "info"

    def new_round(self):
        self.dealer_cards = []
        for player in self.players:
            player.hands = [Hand(())]
            player.active_hand_idx = 0
            player.has_split = False

    @property
    def dealer_hand(self) -> Hand:
        return Hand(tuple(self.dealer_cards))

    def deal_card_to_player(self, player_idx: int, card: int, hand_idx: int | None = None) -> None:
        self.players[player_idx].deal_card(card, hand_idx)
        self.shoe.deal_card(card)

    def deal_card_to_dealer(self, card: int, is_upcard: bool = False) -> None:
        self.dealer_cards.append(card)
        self.shoe.deal_card(card)

    def get_player(self, player_idx: int) -> Player:
        return self.players[player_idx]
