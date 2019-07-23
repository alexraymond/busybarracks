import sys
from PySide2.QtWidgets import *
from PySide2.QtCore import QObject, Signal, Slot
from ui.new_grid_settings_ui import NewGridSettings
from ui.simulator_ui import SimulatorUI


class Application():
    def __init__(self):
        # Create the Qt Application
        self.app = QApplication(sys.argv)
        # Create and show the form
        self.form = NewGridSettings()
        self.simulator = None

        @Slot(int, int)
        def start_new_grid(width, height):
            self.simulator = SimulatorUI(width, height)
            self.simulator.show()

        @Slot(str)
        def load_existing_grid(filename):
            file = open(filename, "r")
            dimensions = file.readline().split()
            if len(dimensions) == 2:
                self.simulator = SimulatorUI(int(dimensions[0]), int(dimensions[1]), filename)
                self.simulator.show()
            else:
                print("Application::load_existing_grid: Ill-formed file!")


        @Slot()
        def cancel():
            print("Please provide grid dimensions.")

        self.form.new_grid_requested.connect(start_new_grid)
        self.form.load_grid_requested.connect(load_existing_grid)
        self.form.cancelled.connect(cancel)

        self.form.show()
        # Run the main Qt loop
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    application = Application()
