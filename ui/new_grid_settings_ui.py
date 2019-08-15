from PySide2.QtWidgets import *
from PySide2.QtCore import QObject, Signal, Slot
from PySide2.QtGui import *


class NewGridSettings(QDialog):

    def __init__(self, parent=None):
        super(NewGridSettings, self).__init__(parent)
        self.setWindowTitle("Create/Load Grid")

        self.button_group = QButtonGroup(self)

        self.new_grid_radio_button = QRadioButton("New grid", self)
        self.load_grid_radio_button = QRadioButton("Use existing grid", self)

        self.button_group.addButton(self.new_grid_radio_button)
        self.button_group.addButton(self.load_grid_radio_button)


        # Create spin boxes and their labels
        self.width_label = QLabel("Width: ")
        self.width_spin_box = QSpinBox(self)
        self.width_spin_box.setMinimum(4)
        self.width_spin_box.setMaximum(100)
        self.height_label = QLabel("Height: ")
        self.height_spin_box = QSpinBox(self)
        self.height_spin_box.setMinimum(4)
        self.height_spin_box.setMaximum(100)

        self.file_line_edit = QLineEdit(self)
        self.file_line_edit.setPlaceholderText("Insert file name...")
        self.file_load = QToolButton(self)
        self.file_load.setText("...")
        self.file_load.clicked.connect(self.open_file_dialog)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.finish_button = QPushButton("Accept")
        self.finish_button.clicked.connect(self.on_finish_clicked)

        self.id_label = QLabel("Player ID: ")
        self.id_line_edit = QLineEdit(self)

        layout = QGridLayout(self)
        layout.addWidget(self.id_label, 0, 0)
        layout.addWidget(self.id_line_edit, 0, 1)
        layout.addWidget(self.new_grid_radio_button, 1, 0)
        layout.addWidget(self.width_label, 2, 0)
        layout.addWidget(self.width_spin_box, 2, 1)
        layout.addWidget(self.height_label, 3, 0)
        layout.addWidget(self.height_spin_box, 3, 1)
        layout.addWidget(self.load_grid_radio_button, 4, 0)
        layout.addWidget(self.file_line_edit, 5, 0)
        layout.addWidget(self.file_load, 5, 1)
        layout.addWidget(self.cancel_button, 6, 0)
        layout.addWidget(self.finish_button, 6, 1)

        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.button_group.buttonToggled.connect(self.highlight_widgets)

        self.new_grid_radio_button.toggle()
        self.finish_button.setFocus()

    @Slot()
    def on_finish_clicked(self):
        if self.button_group.checkedButton() == self.new_grid_radio_button:
            self.new_grid_requested.emit(self.width_spin_box.value(), self.height_spin_box.value())
        elif self.button_group.checkedButton() == self.load_grid_radio_button:
            self.load_grid_requested.emit(self.file_line_edit.text(), self.id_line_edit.text())
        self.close()

    @Slot()
    def on_cancel_clicked(self):
        self.cancelled.emit()
        self.close()

    def highlight_widgets(self, button):
        was_new_grid = button == self.new_grid_radio_button
        was_load_grid = button == self.load_grid_radio_button

        self.width_label.setEnabled(was_new_grid)
        self.width_spin_box.setEnabled(was_new_grid)
        self.height_label.setEnabled(was_new_grid)
        self.height_spin_box.setEnabled(was_new_grid)

        self.file_line_edit.setEnabled(was_load_grid)
        self.file_load.setEnabled(was_load_grid)

    def open_file_dialog(self):
        filename, filter = QFileDialog.getOpenFileName(self, caption="Select Grid File", filter="*.grd", options=QFileDialog.DontUseNativeDialog)
        self.file_line_edit.setText(filename)

    new_grid_requested = Signal(int, int)
    load_grid_requested = Signal(str, str)
    cancelled = Signal()


