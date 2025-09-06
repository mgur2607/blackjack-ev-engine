import sys
from PyQt5.QtWidgets import QApplication
from blackjack_ev.core.ev_calculator import Engine
from blackjack_ev.models.rules import Rules
from blackjack_ev.models.table import Table
from blackjack_ev.models.hand import Hand
from blackjack_ev.models.player import Player
from ui.main_window import MainWindow

class EngineFacade:
    def __init__(self, rules: Rules, main_window, num_players: int = 1, decks: int = 8):
        self.table = Table(rules, num_players, decks)
        self.engine = Engine(self.table)
        self.main_window = main_window

    def __getattr__(self, name):
        return getattr(self.engine, name)

    def deal_card_to_player(self, player_idx: int, card: int, hand_idx: int | None = None) -> None:
        self.table.deal_card_to_player(player_idx, card, hand_idx)
        # After dealing a card, update all panels to reflect the new shoe state
        self.main_window.update_all_panels()

    def next_player_turn(self):
        self.table.turn_index = (self.table.turn_index + 1) % len(self.table.players)

    def split_player_hand(self, player_idx: int):
        self.table.players[player_idx].split_hand()

    def add_player(self):
        self.table.players.append(Player())

    def remove_player(self):
        if len(self.table.players) > 1:
            self.table.players.pop()

    def new_hand(self, player_cards, dealer_upcard):
        self.table.new_round()
        for i, cards in enumerate(player_cards):
            for card in cards:
                self.table.deal_card_to_player(i, card)
        self.table.deal_card_to_dealer(dealer_upcard, is_upcard=True)
        self.main_window.update_all_panels()

    def end_hand(self):
        return self.engine.end_hand()

    def end_game(self, decks):
        self.table = Table(self.table.rules, len(self.table.players), decks)
        self.engine = Engine(self.table)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    rules = Rules()
    window = MainWindow() # Initialize without facade
    facade = EngineFacade(rules, window)
    window.set_facade(facade) # Set facade after it's created
    window.show()
    sys.exit(app.exec_())