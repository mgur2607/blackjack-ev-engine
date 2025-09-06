from typing import Tuple

class Shoe:
    def __init__(self, decks: int = 8):
        self.decks = decks
        self.reset()

    def reset(self) -> None:
        self.counts: Tuple[int, ...] = self._initialize_shoe(self.decks)

    def _initialize_shoe(self, decks: int) -> Tuple[int, ...]:
        num_cards = decks * 4
        num_tens = decks * 16
        return (num_cards, num_cards, num_cards, num_cards, num_cards, num_cards, num_cards, num_cards, num_cards, num_tens)

    def get_counts(self) -> Tuple[int, ...]:
        return self.counts

    def deal_card(self, card: int) -> None:
        if self.counts[card - 1] > 0:
            new_counts = list(self.counts)
            new_counts[card - 1] -= 1
            self.counts = tuple(new_counts)
        else:
            raise ValueError(f"No more cards of value {card} in the shoe.")

    def get_total_cards(self) -> int:
        return sum(self.counts)
