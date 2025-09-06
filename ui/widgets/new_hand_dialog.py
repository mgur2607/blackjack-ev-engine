from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from blackjack_ev.utils.card_utils import name_to_card

class NewHandDialog(QDialog):
    def __init__(self, num_players):
        super().__init__()
        self.setWindowTitle("Yeni El için Kart Gir")
        self.layout = QVBoxLayout(self)

        self.player_card_inputs = []
        for i in range(num_players):
            self.layout.addWidget(QLabel(f"Player {i + 1} Cards:"))
            player_card_input = QLineEdit()
            self.player_card_inputs.append(player_card_input)
            self.layout.addWidget(player_card_input)

        self.layout.addWidget(QLabel("Dealer Upcard:"))
        self.dealer_upcard_input = QLineEdit()
        self.layout.addWidget(self.dealer_upcard_input)

        self.layout.addWidget(QLabel("Dealer Downcard:"))
        self.dealer_downcard_input = QLineEdit()
        self.layout.addWidget(self.dealer_downcard_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_cards(self):
        player_cards = []
        for player_card_input in self.player_card_inputs:
            cards_str = player_card_input.text().split(',')
            cards = []
            for card_name in cards_str:
                card_name = card_name.strip()
                if card_name:
                    cards.append(name_to_card(card_name))
            player_cards.append(cards)

        dealer_upcard = name_to_card(self.dealer_upcard_input.text().strip())
        dealer_downcard = name_to_card(self.dealer_downcard_input.text().strip())

        return player_cards, dealer_upcard, dealer_downcard
