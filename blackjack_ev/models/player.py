from typing import List
from blackjack_ev.models.hand import Hand

class Player:
    def __init__(self):
        self.hands: List[Hand] = [Hand(())]
        self.active_hand_idx: int = 0
        self.has_split: bool = False
        self.ev_enabled: bool = True

    def deal_card(self, card: int, hand_idx: int | None = None) -> None:
        if hand_idx is None:
            hand_idx = self.active_hand_idx
        self.hands[hand_idx] = self.hands[hand_idx].add_card(card)

    def split_hand(self) -> None:
        if not self.can_split():
            raise ValueError("Cannot split hand.")

        self.has_split = True
        card1 = self.hands[0].cards[0]
        card2 = self.hands[0].cards[1]
        self.hands = [Hand((card1,)), Hand((card2,))]

    def can_split(self) -> bool:
        return self.hands[0].is_initial_two and self.hands[0].cards[0] == self.hands[0].cards[1]

    def get_active_hand(self) -> Hand:
        return self.hands[self.active_hand_idx]
