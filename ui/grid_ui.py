from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from grid2d import EMPTY, GLOBAL_OBSTACLE, LOCAL_OBSTACLE
from edict import Broadcaster
from utils import *
from ui.ui_utils import *

import numpy as np

CELL_SIZE = 50


class GridCellUI(QGraphicsRectItem):
    def __init__(self, cell_value, x_coord, y_coord, special_cell=None, parent=None):
        super(GridCellUI, self).__init__()
        self.cell_value = cell_value
        self.setRect(0, 0, CELL_SIZE, CELL_SIZE)
        self.circle_item = QGraphicsEllipseItem(self)
        self.text_item = QGraphicsSimpleTextItem(self.circle_item)
        self.circle_item.setVisible(False)
        self.text_item.setVisible(False)

        self.x_coord = x_coord
        self.y_coord = y_coord
        self.special_cell = special_cell

        self.set_value(cell_value)
        self.hover_enter_callback = None
        self.hover_leave_callback = None
        self.mouse_press_callback = None
        self.setAcceptHoverEvents(False)
        self.setAcceptDrops(False)

    def set_value(self, value, special_cell=None):
        self.cell_value = value
        if special_cell == SpecialCellType.PLAYER_GOAL:
            self.setBrush(QBrush(DARK_RED))
            self.setPen(QPen(QColor(222, 183, 120)))
            self.circle_item.setVisible(False)
        elif self.cell_value == EMPTY:
            self.setBrush(QBrush(QColor(222, 183, 120)))
            self.setPen(QPen(Qt.black))
            self.circle_item.setVisible(False)
        elif self.cell_value == GLOBAL_OBSTACLE:
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            brush.setColor(QColor(41, 29, 25))
            self.setBrush(brush)
        elif self.cell_value == LOCAL_OBSTACLE:
            brush = QBrush()
            brush.setStyle(Qt.DiagCrossPattern)
            brush.setColor(Qt.black)
            self.setBrush(brush)
        if value > 0:  # Is an agent
            self.circle_item.setRect(0, 0, CELL_SIZE, CELL_SIZE)
            self.circle_item.setVisible(True)
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            if self.cell_value == HUMAN:  # Human agent
                brush.setColor(DARK_RED)  # Red
            else:
                brush.setColor(OLIVE_GREEN)  # Green
            self.circle_item.setBrush(brush)
            self.text_item.setVisible(True)
            self.text_item.setText("{}".format(self.cell_value))
            self.text_item.setFont(QFont("Helvetica", 20))
            text_width = self.text_item.boundingRect().width()
            text_height = self.text_item.boundingRect().height()
            # Centralising text inside circle
            self.text_item.setPos((self.circle_item.boundingRect().width() / 2) - (text_width / 2),
                             (self.circle_item.boundingRect().height() / 2) - (text_height / 2))
        self.update()

    def set_hover_enter_callback(self, callback):
        self.hover_enter_callback = callback

    def set_hover_leave_callback(self, callback):
        self.hover_leave_callback = callback

    def hoverEnterEvent(self, event):
        if self.cell_value > 0:
            self.hover_enter_callback(self.cell_value)

    def mousePressEvent(self, event):
        Broadcaster().publish("/cell_pressed", (self.x_coord, self.y_coord))

    def hoverLeaveEvent(self, event):
        self.hover_leave_callback()

    def select_cell(self):
        pen = QPen(Qt.blue)
        pen.setWidth(3)
        self.circle_item.setPen(pen)
        self.update()

    def unselect_cell(self):
        pen = QPen(Qt.black)
        pen.setWidth(1)
        self.circle_item.setPen(pen)
        self.update()

class AgentVisibilityUI(QGraphicsRectItem):
    def __init__(self, origin, visibility_radius, parent=None):
        super(AgentVisibilityUI, self).__init__()
        self.visibility_radius = visibility_radius
        self.origin_x, self.origin_y = origin
        x = (self.origin_x - visibility_radius) * CELL_SIZE
        y = (self.origin_y - visibility_radius) * CELL_SIZE
        width = height = visibility_radius * (2 * CELL_SIZE) + CELL_SIZE
        pen = QPen(Qt.cyan)
        pen.setStyle(Qt.DashLine)
        pen.setWidth(3)
        self.setPen(pen)
        self.setRect(x, y, width, height)

