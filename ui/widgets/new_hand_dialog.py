from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from blackjack_ev.utils.card_utils import name_to_card

class NewHandDialog(QDialog):
    def __init__(self, num_players):
        super().__init__()
        self.setWindowTitle("Yeni El için Kart Gir")
        self.num_players = num_players
        self.player_cards = []
        self.dealer_upcard = None

        self.layout = QVBoxLayout(self)

        self.player_card_inputs = []
        for i in range(num_players):
            self.layout.addWidget(QLabel(f"Player {i + 1} Cards:"))
            player_card_input = QLineEdit()
            player_card_input.setPlaceholderText("e.g., A, 10, K")
            self.player_card_inputs.append(player_card_input)
            self.layout.addWidget(player_card_input)

        self.layout.addWidget(QLabel("Dealer Upcard:"))
        self.dealer_upcard_input = QLineEdit()
        self.dealer_upcard_input.setPlaceholderText("e.g., 5")
        self.layout.addWidget(self.dealer_upcard_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.custom_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def custom_accept(self):
        temp_player_cards = []
        try:
            # Oyuncu kartlarını doğrula
            for i in range(self.num_players):
                player_input_widget = self.player_card_inputs[i]
                cards_str = player_input_widget.text().strip()
                if not cards_str:
                    QMessageBox.warning(self, "Input Error", f"Please enter cards for Player {i+1}.")
                    return

                card_names = [c.strip().upper() for c in cards_str.split(',') if c.strip()]
                cards = [name_to_card(name) for name in card_names]
                temp_player_cards.append(cards)

            # Krupiye kartını doğrula
            dealer_card_str = self.dealer_upcard_input.text().strip().upper()
            if not dealer_card_str:
                QMessageBox.warning(self, "Input Error", "Please enter the dealer's upcard.")
                return
            
            temp_dealer_upcard = name_to_card(dealer_card_str)

            # Tüm veriler geçerliyse, asıl değişkenlere ata
            self.player_cards = temp_player_cards
            self.dealer_upcard = temp_dealer_upcard
            super().accept() # Pencereyi kapat

        except ValueError:
            valid_inputs = "A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K"
            QMessageBox.warning(self, "Invalid Card", f"You have entered an invalid card.\nPlease use one of the following values: {valid_inputs}")

    def get_cards(self):
        return self.player_cards, self.dealer_upcard