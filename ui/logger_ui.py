from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from edict import Broadcaster

class LoggerUI(QWidget):
    def __init__(self, parent=None):
        super(LoggerUI, self).__init__(parent)
        v_layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        v_layout.addWidget(self.text_edit)
        self.setLayout(v_layout)

        #######################
        # Edict subscriptions #
        #######################

        Broadcaster().subscribe("/log/raw", self.append)

    def append(self, text):
        self.text_edit.append(text)