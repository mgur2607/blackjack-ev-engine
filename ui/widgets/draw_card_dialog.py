from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
from blackjack_ev.utils.card_utils import name_to_card

class DrawCardDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kart Çek")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Çekilen Kart:"))
        self.drawn_card_input = QLineEdit()
        self.layout.addWidget(self.drawn_card_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_drawn_card(self):
        return name_to_card(self.drawn_card_input.text().strip())
