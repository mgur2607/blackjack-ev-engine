from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox
from ui.widgets.new_hand_dialog import NewHandDialog
from ui.widgets.new_game_dialog import NewGameDialog

class ControlsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        self.new_hand_button = QPushButton("Yeni El için Kart Gir")
        self.end_game_button = QPushButton("Oyunu Sonlandır (Yeni Shoe)")
        self.add_player_button = QPushButton("Oyuncu Ekle")
        self.remove_player_button = QPushButton("Oyuncu Sil")
        self.apply_suggestion_button = QPushButton("Öneriyi Uygula")

        self.layout.addWidget(self.new_hand_button)
        self.layout.addWidget(self.end_game_button)
        self.layout.addWidget(self.add_player_button)
        self.layout.addWidget(self.remove_player_button)
        self.layout.addWidget(self.apply_suggestion_button)

        self.new_hand_button.clicked.connect(self.new_hand)
        self.end_game_button.clicked.connect(self.end_game)
        self.add_player_button.clicked.connect(self.add_player)
        self.remove_player_button.clicked.connect(self.remove_player)
        self.apply_suggestion_button.clicked.connect(self.apply_suggestion)

    def new_hand(self):
        dialog = NewHandDialog(len(self.main_window.facade.table.players))
        if dialog.exec_():
            player_cards, dealer_upcard, dealer_downcard = dialog.get_cards()
            self.main_window.facade.new_hand(player_cards, dealer_upcard, dealer_downcard)
            self.main_window.update_all_panels()

    def end_game(self):
        dialog = NewGameDialog()
        if dialog.exec_():
            decks = dialog.get_decks()
            self.main_window.facade.end_game(decks)
            self.main_window.update_all_panels()

    def add_player(self):
        self.main_window.facade.add_player()
        self.main_window.update_table_panel()

    def remove_player(self):
        self.main_window.facade.remove_player()
        self.main_window.update_table_panel()

    def apply_suggestion(self):
        print("Öneriyi Uygula clicked")
