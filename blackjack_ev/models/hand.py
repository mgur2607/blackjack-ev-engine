from typing import Tuple

class Hand:
    def __init__(self, cards: Tuple[int, ...]):
        self.cards = cards

    @property
    def total(self) -> int:
        total = sum(self.cards)
        if self.is_soft:
            if total + 10 <= 21:
                total += 10
        return total

    @property
    def is_soft(self) -> bool:
        return 1 in self.cards and sum(self.cards) + 10 <= 21

    @property
    def is_initial_two(self) -> bool:
        return len(self.cards) == 2

    def add_card(self, card: int) -> 'Hand':
        return Hand(self.cards + (card,))
