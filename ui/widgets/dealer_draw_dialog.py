from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from blackjack_ev.utils.card_utils import name_to_card

class DealerDrawDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krupiye Kart Ekle")
        self.drawn_cards = []  # Kartları saklamak için

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Krupiyenin Çektiği Kartlar (virgülle ayırın, örn: A, 10, K):"))
        self.drawn_cards_input = QLineEdit()
        self.layout.addWidget(self.drawn_cards_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.custom_accept)  # Değiştirildi
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def custom_accept(self):
        cards_str = self.drawn_cards_input.text().strip()
        if not cards_str:
            # Boş giriş de geçerli olabilir (hiç kart çekilmediyse)
            super().accept()
            return

        card_names = [c.strip().upper() for c in cards_str.split(',') if c.strip()]
        temp_cards = []
        try:
            for card_name in card_names:
                temp_cards.append(name_to_card(card_name))
            
            self.drawn_cards = temp_cards
            super().accept()  # Sadece tüm kartlar geçerliyse kapat
        except ValueError:
            valid_inputs = "A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K"
            QMessageBox.warning(self, "Hatalı Giriş", f"Geçersiz kart bulundu.\nLütfen şu değerlerden birini veya birkaçını virgülle ayırarak girin: {valid_inputs}")
            # Hatalı girişi temizlemiyoruz ki kullanıcı düzeltebilsin

    def get_drawn_cards(self):
        return self.drawn_cards
