from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from blackjack_ev.utils.card_utils import card_to_name

class DealerPanel(QWidget):
    def __init__(self, facade=None):
        super().__init__()
        self.facade = facade
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Dealer Panel")
        self.layout.addWidget(self.label)

        self.dealer_cards_label = QLabel("Dealer Cards:")
        self.dealer_cards_label.setStyleSheet("background-color: white; color: black; padding: 5px; border-radius: 3px;")
        self.layout.addWidget(self.dealer_cards_label)

    def update_panel(self):
        if self.facade is None or self.facade.table is None:
            return
        dealer_cards = self.facade.table.dealer_cards
        card_names = [card_to_name(card) for card in dealer_cards]
        self.dealer_cards_label.setText(f"Dealer Cards: {', '.join(card_names)}")
