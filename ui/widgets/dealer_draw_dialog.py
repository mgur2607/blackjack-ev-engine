from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from blackjack_ev.utils.card_utils import name_to_card

class DealerDrawDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krupiye Kart Ekle")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Krupiyenin Çektiği Kartlar (virgülle ayırın, örn: A, 10, K):"))
        self.drawn_cards_input = QLineEdit()
        self.layout.addWidget(self.drawn_cards_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_drawn_cards(self):
        cards_str = self.drawn_cards_input.text().split(',')
        cards = []
        for card_name in cards_str:
            card_name = card_name.strip()
            if card_name:
                cards.append(name_to_card(card_name))
        return cards
