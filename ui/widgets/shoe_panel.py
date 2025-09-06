from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from blackjack_ev.models.shoe import Shoe

class ShoePanel(QWidget):
    def __init__(self, facade=None):
        super().__init__()
        self.facade = facade
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Shoe Panel")
        self.layout.addWidget(self.label)

        self.card_labels = {}
        self.card_progress_bars = {}

        for i in range(1, 11):
            card_label = QLabel(f"Card {i}:")
            self.card_labels[i] = card_label
            self.layout.addWidget(card_label)

            card_progress_bar = QProgressBar()
            self.card_progress_bars[i] = card_progress_bar
            self.layout.addWidget(card_progress_bar)

        

    def update_panel(self):
        shoe_counts = self.facade.table.shoe.get_counts()
        total_cards = self.facade.table.shoe.get_total_cards()
        initial_counts = self.facade.table.shoe._initialize_shoe(self.facade.table.shoe.decks)

        for i in range(1, 11):
            count = shoe_counts[i-1]
            initial_count = initial_counts[i-1]
            percentage = (count / initial_count) * 100 if initial_count > 0 else 0
            self.card_labels[i].setText(f"Card {i}: {count}")
            self.card_progress_bars[i].setValue(int(percentage))