class ToolTipUI(QGraphicsRectItem):
    def __init__(self, origin, agent_id):
        super(ToolTipUI, self).__init__()
        self.origin_x, self.origin_y = origin
        x = self.origin_x * CELL_SIZE
        y = self.origin_y * CELL_SIZE

class PathUI(QGraphicsRectItem):
    def __init__(self, agent_id, path, path_length, parent=None):
        super(PathUI, self).__init__()
        self.path = path
        self.lines = []
        if self.path is None or len(self.path) == 0:
            return
        self.origin_x = path[0][POS][0]
        self.origin_y = path[0][POS][1]
        self.agent_id = agent_id
        self.draw_path(path_length)

    def relative(self, pos):
        return (pos[0] - self.origin_x) * CELL_SIZE, (pos[1] - self.origin_y) * CELL_SIZE

    def draw_path(self, path_length):
        max_x = max_y = 0
        min_x = min_y = 100000
        if path_length > len(self.path):
            path_length = len(self.path)
        for i in range(path_length - 1):
            from_x, from_y = self.relative(self.path[i][POS])
            to_x, to_y = self.relative(self.path[i + 1][POS])
            if (to_x > max_x):
                max_x = to_x
            if (to_x < min_x):
                min_x = to_x
            if (to_y > max_y):
                max_y = to_y
            if (to_y < min_y):
                min_y = to_y
            line = QGraphicsLineItem(QLineF(from_x, from_y, to_x, to_y), self)
            self.lines.append(line)
        # Midpoint of destination cell.
        dest_x, dest_y = self.relative(self.path[-1][POS])

        # Drawing box around destination cell.
        box = QGraphicsRectItem(dest_x - CELL_SIZE/2, dest_y - CELL_SIZE/2, CELL_SIZE, CELL_SIZE, self)
        # south = QLineF(dest_x - CELL_SIZE/2, dest_y + CELL_SIZE/2,
        #                dest_x + CELL_SIZE/2, dest_y + CELL_SIZE/2)
        # north = QLineF(dest_x - CELL_SIZE/2, dest_y - CELL_SIZE/2,
        #                dest_x + CELL_SIZE/2, dest_y - CELL_SIZE/2)
        # west = QLineF(dest_x - CELL_SIZE/2, dest_y - CELL_SIZE/2,
        #               dest_x - CELL_SIZE/2, dest_y + CELL_SIZE/2)
        # east = QLineF(dest_x + CELL_SIZE/2, dest_y - CELL_SIZE/2,
        #               dest_x + CELL_SIZE/2, dest_y + CELL_SIZE/2)
        # self.lines.append(QGraphicsLineItem(south, self))
        # self.lines.append(QGraphicsLineItem(north, self))
        # self.lines.append(QGraphicsLineItem(west, self))
        # self.lines.append(QGraphicsLineItem(east, self))

        # Sets pen to all lines.
        for line in self.lines:
            if self.agent_id == HUMAN:  # Human agent
                red = DARK_RED
                pen = QPen(red)  # Red
                brush = QBrush(red)
            else:
                green = OLIVE_GREEN
                pen = QPen(green)  # Green
                brush = QBrush(green)
            pen.setWidth(5)
            line.setPen(pen)
            box.setBrush(brush)



