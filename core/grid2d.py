import numpy as np
import traceback

EMPTY = 0
GLOBAL_OBSTACLE = -1
LOCAL_OBSTACLE = -2


class Grid2D:
    def __init__(self, w, h):
        """
        Constructs blank grid containing only empty spaces.
        Cell occupancy in this grid can be represented as EMPTY (0), OBSTACLE (-1),
        or by agent ids (positive integers).
        :param w: width of 2D grid
        :param h: height of 2D grid
        """
        self.width = w
        self.height = h

        self.cells = np.zeros((w, h), dtype=np.int)

        self.agent_positions = {}

    def within_bounds(self, coord):
        """
        Checks if a given coordinate exists in the 2D grid.
        :param coord: Position to check.
        :returns True if within bounds. False otherwise.
        """
        wr = range(0, self.width)
        hr = range(0, self.height)
        x, y = coord
        return x in wr and y in hr

    def neighbours_of(self, coord, neighbourhood_type='von_neumann'):
        """
        Returns immediate neighbourhood of given coordinate.
        :param coord: Position to return neighbourhood.
        :param neighbourhood_type: Currently supports 'von_neumann' or 'moore' neighbourhoods.
        :return: List of neighbours. False if arguments are invalid..
        """
        if not self.within_bounds(coord):
            print("Grid2D::neighbours_of: Position out of bounds.")
            return None
        x, y = coord
        neighbours = []
        if neighbourhood_type == 'von_neumann':
            if self.within_bounds((x - 1, y)): neighbours.append((x - 1, y))  # Left
            if self.within_bounds((x + 1, y)): neighbours.append((x + 1, y))  # Right
            if self.within_bounds((x, y - 1)): neighbours.append((x, y - 1))  # Up
            if self.within_bounds((x, y + 1)): neighbours.append((x, y + 1))  # Down
        elif neighbourhood_type == 'moore':
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == j == 0: continue
                    if self.within_bounds((x + i, y + j)): neighbours.append((x + i, y + j))
        else:
            print("Grid2D::neighbours_of: This neighbourhood type is not supported.")
            return None
        return neighbours

    def is_cell_empty(self, coord):
        if not self.within_bounds(coord):
            print("Grid2D::neighbours_of: Position out of bounds.")
            return False
        x, y = coord
        return self.cells[x][y] == EMPTY

    def add_obstacle(self, coord, type=GLOBAL_OBSTACLE):
        """
        Adds obstacle to 2D grid.
        :param coord: Position to add the obstacle.
        :param type: Type of obstacle (GLOBAL_OBSTACLE or LOCAL_OBSTACLE).
        :returns True if successful. False if out of bounds.
        """
        x, y = coord
        if not self.within_bounds(coord):
            print("Grid2D::add_obstacle: Position out of bounds.")
            return False
        if self.cells[x][y] != EMPTY:
            print("Grid2D::add_obstacle: Trying to add obstacle to non-empty cell.")
            return False
        self.cells[x][y] = type
        return True

    def remove_obstacle(self, coord):
        """
        Removes obstacle from 2D grid.
        :param coord: Position to remove the obstacle from.
        :returns True if successful. False if out of bounds or obstacle not found.
        """
        if not self.within_bounds(coord):
            print("Grid2D::remove_obstacle: Position out of bounds.")
            return False
        x, y = coord
        if Grid2D.is_obstacle(self.cells[x][y]):
            self.cells[x][y] = EMPTY
            return True

        print("Grid2D::remove_obstacle: There is no obstacle to remove at this cell.")
        return False

    def add_agent(self, agent_id, coord):
        """
        Adds agent to 2D grid.
        Agents are represented as a non-zero positive integer.
        :param agent_id: Agent's unique identifier.
        :param coord: Position to add the agent.
        :returns True if operation successful. False if out of bounds or in conflict.
        """
        if not self.within_bounds(coord):
            print("Grid2D::add_agent: Position out of bounds.")
            return False
        x, y = coord
        if self.cells[x][y] == EMPTY:
            self.cells[x][y] = agent_id
            self.agent_positions[agent_id] = coord
            return True

        print("Grid2D::add_agent: Trying to add agent to non-empty cell.")
        return False

    def remove_agent(self, coord):
        if not self.within_bounds(coord):
            print("Grid2D::remove_agent: Position out of bounds.")
            return False
        x, y = coord
        if self.cells[x][y] > 0:
            agent_id = self.cells[x][y]
            self.cells[x][y] = EMPTY
            del self.agent_positions[agent_id]
            return True

        print("Grid2D::remove_agent: Cell does not contain an agent.")
        return False

    def move_agent(self, agent_id, dest_coord):
        current_coord = self.agent_positions.get(agent_id, False)
        if current_coord is False:
            print("Grid2D::move_agent: Agent not found!")
            return False

        if type(current_coord) is type(dest_coord):
            cur_x, cur_y = current_coord
            dest_x, dest_y = dest_coord

            # Only erase previous cell if you were the last to occupy it.
            # This is important in cases where one agent is closely following the next.
            if self.cells[cur_x][cur_y] == agent_id:
                self.cells[cur_x][cur_y] = EMPTY
            self.cells[dest_x][dest_y] = agent_id
            self.agent_positions[agent_id] = dest_coord
            return True

    @staticmethod
    def is_obstacle(cell):
        return cell == GLOBAL_OBSTACLE or cell == LOCAL_OBSTACLE
