import numpy as np
import time
from pydoc import locate
from grid3d import Grid3D
from grid2d import Grid2D, EMPTY, GLOBAL_OBSTACLE
from agent import Agent
from utils import *
from edict import Broadcaster
from cultures.easy import EasyCulture
from cultures.medium import MediumCulture
from cultures.hard import HardCulture

from argument import *


COMMUNICATION = True


#FIXME: Agents need to be able to re-inform their new paths after rerouting.

class Simulator:
    def __init__(self, w, h, filename, player_id):
        self.__world_model = Grid3D(w, h)
        self.__agents = {}
        self.__obstacles = []
        self.__width = w
        self.__height = h
        self.__current_time_step = 0
        self.__start_time = None
        self.__num_collisions = 0
        self.__player_id = player_id
        self.__game_over = False

        self.__culture = HardCulture()
        self.__events = []

        if filename:
            self.load_grid(filename)
            self.load_culture(filename)

        Broadcaster().subscribe("/log/raw", self.print_log)
        Broadcaster().subscribe("/human_collision", self.increment_collision_counter)
        Broadcaster().subscribe("/new_event", self.add_event)

    def add_event(self, event):
        self.__events.append((event, time.time()))

    def increment_collision_counter(self):
        self.__num_collisions += 1

    def save_results(self):
        end_time = time.time()
        time_elapsed = end_time - self.__start_time
        human_score = self.agent(HUMAN).score
        time_penalty = self.agent(HUMAN).time_penalty
        file = open(str(self.__player_id) + ".txt", "w")
        culture = '?'
        if type(self.__culture) == EasyCulture:
            culture = 'E'
        elif type(self.__culture) == MediumCulture:
            culture = 'M'
        elif type(self.__culture) == HardCulture:
            culture = 'H'
        file.write("Player id: " + str(self.__player_id) + "\n")
        file.write("Culture: " + culture + "\n")
        file.write("Mode: " + 'X\n' if Agent.EXPLAINABLE else "Mode: " + 'N\n')
        file.write("Score: " + str(human_score) + "\n")
        file.write("Collisions: " + str(self.__num_collisions) + "\n")
        file.write("Time elapsed: " + str(time_elapsed) + "\n")
        file.write("Time penalty: " + str(time_penalty) + "\n")
        file.write("Events:\n")
        for event in self.__events:
            event_text = event[0]
            event_time = event[1]
            file.write("{0} : {1}\n".format(event_text, event_time))
        file.close()

    def print_log(self, log):
        print(log)

    def agent(self, agent_id):
        return self.__agents.get(agent_id, None)

    def is_cell_empty(self, coord, t = 0):
        return self.__world_model.raw_grid_at(t)[coord[0]][coord[1]] == EMPTY

    def cell_at(self, coord, t = 0):
        return self.__world_model.raw_grid_at(t)[coord[0]][coord[1]]

    def random_coord(self):
        """
        Convenience method that returns a random coordinate within the grid.
        :return: Random (x,y) tuple bounded by grid dimensions.
        """
        rx = np.random.randint(0, self.__width)
        ry = np.random.randint(0, self.__height)
        return rx, ry

    def create_random_obstacles(self, num_obstacles):
        """
        Convenience method that populates the world model with random obstacles.
        """
        num_cells = self.__width * self.__height

        if num_obstacles > self.empty_cells_at(self.__current_time_step):
            print("Simulator::create_random_obstacles: There are no sufficient empty cells.")
            return

        obstacles_placed = 0
        while obstacles_placed < num_obstacles:  # TODO: Improve algorithm.
            coord = self.random_coord()
            if self.is_cell_empty(coord):
                self.__obstacles.append(coord)
                self.__world_model.add_obstacle(coord)
                obstacles_placed += 1
        print(self.__world_model.raw_grid_at(0).transpose())

    def create_random_agents(self, num_agents):
        """
        Convenience method that populates the world model with random agents.
        """
        num_cells = self.__width * self.__height

        if num_agents > self.empty_cells_at(self.__current_time_step):
            print("Simulator::create_random_agents: There are no sufficient empty cells.")
            return

        agents_placed = 0
        while agents_placed < num_agents:  # TODO: Improve algorithm.
            coord = self.random_coord()
            if self.is_cell_empty(coord):
                self.add_agent(coord)
                agents_placed += 1
        print(self.__world_model.raw_grid_at(0).transpose())

    def assign_random_goals(self):
        """
        Assigns random goals to agents in the world model.
        This method does not consider whether goals are reachable at all.
        """
        goals_assigned = 0
        for agent in self.__agents.values():
            coord = self.random_coord()
            if self.is_cell_empty(coord):
                agent.assign_goal(coord)

    def assign_goal(self, agent_id, goal_coord):
        if self.is_cell_empty(goal_coord):
            self.__agents[agent_id].assign_goal(goal_coord)
            return
        print("Simulator::assign_goal: Trying to assign goal to non-empty cell!")

    def update_agents(self, t):
        """
        This method updates all agents with what is currently visible (for each)
        at a specific time step t.
        """

        for agent in self.__agents.values():
            current_pos = self.__world_model.find_agent(agent.agent_id(), self.__current_time_step)
            agent.set_current_pos(current_pos)
            if self.__game_over == False and agent.is_human() and current_pos == agent.goal():
                Broadcaster().publish("/game_over")
                self.__game_over = True
            vr = agent.visibility_radius()
            visible_cells = {}
            for i in range(0, self.__width):
                for j in range(0, self.__height):
                    x, y = current_pos
                    cell_value = self.__world_model.raw_grid_at(t)[i][j]
                    if in_visibility_range(vr, current_pos, (i, j)):
                        visible_cells[(i, j)] = cell_value
                    else:
                        # Global obstacles are copied anyway.
                        if cell_value == GLOBAL_OBSTACLE:
                            visible_cells[(i, j)] = cell_value

            agent.update_world_knowledge(visible_cells, t)



    def add_obstacle(self, coord, type=GLOBAL_OBSTACLE):
        success = self.__world_model.add_obstacle(coord, type)
        if success:
            self.__obstacles.append(coord)

    def add_any_agent(self, coord):
        match = True
        for id in range(1, 1000):
            match = any(agent.agent_id() == id for agent in self.__agents.values())
            if match is False:
                break
        if match is False:
            success = self.__world_model.add_agent(id, coord)
            if success:
                self.__agents[id] = Agent(id, (self.__width, self.__height), self)
                self.__agents[id].set_culture(self.__culture)
                self.__culture.initialise_random_values(self.__agents[id])

    def add_agent(self, coord, agent_id=None):
        if agent_id is None:
            self.add_any_agent(coord)
            return
        if agent_id in self.__agents:
            print("Simulator::add_agent: Agent already exists!")
            return
        success = self.__world_model.add_agent(agent_id, coord)
        if success:
            self.__agents[agent_id] = Agent(agent_id, (self.__width, self.__height), self)
            # self.__culture.initialise_random_values(self.__agents[agent_id])
            if agent_id == HUMAN:  # By convention, agent 1 is always going to be the human player.
                self.__agents[agent_id].set_human_control(True)



    def erase_item(self, coord):
        if self.is_cell_empty(coord):
            return
        if Grid2D.is_obstacle(self.cell_at(coord)):
            self.__obstacles.remove(coord)
            self.__world_model.remove_obstacle(coord)
        if self.cell_at(coord) > 0:
            agent_id = self.cell_at(coord)
            self.__world_model.remove_agent(agent_id, coord)
            for agent in self.__agents.values():
                if agent.agent_id() == agent_id:
                    del self.__agents[agent_id]
        self.update_agents(self.__current_time_step)

    def agents(self):
        return self.__agents

    def simulation_size(self):
        return self.__world_model.simulation_size()

    def grid_at(self, t):
        return self.__world_model.raw_grid_at(t)

    def empty_cells_at(self, t):
        num_cells = self.__width * self.__height
        return num_cells - len(self.__obstacles) - len(self.__agents)

    def communicate(self):
        if COMMUNICATION:
            for agent in self.__agents.values():
                if agent.is_human() is False:
                    agent.communicate()

    def simulate_step(self):
        t = self.__current_time_step
        Broadcaster().publish("/log/raw", "\n*** END OF STEP {} ***\n".format(t))
        self.__world_model.lock_for_edits()
        moves = {}
        still_agents = 0
        for agent in self.__agents.values():
            # Check if the plan covers the next time step.
            if agent.latest_plan() is None or len(agent.latest_plan()) <= 1:
                # Uses current position (stay still).
                moves[agent.agent_id()] = self.__world_model.find_agent(agent.agent_id(), t)
                still_agents += 1
                continue
            moves[agent.agent_id()] = agent.latest_plan()[1][POS]
        if still_agents == len(self.__agents):
            print("Agents have reached a standstill.")
        # Propose move to model.
        moves_str = "Proposed moves: {}".format(moves)
        # Broadcaster().publish("/log/raw", moves_str)
        print(moves_str)
        result = self.__world_model.attempt_move(moves)
        if result:
            self.__current_time_step += 1
            # self.update_agents(self.__current_time_step)
            Broadcaster().publish("/new_time_step")
            if self.__current_time_step == 1:
                Broadcaster().publish("/first_move")
                self.__start_time = time.time()
        return result

    def send_locution(self, source_id, destination_id, locution):
        self.__agents[destination_id].receive_locution(source_id, locution)

    def load_grid(self, filename):
        print("Loading grid!")
        file = open(filename, "r")
        grid = self.__world_model.grid_at(0)
        file.readline()  # Skip dimensions line.
        for i in range(grid.width):
            values = file.readline().split()
            if len(values) != grid.height:
                print("Simulator::load_grid: Ill-formed file! Grid might be corrupted.")
                return
            for j in range(len(values)):
                cell_value = int(values[j])
                if cell_value > 0:
                    print("Adding agent {}".format(cell_value))
                    self.add_agent((i,j), cell_value)
                elif cell_value < 0:
                    self.add_obstacle((i,j), cell_value) # TODO: Fix signature mismatch of add_obstacle and add_agent
                grid.cells[i][j] = values[j] # TODO: Load properly (use add_* methods)
        goals = file.readline().split()[0]
        if goals == "GOALS":
            goal = file.readline()
            while goal.split()[0] != "CULTURE":
                agent_id, goal_x, goal_y = goal.split()
                self.assign_goal(int(agent_id), (int(goal_x), int(goal_y)))
                goal = file.readline()
        file.close()

    def load_culture(self, filename):
        print("Loading culture!")
        file = open(filename, "r")
        line = file.readline()
        while line:
            if line.split()[0] == "CULTURE":
                culture = file.readline().split()[0]
                if culture == 'E':
                    self.__culture = EasyCulture()
                elif culture == 'M':
                    self.__culture = MediumCulture()
                elif culture == 'H':
                    self.__culture = HardCulture()
                else:
                    print("Simulator::load_culture: No culture chosen!")
                    return
                for agent in self.__agents.values():
                    agent.set_culture(self.__culture)
            elif line.split()[0] == "MODE":
                mode = file.readline().split()[0]
                if mode == 'X':
                    Agent.EXPLAINABLE = True
                elif mode == 'N':
                    Agent.EXPLAINABLE = False
                else:
                    print("Simulator::load_culture: No mode defined!")
                    return
            elif line.split()[0] == "PROPERTIES":
                property_tuple = file.readline().split()
                while property_tuple[0] != "END":
                    # Format: agent_id {property string} VALUE {value string}
                    agent_id = int(property_tuple[0])
                    separator_index = [i for i, text in enumerate(property_tuple) if text == "VALUE"][0]
                    property = " ".join(property_tuple[1:separator_index])
                    value_string = " ".join(property_tuple[separator_index+1:])
                    if value_string.isdigit():
                        value = int(value_string)
                    else:
                        value = value_string
                    self.__agents[agent_id].assign_property_value(property, value)
                    property_tuple = file.readline().split()

            line = file.readline()

    def save_grid(self, filename):
        file = open(filename, "w")
        grid = self.__world_model.grid_at(0)
        dim_x = grid.width
        dim_y = grid.height
        file.write("{} {}\n".format(dim_x, dim_y))
        for i in range(grid.width):
            for j in range(grid.height):
                file.write("{} ".format(grid.cells[i][j]))
            file.write("\n")
        file.write("GOALS\n")
        for agent in self.__agents.values():
            goal_x, goal_y = agent.goal()
            file.write("{} {} {}\n".format(agent.agent_id(), goal_x, goal_y))
        file.write("CULTURE\n")
        if type(self.__culture) == EasyCulture:
            file.write("E\n")
        elif type(self.__culture) == MediumCulture:
            file.write("M\n")
        elif type(self.__culture) == HardCulture:
            file.write("H\n")
        file.write("MODE\n")
        if Agent.EXPLAINABLE:
            file.write("X\n")
        else:
            file.write("N\n")
        file.write("PROPERTIES\n")
        for agent in self.__agents.values():
            agent_id = agent.agent_id()
            properties = agent.culture_properties()
            for property in properties:
                value = agent.__dict__.get(property, None)
                file.write("{} {} VALUE {}\n".format(agent_id, property, value))
        file.write("END")
        file.close()

#
# if __name__ == "__main__":
#     sim = Simulator(10, 10)
#     sim.create_random_obstacles(40)
#     sim.create_random_agents(5)
#     sim.assign_random_goals()
#     sim.update_agents(0)
