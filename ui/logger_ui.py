from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from edict import Broadcaster

class SidePanelUI(QWidget):
    def __init__(self, parent=None):
        super(SidePanelUI, self).__init__(parent)
        v_layout = QVBoxLayout(self)
        self.logger_text_edit = QTextEdit(self)
        self.logger_text_edit.setReadOnly(True)
        v_layout.addWidget(self.logger_text_edit)

        self.property_label = QLabel(self)
        self.property_label.setFont(QFont("Helvetica", 14))
        v_layout.addWidget(self.property_label)
        self.setLayout(v_layout)

        #######################
        # Edict subscriptions #
        #######################

        Broadcaster().subscribe("/log/raw", self.append_to_log)
        Broadcaster().subscribe("/property_label/raw", self.set_property_label)

    def append_to_log(self, text):
        self.logger_text_edit.append(text)

    def set_property_label(self, text):
        print("Setting property label")
        self.property_label.setText(text)