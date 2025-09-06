from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox

class NewGameDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yeni Oyun")
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Number of decks:"))
        self.decks_input = QSpinBox()
        self.decks_input.setMinimum(1)
        self.decks_input.setValue(8)
        self.layout.addWidget(self.decks_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_decks(self):
        return self.decks_input.value()