class GridUI(QGraphicsView):
    def __init__(self, x_cells, y_cells, parent=None):
        super(GridUI, self).__init__(parent)
        self.grid_scene = QGraphicsScene()
        self.cells = {}
        self.x_cells = x_cells
        self.y_cells = y_cells
        self.grid_rect = QRectF(0, 0, x_cells * CELL_SIZE, y_cells * CELL_SIZE)
        self.agent_world_models = {}
        self.agent_plans = {}
        self.agent_optimal_plans = {}
        self.agent_visibilities = {}
        self.agent_positions = {}
        self.agent_goals = {}
        self.ui_paths = {}
        self.ui_visibilities = {}
        self.base_grid = np.zeros((x_cells, y_cells), dtype=np.int)
        self.keep_paths_on = False
        self.current_selection = None
        self.human_goal = None
        self.path_length = 100
        for i in range(x_cells):
            self.cells[i] = {}
            for j in range(y_cells):
                cell = GridCellUI(EMPTY, i, j, self)
                # cell.agent_hover_enter.connect(self.load_agent_grid)
                cell.set_hover_enter_callback(self.show_goal)
                cell.set_hover_leave_callback(self.draw_base_grid)
                self.cells[i][j] = cell
                self.grid_scene.addItem(cell)
                cell.setPos(i * CELL_SIZE, j * CELL_SIZE)
        self.setRenderHint(QPainter.Antialiasing)
        self.setScene(self.grid_scene)
        self.fitInView(self.grid_rect, Qt.KeepAspectRatio)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        Broadcaster().subscribe("/highlighted_agent", self.set_highlighted_agent)

    def set_highlighted_agent(self, highlighted_agent):
        self.highlighted_agent = highlighted_agent
        self.set_paths_on(True)

    def save_snapshot(self, player_id, time_step):
        filename = "results/{}/{}.png".format(player_id, time_step)
        # image = QImage(filename)
        # painter = QPainter(image)
        # painter.setRenderHint(QPainter.Antialiasing)
        # self.grid_scene.render(painter)
        # image.save(filename)

        pixmap = self.grab()
        pixmap.save(filename)


    def resizeEvent(self, event):
        self.fitInView(self.grid_rect, Qt.KeepAspectRatio)

    def draw_grid(self, grid):
        self.refresh_paths()
        for i in range(self.x_cells):
            for j in range(self.y_cells):
                special_cell = None
                if self.human_goal == (i, j):
                    special_cell = SpecialCellType.PLAYER_GOAL
                self.cells[i][j].set_value(grid[i][j], special_cell)

    def update_agent_positions(self, positions):
        self.agent_positions = positions

    def update_agent_models(self, world_models):
        self.agent_world_models = world_models

    def update_agent_plans(self, plans):
        self.agent_plans = plans

    def update_agent_optimal_plans(self, optimal_plans):
        self.agent_optimal_plans = optimal_plans

    def update_agent_visibilities(self, visibilities):
        self.agent_visibilities = visibilities

    def update_agent_goals(self, goals):
        self.agent_goals = goals
        self.human_goal = self.agent_goals.get(1, None)

    def draw_visibility(self, agent_id):
        # FIXME: Known bug -- visibility is not drawn when agent doesn't have a plan.
        visibility = AgentVisibilityUI(self.agent_positions[agent_id], self.agent_visibilities[agent_id])
        self.ui_visibilities[agent_id] = visibility
        self.grid_scene.addItem(visibility)

    def draw_path(self, agent_id, optimal=True):
        plan = self.agent_plans.get(agent_id, None)
        if plan is None or len(plan) == 0:
            return
        if optimal:
            plan = self.agent_optimal_plans.get(agent_id, None)
            path = PathUI(agent_id, self.agent_optimal_plans[agent_id], self.path_length, self)
        else:
            path = PathUI(agent_id, self.agent_plans[agent_id], self.path_length, self)
        self.ui_paths[agent_id] = path
        self.grid_scene.addItem(path)
        origin_x, origin_y = self.agent_plans[agent_id][0][POS]
        path.setPos(origin_x * CELL_SIZE + CELL_SIZE / 2, origin_y * CELL_SIZE + CELL_SIZE / 2)

    def refresh_paths(self):
        for agent_id, path in self.ui_paths.items():
            self.grid_scene.removeItem(path)
        for agent_id, visibility in self.ui_visibilities.items():
            self.grid_scene.removeItem(visibility)
        self.ui_paths = {}
        self.ui_visibilities = {}
        if self.keep_paths_on:
            for agent_id, path in self.agent_plans.items():
                if self.highlighted_agent == agent_id:
                    self.draw_path(agent_id)

    def set_paths_on(self, on):
        self.keep_paths_on = on
        self.refresh_paths()

    def set_base_grid(self, grid):
        self.base_grid = grid

    def draw_base_grid(self):
        self.refresh_paths()
        self.draw_grid(self.base_grid)

    def show_goal(self, agent_id):
        if self.agent_plans.get(agent_id, None) is not None:
            self.draw_path(agent_id)

    def load_agent_grid(self, agent_id):
        self.draw_grid(self.agent_world_models[agent_id])
        self.draw_visibility(agent_id)
        self.show_goal(agent_id)

    def clear_selection(self):
        if self.current_selection is not None:
            previous_i, previous_j = self.current_selection
            self.cells[previous_i][previous_j].unselect_cell()

    def select_agent(self, agent_id, coord):
        i, j = coord
        if self.cells[i][j].cell_value != agent_id:
            print("GridUI::select_agent: Mismatch between position clicked and agent location.")
            return
        self.clear_selection()
        self.current_selection = coord
        self.cells[i][j].select_cell()



