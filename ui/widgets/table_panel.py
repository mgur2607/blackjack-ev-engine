from PyQt5.QtWidgets import QWidget, QVBoxLayout
from ui.widgets.player_panel import PlayerPanel

class TablePanel(QWidget):
    def __init__(self, facade=None):
        super().__init__()
        self.facade = facade
        self.layout = QVBoxLayout(self)

        self.player_panels = []

    def update_panel(self):
        if self.facade is None or self.facade.table is None:
            return
        for player_panel in self.player_panels:
            player_panel.update_panel()
