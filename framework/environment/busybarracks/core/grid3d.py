from typing import List
import copy

import grid2d
from grid2d import Grid2D, GLOBAL_OBSTACLE
from game_utils import *


class Grid3D:
    #__steps = ...  # type: List[Grid2D]

    def __init__(self, broadcaster, w, h):
        """
        Constructs 3D grid (2D + time) containing one time step (initially).
        Further time steps can be appended to __steps.
        :param w: width of 2D grid
        :param h: height of 2D grid
        """
        self.broadcaster = broadcaster
        self.__steps = []
        self.__steps.append(grid2d.Grid2D(w, h))

        self.__edit_lock = False
        self.__agent_positions = {}
        self.__latest_time_step = 0

    def within_bounds(self, coord, t=0):
        """
        Checks if a given coordinate exists in the 2D grid.
        :param coord: Position to check.
        :returns True if within bounds. False otherwise.
        """
        return self.__steps[0].within_bounds(coord) and t <= (len(self.__steps) - 1)

    @property
    def is_locked_for_edits(self):
        """
        :returns True if grid is locked for edits (i.e. in simulation mode).
        """
        return self.__edit_lock

    def grid_at(self, t):
        """
        Returns 2D grid snapshot from time step t.
        :param t: Time step.
        :returns Grid2D instance if found. False if not found.
        """
        if t > len(self.__steps) or t < 0:
            #print("Grid3D::grid_at: Time step {0} out of bounds.".format(t))
            return False
        return self.__steps[t]

    def raw_grid_at(self, t):
        """
        Returns 2D grid snapshot from time step t.
        :param t: Time step.
        :returns Numpy 2D array if found. False if not found.
        """
        return self.grid_at(t).cells

    def add_agent(self, agent_id, coord_at_t0):
        """
        Adds agent to first time step of grid.
        :param agent_id: Agent's unique identifier.
        :param coord_at_t0: Agent's coordinates at time step 0.
        :returns True if successful.
        """
        time_step = 0
        if self.is_locked_for_edits:
            #print("Grid3D::add_agent: Cannot add agent while grid is locked for edits.")
            return False
        if agent_id < 1:
            #print("Grid3D::add_agent: Invalid agent ID.")
            return False
        if not self.within_bounds(coord_at_t0):
            #print("Grid3D::add_agent: Coordinate {} is out of bounds.".format(coord_at_t0))
            return False
        if self.__agent_positions.get(agent_id, None):
            #print("Grid3D::add_agent: Agent {0} already added.".format(agent_id))
            return False
        success = self.__steps[time_step].add_agent(agent_id, coord_at_t0)
        if success:
            self.__agent_positions[agent_id] = {}
            self.__agent_positions[agent_id][time_step] = coord_at_t0
        return success

    def remove_agent(self, agent_id, coord_at_t0):
        time_step = 0
        if self.is_locked_for_edits:
            #print("Grid3D::remove_agent: Cannot remove agent while grid is locked for edits.")
            return False
        if agent_id < 1:
            #print("Grid3D::remove_agent: Invalid agent ID.")
            return False
        if not self.within_bounds(coord_at_t0):
            #print("Grid3D::remove_agent: Coordinate {} is out of bounds.".format(coord_at_t0))
            return False
        if self.__agent_positions.get(agent_id, None):
            del self.__agent_positions[agent_id]
            return self.__steps[0].remove_agent(coord_at_t0)

        return False

    def find_agent(self, agent_id, time_step):
        """
        Finds the position of a specified agent at a given time step.
        :param agent_id: Agent's unique identifier.
        :param time_step: Time step of simulation.
        :returns Coordinate of agent at said time step if successful. False otherwise.
        """
        agent_found = self.__agent_positions.get(agent_id, None)
        if agent_found is None:
            #print("Grid3D::find_agent: Agent {0} not found.".format(agent_id))
            return False
        coord = agent_found.get(time_step, None)
        if coord is None:
            #print("Grid3D::find_agent: Agent {0} is not present at time step {1}".format(agent_id, time_step))
            return False
        return coord

    def add_obstacle(self, coord, type=GLOBAL_OBSTACLE):
        """
        Adds obstacle to all cells in simulation.
        :param coord: Position to add the obstacle.
        :returns True if successful.
        """
        if self.is_locked_for_edits:
            #print("Grid3D::add_obstacle: Cannot add obstacle while grid is locked for edits.")
            return False
        if not self.within_bounds(coord):
            #print("Grid3D::add_obstacle: Coordinate {} is out of bounds.".format(coord))
            return False
        for i in range(len(self.__steps)):
            if self.__steps[i].add_obstacle(coord, type) is not True:
                return False
        return True

    def remove_obstacle(self, coord):
        if self.is_locked_for_edits:
            #print("Grid3D::remove_obstacle: Cannot remove obstacle while grid is locked for edits.")
            return False
        if not self.within_bounds(coord):
            #print("Grid3D::remove_obstacle: Coordinate {} is out of bounds.".format(coord))
            return False
        for i in range(len(self.__steps)):
            if self.__steps[i].remove_obstacle(coord) is not True:
                return False

    def attempt_move(self, moves):
        """
        Attempts a move from latest simulated time step to next.
        A dict is passed as arguments containing agent_ids and coordinates for next time step.
        The reason individual moves aren't allowed is to prevent asynchronous progress.
        The feasibility of proposed moves is evaluated and checked against conflicts.
        :type moves: dict {key=agent_id (int), value=coord (int, int tuple)}.
        :param moves: Dict containing pairs of moves that constitute a round.
        :returns True if moves accepted by world model. False if conflict is detected.
        """
        #########################################
        # Validating move and performing checks.#
        #########################################
        if not self.is_locked_for_edits:
            #print("Grid3D::attempt_move: Grid needs to be locked to attempt move.")
            return False
        if len(moves) < len(self.__agent_positions):
            #print("Grid3D::attempt_move: There are fewer moves than registered agents.")
            return False
        if len(moves) > len(self.__agent_positions):
            #print("Grid3D::attempt_move: There are more moves than registered agents.")
            return False
        next_time_step = self.__latest_time_step + 1
        crashing_agents = []
        out_of_bounds = []
        conflicts = set()
        coords = list(moves.values())
        if len(self.__steps) - 1 < next_time_step:
            self.__steps.append(copy.deepcopy(self.__steps[self.__latest_time_step]))
        else:
            self.__steps[next_time_step] = copy.deepcopy(self.__steps[self.__latest_time_step])
        for agent_id, coord in moves.items():
            grid = self.raw_grid_at(next_time_step)
            if not self.within_bounds(coord):
                out_of_bounds.append(agent_id)
                continue
            x, y = coord
            if Grid2D.is_obstacle(grid[x][y]):
                crashing_agents.append(agent_id)
            if coords.count(coord) > 1:
                conflicts.add(agent_id)
            if next_time_step > 2: #  No point checking for illegal swaps at beginning.
                for other_agent_id, their_coord in moves.items():
                    if agent_id == other_agent_id:
                        continue
                    current_step = next_time_step - 1
                    # Formatting position to ((x,y), t)
                    previous_pos = (self.__agent_positions[agent_id][current_step], current_step)
                    their_previous_pos = (self.__agent_positions[other_agent_id][current_step], current_step)
                    path_a = [previous_pos, (coord, next_time_step)]
                    path_b = [their_previous_pos, (their_coord, next_time_step)]
                    if illegal_position_swap(path_a, path_b, 2):
                        conflicts.add(agent_id)
                        conflicts.add(other_agent_id)


        if len(crashing_agents) > 0:
            #print("Grid3D::attempt_move: Agent(s) {0} will collide with obstacles.".format(crashing_agents))
            return False
        if len(out_of_bounds) > 0:
            #print("Grid3D::attempt_move: Agent(s) {0} are heading out of bounds.".format(out_of_bounds))
            return False
        if len(conflicts) > 0:
            #print("Grid3D::attempt_move: Conflicts found between agents {0}.".format(conflicts))
            if 1 in conflicts:
                self.broadcaster.publish("/human_collision")
                self.broadcaster.publish("/new_event", "COLLISION")
                return False

        ######################################################################
        # Checks done. Moves are feasible, now move agents on next time step.#
        ######################################################################

        for agent_id, coord in moves.items():
            self.__steps[next_time_step].move_agent(agent_id, coord)
            self.__agent_positions[agent_id][next_time_step] = coord
        self.__latest_time_step = next_time_step
        return True

    def lock_for_edits(self):
        self.__edit_lock = True

    def simulation_size(self):
        return len(self.__steps)


