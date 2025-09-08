from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QCheckBox

from ui.widgets.draw_card_dialog import DrawCardDialog
from blackjack_ev.utils.card_utils import card_to_name


class HandPanel(QWidget):
    def __init__(self, hand_index, player_panel):
        super().__init__()
        self.hand_index = hand_index
        self.player_panel = player_panel
        self.layout = QVBoxLayout(self)

        self.cards_label = QLabel("Cards:")
        self.cards_label.setStyleSheet("background-color: white; color: black; padding: 5px; border-radius: 3px;")
        self.layout.addWidget(self.cards_label)

        self.total_label = QLabel("Total:")
        self.layout.addWidget(self.total_label)

        self.action_buttons_layout = QHBoxLayout()
        self.hit_button = QPushButton("Hit")
        self.stand_button = QPushButton("Stand")
        self.action_buttons_layout.addWidget(self.hit_button)
        self.action_buttons_layout.addWidget(self.stand_button)
        self.layout.addLayout(self.action_buttons_layout)

        self.ev_label = QLabel("EVs:")
        self.layout.addWidget(self.ev_label)

        self.best_action_label = QLabel("Best Action:")
        self.layout.addWidget(self.best_action_label)

        self.hit_button.clicked.connect(self.hit)
        self.stand_button.clicked.connect(self.stand)

    def update_panel(self):
        player = self.player_panel.facade.table.get_player(self.player_panel.player_index)
        hand = player.hands[self.hand_index]
        card_names = [card_to_name(card) for card in hand.cards]
        self.cards_label.setText(f"Cards: {', '.join(card_names)}")
        self.total_label.setText(f"Total: {hand.total}")

        if not player.ev_enabled:
            self.ev_label.setText("EVs: Disabled")
            self.best_action_label.setText("Best Action: Disabled")
            return

        evs = self.player_panel.facade.engine.compute_ev(self.player_panel.player_index, self.hand_index)
        self.ev_label.setText(f"EVs: {evs}")

        best_action = "None"
        if evs:
            best_action = max(evs, key=lambda action: evs[action] if evs[action] is not None else -float('inf'))
        self.best_action_label.setText(f"Best Action: {best_action}")

    def hit(self):
        dialog = DrawCardDialog()
        if dialog.exec_():
            drawn_card = dialog.get_drawn_card()
            self.player_panel.facade.deal_card_to_player(self.player_panel.player_index, drawn_card, self.hand_index)
            self.player_panel.update_panel()

    def stand(self):
        self.player_panel.facade.next_player_turn()
        self.player_panel.update_panel()


class PlayerPanel(QWidget):
    def __init__(self, player_index, facade):
        super().__init__()
        self.player_index = player_index
        self.facade = facade
        self.layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.player_label = QLabel(f"Player {player_index + 1}")
        header_layout.addWidget(self.player_label)

        self.ev_enabled_checkbox = QCheckBox("Hesaplama Açık")
        self.ev_enabled_checkbox.setChecked(True)
        self.ev_enabled_checkbox.stateChanged.connect(self.toggle_ev_calculation)
        header_layout.addWidget(self.ev_enabled_checkbox)
        self.layout.addLayout(header_layout)

        self.hands_layout = QHBoxLayout()
        self.layout.addLayout(self.hands_layout)

        self.split_button = QPushButton("Split")
        self.layout.addWidget(self.split_button)
        self.split_button.clicked.connect(self.split)

    def toggle_ev_calculation(self, state):
        player = self.facade.table.get_player(self.player_index)
        player.ev_enabled = (state == 2) # 2 is checked, 0 is unchecked
        self.update_panel()

    def update_panel(self):
        if self.facade is None or self.facade.table is None:
            return
        player = self.facade.table.get_player(self.player_index)

        for i in reversed(range(self.hands_layout.count())):
            self.hands_layout.itemAt(i).widget().setParent(None)

        for i, hand in enumerate(player.hands):
            hand_panel = HandPanel(i, self)
            self.hands_layout.addWidget(hand_panel)
            hand_panel.update_panel()

        self.split_button.setEnabled(player.can_split())

    def split(self):
        self.facade.split_player_hand(self.player_index)
        self.update_panel()
