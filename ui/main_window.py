import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from ui.widgets.table_panel import TablePanel
from ui.widgets.shoe_panel import ShoePanel
from ui.widgets.dealer_panel import DealerPanel
from ui.widgets.controls_panel import ControlsPanel
from ui.widgets.player_panel import PlayerPanel

class MainWindow(QMainWindow):
    def __init__(self, facade=None):
        super().__init__()
        self.facade = facade
        self.setWindowTitle("Blackjack EV Karar Motoru")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Left side: Dealer Panel and Player Panels (scrollable)
        left_section_layout = QVBoxLayout()

        self.dealer_panel = DealerPanel(None)
        left_section_layout.addWidget(self.dealer_panel)

        self.table_scroll_area = QScrollArea()
        self.table_scroll_area.setWidgetResizable(True)
        self.table_panel = TablePanel(None)
        self.table_scroll_area.setWidget(self.table_panel)
        left_section_layout.addWidget(self.table_scroll_area)

        # Set left section to take 80% of horizontal space
        self.main_layout.addLayout(left_section_layout, 8)

        # Right side: Shoe and Controls Panels
        right_layout = QVBoxLayout()
        self.shoe_panel = ShoePanel(None)
        self.controls_panel = ControlsPanel(self)
        right_layout.addWidget(self.shoe_panel)
        right_layout.addWidget(self.controls_panel)

        self.main_layout.addLayout(right_layout, 2)

    def set_facade(self, facade):
        self.facade = facade
        self.dealer_panel.facade = facade
        self.table_panel.facade = facade
        self.shoe_panel.facade = facade
        self.controls_panel.main_window = self # Ensure controls panel has correct main_window reference

        # Clear and re-add player panels in TablePanel
        for i in reversed(range(self.table_panel.layout.count())):
            widget = self.table_panel.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.table_panel.player_panels = []
        for i in range(len(self.facade.table.players)):
            player_panel = PlayerPanel(i, self.facade)
            self.table_panel.player_panels.append(player_panel)
            self.table_panel.layout.addWidget(player_panel)

        self.dealer_panel.update_panel()
        self.table_panel.update_panel()
        self.shoe_panel.update_panel()
        self.update_all_panels()

    def update_table_panel(self):
        # Clear existing player panels
        for i in reversed(range(self.table_panel.layout.count())):
            widget = self.table_panel.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.table_panel.player_panels = []
        for i in range(len(self.facade.table.players)):
            player_panel = PlayerPanel(i, self.facade)
            self.table_panel.player_panels.append(player_panel)
            self.table_panel.layout.addWidget(player_panel)

        # Ensure the scroll area updates its content
        self.table_panel.adjustSize()

    def update_all_panels(self):
        self.table_panel.update_panel()
        self.shoe_panel.update_panel()
        self.dealer_panel.update_panel()