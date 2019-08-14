from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from edict import Broadcaster
from utils import *
from ui.ui_utils import *


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
            button.setCheckable(False)
            self.button_group.addButton(button)

        self.grid_layout.setColumnMinimumWidth(0, 50)
        self.grid_layout.setColumnMinimumWidth(1, 50)
        self.grid_layout.setColumnMinimumWidth(2, 50)

        self.grid_layout.addWidget(self.up_button, 0, 1, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.down_button, 2, 1, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.left_button, 1, 0, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.right_button, 1, 2, Qt.AlignHCenter)
        self.grid_layout.addWidget(self.wait_button, 1, 1, Qt.AlignHCenter)

        self.setLayout(self.grid_layout)

        self.button_group.buttonClicked.connect(self.set_button_pressed)

        self.current_direction = None


    def set_button_pressed(self, button):
        print("Button clicked!")
        if button == self.up_button:
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
        Broadcaster().publish("/direction_chosen", self.current_direction)
        Broadcaster().publish("/advance_simulation")


class SidePanelUI(QWidget):
    def __init__(self, parent=None):
        super(SidePanelUI, self).__init__(parent)

        v_layout = QVBoxLayout(self)

        self.score_label = QLabel(self)
        self.score_label.setFont(HUGE_FONT)
        v_layout.addWidget(self.score_label)

        # self.logger_text_edit = QTextEdit(self)
        # self.logger_text_edit.setReadOnly(True)
        # v_layout.addWidget(self.logger_text_edit)

        self.human_property_label = QLabel(self)
        self.human_property_label.setFont(LARGE_FONT)
        v_layout.addWidget(self.human_property_label)

        self.property_label = QLabel(self)
        self.property_label.setFont(LARGE_FONT)
        v_layout.addWidget(self.property_label)

        self.button_cluster = ButtonClusterUI(self)
        v_layout.addWidget(self.button_cluster)

        self.setLayout(v_layout)



        #######################
        # Edict subscriptions #
        #######################

        # Broadcaster().subscribe("/log/raw", self.append_to_log)
        Broadcaster().subscribe("/property_label/raw", self.set_property_label)
        Broadcaster().subscribe("/score_changed", self.set_score)

    def append_to_log(self, text):
        # self.logger_text_edit.append(text)
        pass

    def set_property_label(self, agent_id, text):
        print("Setting property label")
        if agent_id == HUMAN:
            self.human_property_label.setText("You:\n" + text)
            self.human_property_label.setFont(LARGE_FONT)
            self.human_property_label.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        else:
            self.property_label.setText("Agent {}:\n".format(agent_id) + text)
            self.property_label.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

    def set_score(self, score):
        self.score_label.setText("Fuel: " + str(score) + u"\U000026FD")