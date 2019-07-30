from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from edict import Broadcaster
from utils import MoveDirection


class ButtonClusterUI(QWidget):
    def __init__(self, parent=None):
        super(ButtonClusterUI, self).__init__(parent)
        self.direction_buttons = []
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.grid_layout = QGridLayout(self)
        self.up_button = QToolButton(self)
        self.up_button.setText("↑")
        self.up_button.setFixedSize(60, 60)

        self.down_button = QToolButton(self)
        self.down_button.setText("↓")
        self.down_button.setFixedSize(60, 60)

        self.left_button = QToolButton(self)
        self.left_button.setText("←")
        self.left_button.setFixedSize(60, 60)

        self.right_button = QToolButton(self)
        self.right_button.setText("→")
        self.right_button.setFixedSize(60, 60)

        self.wait_button = QToolButton(self)
        self.wait_button.setText("Wait")
        self.wait_button.setFixedSize(60, 60)

        self.direction_buttons.extend([self.up_button, self.down_button, self.left_button, self.right_button, self.wait_button])
        for button in self.direction_buttons:
            button.setCheckable(True)
            self.button_group.addButton(button)

        self.go_button = QToolButton(self)
        self.go_button.setText("Next (1" + u"\U0001F4B0" + ")")
        self.go_button.setFont(QFont("Helvetica", 16))
        self.go_button.setFixedSize(180, 60)

        self.grid_layout.setColumnMinimumWidth(0, 50)
        self.grid_layout.setColumnMinimumWidth(1, 50)
        self.grid_layout.setColumnMinimumWidth(2, 50)

        self.grid_layout.addWidget(self.up_button, 0, 1, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.down_button, 2, 1, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.left_button, 1, 0, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.right_button, 1, 2, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.wait_button, 1, 1, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.go_button, 3, 0, 3, 0, Qt.AlignHCenter)

        self.setLayout(self.grid_layout)

        self.button_group.buttonToggled.connect(self.set_button_pressed)

        self.current_direction = None


    def set_button_pressed(self, button, checked):
        if checked is False:
            return
        elif button == self.up_button:
            self.current_direction = MoveDirection.UP
        elif button == self.down_button:
            self.current_direction = MoveDirection.DOWN
        elif button == self.left_button:
            self.current_direction = MoveDirection.LEFT
        elif button == self.right_button:
            self.current_direction = MoveDirection.RIGHT
        elif button == self.wait_button:
            self.current_direction = MoveDirection.WAIT
        else:
            self.current_direction = None


class SidePanelUI(QWidget):
    def __init__(self, parent=None):
        super(SidePanelUI, self).__init__(parent)

        v_layout = QVBoxLayout(self)

        self.score_label = QLabel(self)
        self.score_label.setFont(QFont("Helvetica", 24))
        v_layout.addWidget(self.score_label)

        self.logger_text_edit = QTextEdit(self)
        self.logger_text_edit.setReadOnly(True)
        v_layout.addWidget(self.logger_text_edit)

        self.property_label = QLabel(self)
        self.property_label.setFont(QFont("Helvetica", 16))
        v_layout.addWidget(self.property_label)

        self.button_cluster = ButtonClusterUI(self)
        v_layout.addWidget(self.button_cluster)

        self.setLayout(v_layout)



        #######################
        # Edict subscriptions #
        #######################

        Broadcaster().subscribe("/log/raw", self.append_to_log)
        Broadcaster().subscribe("/property_label/raw", self.set_property_label)
        Broadcaster().subscribe("/score_changed", self.set_score)

    def append_to_log(self, text):
        self.logger_text_edit.append(text)

    def set_property_label(self, text):
        print("Setting property label")
        self.property_label.setText(text)

    def set_score(self, score):
        self.score_label.setText("Score: " + str(score) + u"\U0001F4B0")