from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from blackjack_ev.utils.card_utils import name_to_card

class DrawCardDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kart Çek")
        self.drawn_card = None  # Kart değerini saklamak için

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Çekilen Kart:"))
        self.drawn_card_input = QLineEdit()
        self.layout.addWidget(self.drawn_card_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.custom_accept)  # Değiştirildi
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def custom_accept(self):
        card_text = self.drawn_card_input.text().strip().upper()
        if not card_text:
            QMessageBox.warning(self, "Hatalı Giriş", "Lütfen bir kart girin.")
            return

        try:
            # Kartı doğrula ve sakla
            self.drawn_card = name_to_card(card_text)
            # Sadece başarılı olursa pencereyi kapat
            super().accept()
        except ValueError:
            valid_inputs = "A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K"
            QMessageBox.warning(self, "Hatalı Giriş", f"Geçersiz kart: '{card_text}'.\nLütfen şu değerlerden birini girin: {valid_inputs}")
            self.drawn_card_input.clear()

    def get_drawn_card(self):
        # Saklanan değeri döndür
        return self.drawn_card
