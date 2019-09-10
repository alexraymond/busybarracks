from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import time
from simulator import Simulator
from interactive_argument import InteractiveArgument
from ui.grid_ui import GridUI
from ui.side_panel_ui import SidePanelUI
from edict import Broadcaster
from grid2d import LOCAL_OBSTACLE
from utils import *
from ui.ui_utils import *


class SimulatorUI(QMainWindow):

    def __init__(self, width, height, filename=None, player_id=None, parent=None):
        super(SimulatorUI, self).__init__(parent)

        # TODO: Clean this mess

        self.player_id = player_id

        self.simulator = Simulator(width, height, filename, player_id)

        self.setWindowTitle("Busy Barracks")

        self.file_menu = self.menuBar().addMenu("File")

        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save_grid)
        self.file_menu.addAction(self.save_action)
        self.edit_menu = self.menuBar().addMenu("Edit")

        print("Starting grid with dimensions {} {}".format(width, height))

        self.edit_lock = False
        self.agent_selected = None
        self.current_edit_action = QAction("void")

        # TODO: Re-add progress widget later
        # #######################################
        # # Creating simulation progress widget #
        # #######################################

        progress_widget = QWidget(self)

        h_layout = QHBoxLayout()
        self.step_slider = QSlider()
        self.step_slider.setOrientation(Qt.Horizontal)
        self.step_slider_label = QLabel("Step: 0")
        self.step_slider.setMaximum(self.simulator.simulation_size())

        self.beginning_button = QPushButton(progress_widget)
        self.beginning_button.setIcon(QIcon("icons/beginning.png"))
        self.beginning_button.clicked.connect(self.rewind_simulation)
        self.backward_button = QPushButton(progress_widget)
        self.backward_button.setIcon(QIcon("icons/backward.png"))
        self.backward_button.clicked.connect(self.retreat_simulation)
        self.forward_button = QPushButton(progress_widget)
        self.forward_button.setIcon(QIcon("icons/forward-add.png"))
        self.forward_button.clicked.connect(self.advance_simulation)
        self.end_button = QPushButton(progress_widget)
        self.end_button.setIcon(QIcon("icons/end.png"))
        self.end_button.clicked.connect(self.skip_to_end_simulation)
        h_layout.addWidget(self.beginning_button)
        h_layout.addWidget(self.backward_button)
        h_layout.addWidget(self.step_slider_label)
        h_layout.addWidget(self.step_slider)
        h_layout.addWidget(self.forward_button)
        h_layout.addWidget(self.end_button)
        progress_widget.setLayout(h_layout)

        ####################
        # Creating actions #
        ####################

        self.actions = []
        self.toolbar = QToolBar()
        self.toolbar.setMovable(True)
        self.add_global_obstacle_action = QAction(QIcon("icons/wall.svg"), "Add Global Obstacle", self.toolbar)
        self.add_global_obstacle_action.setCheckable(True)
        self.actions.append(self.add_global_obstacle_action)
        self.edit_menu.addAction(self.add_global_obstacle_action)

        self.add_local_obstacle_action = QAction(QIcon("icons/cone.png"), "Add Local Obstacle", self.toolbar)
        self.add_local_obstacle_action.setCheckable(True)
        self.actions.append(self.add_local_obstacle_action)
        self.edit_menu.addAction(self.add_local_obstacle_action)

        self.add_agent_action = QAction(QIcon("icons/robot.svg"), "Add Agent", self.toolbar)
        self.add_agent_action.setCheckable(True)
        self.actions.append(self.add_agent_action)
        self.edit_menu.addAction(self.add_agent_action)

        self.assign_goal_action = QAction(QIcon("icons/flag.png"), "Assign Goal to Agent", self.toolbar)
        self.assign_goal_action.setCheckable(True)
        self.assign_goal_action.setDisabled(True)
        self.actions.append(self.assign_goal_action)
        self.edit_menu.addAction(self.assign_goal_action)

        self.erase_item_action = QAction(QIcon("icons/eraser.png"), "Remove Obstacle/Agent", self.toolbar)
        self.erase_item_action.setCheckable(True)
        self.actions.append(self.erase_item_action)
        self.edit_menu.addAction(self.erase_item_action)

        self.assign_random_goals_action = QAction(QIcon("icons/random.png"), "Assign Random Goals", self.toolbar)
        self.show_paths_action= QAction(QIcon("icons/arrows.png"), "Show all paths", self.toolbar)
        self.show_paths_action.setCheckable(True)
        self.toolbar.addAction(self.add_global_obstacle_action)
        self.toolbar.addAction(self.add_local_obstacle_action)
        self.toolbar.addAction(self.add_agent_action)
        self.toolbar.addAction(self.assign_goal_action)
        self.toolbar.addAction(self.erase_item_action)
        self.toolbar.addAction(self.show_paths_action)
        self.toolbar.addAction(self.assign_random_goals_action)
        self.toolbar.setIconSize(QSize(35,35))
        self.grid_view = GridUI(width, height)

        self.setCentralWidget(self.grid_view)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        #######################
        # Creating side panel #
        #######################

        self.side_panel = SidePanelUI(self)
        self.side_dock_widget = QDockWidget("Simulation Logger", self)
        self.side_dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.side_dock_widget.setWidget(self.side_panel)
        self.side_dock_widget.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.side_dock_widget)
        self.side_panel.button_cluster.button_group.buttonClicked.connect(self.update_agents)

        # TODO: Re-add progress widget later
        # bottom_dock_widget = QDockWidget("Simulation Progress", self)
        # bottom_dock_widget.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        # bottom_dock_widget.setWidget(progress_widget)
        # bottom_dock_widget.setFeatures(QDockWidget.DockWidgetMovable)
        # self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock_widget)
        progress_widget.setVisible(False)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        ###############################
        # Connecting actions to slots #
        ###############################

        self.add_global_obstacle_action.toggled.connect(self.add_global_obstacle_toggled)
        self.add_local_obstacle_action.toggled.connect(self.add_local_obstacle_toggled)
        self.add_agent_action.toggled.connect(self.add_agent_toggled)
        self.assign_goal_action.toggled.connect(self.assign_goal_toggled)
        self.erase_item_action.toggled.connect(self.erase_item_toggled)
        self.show_paths_action.toggled.connect(self.show_paths_toggled)
        self.assign_random_goals_action.triggered.connect(self.assign_random_goals)

        # self.step_slider.valueChanged.connect(self.update_step)

        self.update_step(0)

        ############################
        # Creating argument widget #
        ############################

        # self.arg_widget = QDialog()
        # self.arg_widget.hide()


        #######################
        # Edict subscriptions #
        #######################

        Broadcaster().subscribe("/cell_pressed", self.cell_pressed)
        Broadcaster().subscribe("/new_argument", self.show_argument)
        Broadcaster().subscribe("/human_collision", self.show_collision_dialogue)
        Broadcaster().subscribe("/advance_simulation", self.advance_simulation)
        Broadcaster().subscribe("/game_over", self.show_game_over)
        # Broadcaster().subscribe("/model_updated", self.update_agents)

    def show_game_over(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Success!")
        msg_box.setFont(MEDIUM_FONT)
        msg_box.setText("Congratulations! You have reached the goal.")
        msg_box.exec_()
        self.simulator.save_results()
        self.deleteLater()

    def show_collision_dialogue(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Collision!")
        msg_box.setFont(MEDIUM_FONT)
        msg_box.setText("You have collided with another officer and it was <b>your fault</b>.\nLose 20 " + u"\U000026FD" + ".")
        msg_box.exec_()

    def show_argument2(self, interactive_argument: InteractiveArgument):
        print("Showing message box!")
        print(interactive_argument)
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Agent {} says to you:".format(interactive_argument.sender_id))
        msg_box.setText(interactive_argument.proposed_argument)
        buttons = {}
        for key, argument in interactive_argument.possible_answers.items():
            button = msg_box.addButton(argument, QMessageBox.AcceptRole)
            buttons[button] = key

        msg_box.exec_()

    def show_argument(self, interactive_argument: InteractiveArgument):
        arg_widget = QDialog()
        other_agent_id = interactive_argument.sender_id
        Broadcaster().publish("/request_agent_stats", HUMAN)
        Broadcaster().publish("/request_agent_stats", other_agent_id)
        arg_widget.setWindowTitle("Agent {} says to you:".format(other_agent_id))
        main_arg_label = QLabel(arg_widget)
        main_arg_label.setText("Agent {}: <i>\"".format(other_agent_id) + interactive_argument.proposed_argument + "\"</i>")
        main_arg_label.setFont(LARGE_FONT)
        buttons = {}
        button_group = QButtonGroup(arg_widget)
        def button_pressed(button):
            arg_id = buttons[button]
            arg_widget.done(arg_id)
            Broadcaster().publish("/new_event", "ARG{}".format(arg_id))


        for key, argument in interactive_argument.possible_answers.items():
            button = QPushButton(argument, arg_widget)
            button.setFont(LARGE_FONT)
            button_group.addButton(button)
            buttons[button] = key  # Inverse dict to find key when pressing button.
            button_group.buttonClicked.connect(button_pressed)

        frame = QFrame(arg_widget)

        # h_layout = QHBoxLayout(arg_widget)
        # human_agent_stats_label = QLabel(arg_widget)
        # text = "You:\n"
        # text += self.simulator.agent(HUMAN).get_properties_as_text()
        # human_agent_stats_label.setText(text)
        # font = QFont("Helvetica", 14)
        # font.setBold(True)
        # human_agent_stats_label.setFont(font)
        #
        # separator_label = QLabel(arg_widget)
        # separator_label.setFrameStyle(QFrame.VLine | QFrame.Plain)
        #
        # frame.setFrameStyle(QFrame.Panel | QFrame.Plain)
        #
        # computer_agent_stats_label = QLabel(arg_widget)
        # text = "Agent {}:\n".format(other_agent_id)
        # text += self.simulator.agent(other_agent_id).get_properties_as_text()
        # computer_agent_stats_label.setText(text)
        # computer_agent_stats_label.setFont(QFont("Helvetica", 14))
        #
        # h_layout.addWidget(human_agent_stats_label)
        # h_layout.addWidget(separator_label)
        # h_layout.addWidget(computer_agent_stats_label)
        # frame.setLayout(h_layout)

        v_layout = QVBoxLayout(arg_widget)
        v_layout.addWidget(main_arg_label)
        v_layout.addWidget(frame)
        spacer = QSpacerItem(0, 25)
        # v_layout.addWidget(spacer)
        buttons_label = QLabel(arg_widget)
        buttons_label.setText("Possible valid responses:")
        buttons_label.setAlignment(Qt.AlignCenter)
        buttons_label.setFont(QFont("Helvetica", 14))
        v_layout.addWidget(buttons_label)
        for button in buttons.keys():
            v_layout.addWidget(button)

        # self.setWindowModality(QWidget.Modal)
        arg_widget.setLayout(v_layout)
        arg_widget.setMinimumSize(300, 200)
        arg_widget.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        open_time = time.time()
        chosen_argument = arg_widget.exec_()
        close_time = time.time()
        Broadcaster().publish("/human_reply", chosen_argument)
        Broadcaster().publish("/time_in_popup", close_time - open_time)



    def rewind_simulation(self):
        self.step_slider.setValue(0)

    def skip_to_end_simulation(self):
        self.step_slider.setValue(self.step_slider.maximum())

    def reset_human_direction(self):
        button_group = self.side_panel.button_cluster.button_group
        if len(button_group.buttons()) > 0:
            Broadcaster().publish("/direction_chosen", self.side_panel.button_cluster.current_direction)
            self.update_agents()

    def advance_simulation(self):
        if self.current_step() == self.step_slider.maximum():
            self.run_step()
            return
        self.step_slider.setValue(self.current_step() + 1)


    def retreat_simulation(self):
        if self.current_step() > 0:
            self.step_slider.setValue(self.current_step() - 1)

    def save_grid(self):
        filename, filter = QFileDialog.getSaveFileName(self, "Save Grid to File", filter="*.grd", options=QFileDialog.DontUseNativeDialog)
        if filename:
            self.simulator.save_grid(filename)

    def untoggle_other_actions(self):
        for action in self.actions:
            if action != self.current_edit_action:
                action.setChecked(False)


    def cell_pressed(self, coord):
        self.grid_view.clear_selection()
        if self.current_edit_action.isChecked():
            if self.current_edit_action == self.add_global_obstacle_action:
                self.simulator.add_obstacle(coord)
            elif self.current_edit_action == self.add_local_obstacle_action:
                self.simulator.add_obstacle(coord, LOCAL_OBSTACLE)
            elif self.current_edit_action == self.add_agent_action:
                self.simulator.add_agent(coord)
            elif self.current_edit_action == self.erase_item_action:
                self.simulator.erase_item(coord)
            elif self.current_edit_action == self.assign_goal_action:
                if self.agent_selected is not None:
                    self.simulator.assign_goal(self.agent_selected, coord)
                    self.current_edit_action.setChecked(False)

            self.update_step()
        cell_value = self.simulator.cell_at(coord, self.step_slider.value())
        if cell_value > 0:  # If cell pressed is agent.
            self.grid_view.select_agent(cell_value, coord)
            self.assign_goal_action.setEnabled(True)
            self.agent_selected = cell_value

            # Request properties to display in side panel.
            Broadcaster().publish("/request_agent_stats", self.agent_selected)
        else:
            self.agent_selected = None
            self.assign_goal_action.setDisabled(True)

    def assign_goal_toggled(self, toggled):
        self.current_edit_action = self.assign_goal_action
        self.untoggle_other_actions()

    def add_global_obstacle_toggled(self, toggled):
        self.current_edit_action = self.add_global_obstacle_action
        self.untoggle_other_actions()

    def add_local_obstacle_toggled(self, toggled):
        self.current_edit_action = self.add_local_obstacle_action
        self.untoggle_other_actions()

    def add_agent_toggled(self, toggled):
        self.current_edit_action = self.add_agent_action
        self.untoggle_other_actions()

    def erase_item_toggled(self, toggled):
        self.current_edit_action = self.erase_item_action
        self.untoggle_other_actions()

    def lock_grid(self):
        if self.edit_lock is False:
            message_box = QMessageBox()
            message_box.setText("Edits are now disabled.")
            # message_box.exec_()
            self.edit_lock = True

            self.add_global_obstacle_action.setDisabled(True)
            self.add_agent_action.setDisabled(True)
            self.erase_item_action.setDisabled(True)


    def run_step(self):
        self.lock_grid()
        success = self.simulator.simulate_step()
        if success:
            self.update_step(self.step_slider.value() + 1)
            self.reset_human_direction()  # TODO: Remove hideous workaround
            self.grid_view.save_snapshot(self.player_id, self.step_slider.value() + 1)
        # else:
        #     message_box = QMessageBox()
        #     message_box.setText("Failed to perform move.")
        #     message_box.exec_()

    def add_random_agent(self):
        self.simulator.create_random_agents(self.num_agents_spin_box.value())
        self.grid_view.set_base_grid(self.simulator.grid_at(self.step_slider.value()))
        self.grid_view.draw_base_grid()
        self.update_agents()

    def add_random_obstacles(self):
        self.simulator.create_random_obstacles(self.num_obstacles_spin_box.value())
        self.grid_view.set_base_grid(self.simulator.grid_at(self.step_slider.value()))
        self.grid_view.draw_base_grid()
        self.update_agents()

    def assign_random_goals(self):
        self.simulator.assign_random_goals()
        self.update_agents()

    def show_paths_toggled(self, toggled):
        self.grid_view.set_paths_on(toggled)  # 2 equals checked in QCheckBox.

    def update_agents(self):
        step = self.current_step()
        print("Update agents for step {}".format(step))
        self.simulator.update_agents(step)
        agents = self.simulator.agents()
        # FIXME: Should pass agents instead of creating all those data structures.
        world_models = {}
        plans = {}
        visibilities = {}
        positions = {}
        goals = {}
        for agent in agents.values():
            positions[agent.agent_id()] = agent.current_pos()
            world_models[agent.agent_id()] = agent.world_model_at(step)
            plans[agent.agent_id()] = agent.plan_at(step)
            visibilities[agent.agent_id()] = agent.visibility_radius()
            goals[agent.agent_id()] = agent.goal()
        self.grid_view.update_agent_positions(positions)
        self.grid_view.update_agent_models(world_models)
        self.grid_view.update_agent_plans(plans)
        self.grid_view.update_agent_visibilities(visibilities)
        self.grid_view.update_agent_goals(goals)

    def update_step(self, step=-1):
        if step == -1:
            step = self.step_slider.value()
        maximum = self.simulator.simulation_size() - 1
        self.step_slider.setMaximum(maximum)
        self.step_slider.setValue(step)
        if step == maximum:
            self.forward_button.setIcon(QIcon("icons/forward-add.png"))
        else:
            self.forward_button.setIcon(QIcon("icons/forward.png"))
        self.step_slider_label.setText("Step: {}".format(step))
        self.update_agents()  # TODO: Remove duplicate call
        self.grid_view.set_base_grid(self.simulator.grid_at(step))
        self.grid_view.draw_base_grid()
        self.simulator.communicate()
        self.update_agents()

    def current_step(self):
        return self.step_slider.value()
