from itertools import count
import numpy as np
import collections
import copy

from systemd.journal import send

from grid2d import Grid2D, EMPTY, GLOBAL_OBSTACLE, LOCAL_OBSTACLE
from edict import Broadcaster
from utils import *
from interactive_argument import InteractiveArgument
from locution import *



class Agent:
    EXPLAINABLE = True

    def __init__(self, agent_id, grid_dimensions, simulator):
        self.__goal = None
        self.__plan = []
        self.__optimal_plan = []
        self.__known_cells = {}
        self.__agent_id = agent_id
        self.__visibility_radius = 2  # np.random.randint(4, 5)  # TODO: Change this.
        self.__current_pos = None
        self.__current_time_step = 0
        self.__latest_world_model = None
        self.__previous_world_models = {}
        self.__previous_plans = {}
        self.__previous_optimal_plans = {}
        self.__grid_width, self.__grid_height = grid_dimensions
        self.__simulator = simulator
        self.__other_agents_waypoints = {}
        self.__max_waypoints_per_locution = 2
        self.__arguments_used_this_round = set()
        self.__agents_estimated_plans = {}
        self.__agents_estimated_plan_lengths = {}
        self.__negotiated_with = set()
        self.__current_conflict = None
        self.__conceding_to_agents = set()

        self.__culture = None

        self.score = 100
        self.time_penalty = 0
        self.__human_controlled = False
        self.__current_direction = None
        self.__human_reply = None

        Broadcaster().subscribe("/time_penalty", self.count_time_penalty)

    def __getitem__(self, item):
        return self.__dict__.get(item, None)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def count_time_penalty(self):
        self.time_penalty += 1

    def is_human(self):
        return self.__human_controlled

    def is_AI(self):
        return not self.__human_controlled

    def set_human_control(self, control):
        self.__human_controlled = control
        if self.__human_controlled is True:
            if self.__current_pos is not None:
                self.__plan = [(self.__current_pos, self.__current_time_step)]
            Broadcaster().subscribe("/direction_chosen", self.set_direction)
            Broadcaster().subscribe("/new_time_step", self.change_score)
            Broadcaster().subscribe("/human_collision", self.score_collision)
            Broadcaster().subscribe("/human_reply", self.set_human_reply)

    def set_human_reply(self, reply):
        self.__human_reply = reply

    def score_collision(self):
        self.change_score(-20)

    def change_score(self, delta = -1):
        self.score += delta
        Broadcaster().publish("/score_changed", self.score)

    def set_direction(self, direction):
        if self.__human_controlled is False:
            return
        if self.__current_pos is not None:
            self.__plan[0] = (self.__current_pos, self.__current_time_step)
        x, y = self.__current_pos
        if direction == MoveDirection.UP and y > 0:
            self.__plan[1] = ((x, y - 1), self.__current_time_step+1)
        elif direction == MoveDirection.DOWN and y < self.__grid_height :
            self.__plan[1] = ((x, y + 1), self.__current_time_step+1)
        elif direction == MoveDirection.LEFT and x > 0:
            self.__plan[1] = ((x - 1, y), self.__current_time_step+1)
        elif direction == MoveDirection.RIGHT and x < self.__grid_width:
            self.__plan[1] = ((x + 1, y), self.__current_time_step+1)
        else:
            self.__plan[1] = ((x, y), self.__current_time_step+1)
        self.__current_direction = direction
        self.__previous_plans[self.__current_time_step] = copy.deepcopy(self.__plan)
        self.__previous_optimal_plans[self.__current_time_step] = copy.deepcopy(self.__optimal_plan)
        Broadcaster().publish("/score_changed", self.score)

    def culture_properties(self):
        if self.__culture is None:
            return
        return self.__culture.__dict__.get("properties", None)

    def get_properties_as_text(self):
        text = ""
        for property in self.culture_properties():
            value = self.__dict__.get(property, None)
            text += str(property) + ": " + str(value) + "\n"
        return text

    def set_culture(self, culture):
        self.__culture = culture
        if self.culture_properties() is None:
            print("Agent::set_culture: Culture {} has no properties.".format(culture.name))
            return
        for property, default_value in self.culture_properties().items():
            self.__setattr__(property, default_value)

    def assign_property_value(self, property, value):
        if hasattr(self, property) is False:
            print("Agent::assign_property_value: Property {} not found within agent.".format(property))
            return
        self.__setattr__(property, value)

    def agent_id(self):
        return self.__agent_id

    def visibility_radius(self):
        return self.__visibility_radius

    def assign_goal(self, goal):
        """
        Assigns a goal to the agent.
        :param goal: x,y tuple representing goal coordinates.
        """
        self.__goal = goal

    def set_current_pos(self, current_pos):
        """
        Informs the agent what is its current position.
        :param current_pos: x,y tuple representing current position.
        """
        self.__current_pos = current_pos

    def rebuild_partial_world_model(self):
        """
        Rebuilds a 2D grid representing the current knowledge/beliefs of the agent.
        :return: False if information is insufficient. True if successful.
        """
        if self.__current_pos is None:
            print("Agent::build_partial_world_model: Current position not defined.")
            return False
        self.__latest_world_model = Grid2D(self.__grid_width, self.__grid_height)
        for coord, cell in self.__known_cells.items():
            if Grid2D.is_obstacle(cell):
                self.__latest_world_model.add_obstacle(coord, cell)
            elif cell != EMPTY:
                self.__latest_world_model.add_agent(cell, coord)
        # print("\nVisible world for agent {0} ({3}) (radius {2}): \n{1}.".format(
        #     self.__agent_id, self.__latest_world_model.cells.transpose(), self.__visibility_radius, self.__current_pos))
        return True

    def update_world_knowledge(self, visible_cells, time_step, overwrite=False):
        """
        Receives information about visible cells at the current time step.
        This information overwrites previously conflicting data.
        :param visible_cells: dict {key=coord (x,y tuple), value=cell (int)}
        :param time_step: Current time step.
        """
        if time_step > self.__current_time_step:
            self.clear_negotiation_status()
        self.__current_time_step = time_step

        # Merging two dictionaries.
        self.__known_cells = {**self.__known_cells, **visible_cells}

        # This step is important to avoid repeated occurrences of agents.
        agents_found = {}
        for coord, cell in self.__known_cells.items():
            if cell > 0: # If is agent
                if cell in agents_found: # Conflict!
                    if visible_cells.get(coord, None) == cell: # If seen recently
                        self.__known_cells[agents_found[cell]] = EMPTY
                    else:
                        self.__known_cells[coord] = EMPTY
                agents_found[cell] = coord
        self.rebuild_partial_world_model()
        # If it's still the first model (editing enabled) or a new one, then allow copying.
        if overwrite or (len(self.__previous_world_models) <= 1 or time_step not in self.__previous_world_models):
            self.__previous_world_models[time_step] = copy.deepcopy(self.__latest_world_model)
        if self.__goal is None:
            return
        if self.__current_pos != self.__goal:
            self.__plan = self.find_path_3D_search((self.__current_pos, self.__current_time_step), self.__goal)
            self.__optimal_plan = self.find_path_3D_search((self.__current_pos, self.__current_time_step), self.__goal, concede_to_agents=False)
            if self.__human_controlled:
                pass
                # self.set_direction(self.__current_direction)
            if overwrite or (len(self.__previous_plans) <= 1 or time_step not in self.__previous_plans):
                self.__previous_plans[time_step] = copy.deepcopy(self.__plan)
                self.__previous_optimal_plans[time_step] = copy.deepcopy(self.__optimal_plan)
        # print("Path from {0} to {1}: {2}".format(self.__current_pos, self.__goal, self.__plan))
        # print("Turns from {0} to {1}: {2}".format(self.__current_pos, self.__goal, self.next_waypoints()))

    def find_path_BFS(self, origin, goal, ignore_agents=True):
        """
        Finds a path using Breadth-First Search.
        :param origin: (x,y) tuple representing start.
        :param goal: (x,y) tuple representing destination.
        :return: Returns a list of tuples (cells) representing a path. If goal is unreachable, returns None.
        """
        to_visit = collections.deque()
        came_from = {}
        to_visit.append(origin)
        came_from[origin] = None
        goal_found = False


        # Performs search and returns dict with previous steps for every vertex.
        while len(to_visit) > 0:
            current = to_visit.popleft()

            if current == goal:  # Found goal!
                goal_found = True
                break

            for neighbour in self.__latest_world_model.neighbours_of(current, 'von_neumann'):
                x, y = neighbour
                cell_condition = self.__latest_world_model.cells[x][y] >= 0 if ignore_agents \
                    else self.__latest_world_model.cells[x][y] == EMPTY
                if neighbour not in came_from and cell_condition:
                    to_visit.append(neighbour)
                    came_from[neighbour] = current

        if goal_found:  # Reconstructing path backwards from dict.
            path = list()
            path.append(goal)
            current = came_from[goal]
            while current != origin:
                path.append(current)
                current = came_from[current]
            path.append(origin)
            path.reverse()
            return path

        print("Agent::find_path_BFS: Agent {} could not reach its goal.".format(self.__agent_id))
        return None

    def find_path_3D_search(self, origin, goal, initial_time_step=None, concede_to_agents=True, timeout=100):
        # if self.__human_controlled is True:
        #     return self.__plan
        if initial_time_step is None:
            initial_time_step = self.__current_time_step

        to_visit = collections.deque()
        came_from = {}
        to_visit.append(origin)
        came_from[origin] = None
        goal_found = False

        # Performs search and returns dict with previous steps for every vertex.
        while len(to_visit) > 0:
            current = to_visit.popleft()

            if current[TIME_STEP] - initial_time_step > timeout:
                print("Agent::find_path_3D_search: Search has timed out.".format(self.__agent_id))
                break

            if current[POS] == goal:  # Found goal!
                if concede_to_agents and len(self.__conceding_to_agents) > 0:  # Wait if not conceding.
                    # Calculate when it's the last occurrence that they traverse your cell.
                    last_occurrence_time_step = 0
                    for agent in self.__conceding_to_agents:
                        for step in self.__agents_estimated_plans[agent]:
                            if step[POS] == current[POS]:
                                if last_occurrence_time_step < step[TIME_STEP]:
                                    last_occurrence_time_step = step[TIME_STEP]
                    if current[TIME_STEP] > last_occurrence_time_step:
                        goal_found = True
                        break
                else:
                    goal_found = True
                    break

            neighbours = self.__latest_world_model.neighbours_of(current[POS], 'von_neumann')
            wait_step = current[POS]
            neighbours.append(wait_step)

            for neighbour in neighbours:
                x, y = neighbour
                neighbouring_step = (neighbour, current[TIME_STEP] + 1)
                if neighbouring_step not in came_from and self.__latest_world_model.cells[x][y] >= 0:
                    if concede_to_agents:
                        conflict = False
                        for agent in self.__conceding_to_agents:
                            their_plan = self.__agents_estimated_plans[agent]
                            my_position = (current[POS], current[TIME_STEP] + 1)
                            coming_to_my_position = True if my_position in their_plan else False
                            time_step = current[TIME_STEP]
                            if current[TIME_STEP] >= their_plan[-1][TIME_STEP]:
                                time_step = their_plan[-1][TIME_STEP]
                            their_position = [pos for pos in their_plan if pos[TIME_STEP] == time_step][0]
                            going_to_their_position = neighbouring_step == (their_position[POS], current[TIME_STEP] + 1)
                            if neighbouring_step in their_plan:
                                conflict = True
                            elif coming_to_my_position and going_to_their_position:
                                conflict = True

                        if conflict:
                            continue

                    to_visit.append(neighbouring_step)
                    came_from[neighbouring_step] = current

        if goal_found:  # Reconstructing path backwards from dict.
            path = list()
            path.append(current)
            current = came_from[current]
            while current != origin and current is not None:
                path.append(current)
                current = came_from[current]
            path.append(origin)
            path.reverse()
            return path

        print("Agent::find_path_3D_search: Agent {} could not reach its goal.".format(self.__agent_id))
        return None



    def next_waypoints(self):
        if self.__plan is None:
            return None
        if len(self.__plan) < 2:
            return None
        WEST = 0
        EAST = 1
        NORTH = 2
        SOUTH = 3
        def direction(p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            if x1 > x2:
                return EAST
            elif x1 < x2:
                return WEST
            elif y1 > y2:
                return SOUTH
            elif y1 < y2:
                return NORTH
            else:
                return -1

        turns = []
        current_direction = direction(self.__plan[0][POS], self.__plan[1][POS])
        for i in range(len(self.__plan) - 1):
            new_direction = direction(self.__plan[i][POS], self.__plan[i+1][POS])
            if new_direction != current_direction:
                turns.append(self.__plan[i])
                current_direction = new_direction
        # if self.__human_controlled is True:
        #     estimated_path = self.estimated_path((self.__current_pos, self.__current_time_step), self.__goal)
        #     turns.append(estimated_path[-1])
        # else:
        turns.append(self.__plan[-1])
        return turns

    def next_turn(self):
        if self.next_waypoints() is None:
            return None
        return self.next_waypoints()[0]

    def find_agents_in_range(self):
        # Listing agents in communication/visibility range.
        agents_in_range = {}
        grid = self.__latest_world_model.cells
        vr = self.__visibility_radius
        pos = self.__current_pos
        time_step = self.__current_time_step
        for i in range(self.__grid_width):
            for j in range(self.__grid_height):
                if is_agent(grid[i][j]) and in_visibility_range(vr, pos, (i, j)):
                    agents_in_range[grid[i][j]] = ((i, j), time_step)
        return agents_in_range

    def communicate(self):
        agents_in_range = self.find_agents_in_range()

        for other_agent_id in agents_in_range.keys():
            if self.__agent_id == other_agent_id:
                continue
            # Check if we already know their destination.
            # TODO: This is only a partial destination. Need to ask again after a while.
            # if other_agent_id not in self.__other_agents_waypoints:
            if other_agent_id not in self.__negotiated_with:
                # Ask for their objective.
                locution = Locution(ActType.ASK, ContentType.WAYPOINTS)
                self.__simulator.send_locution(self.__agent_id, other_agent_id, locution)

    def straight_line_obstructions(self, origin, destination):
        # Checks for obstructions in a straight line.
        if origin[POS] == destination[POS]:
            return []
        time_step = origin[TIME_STEP]
        x1, y1 = origin[POS]
        x2, y2 = destination[POS]
        VERTICAL = x1 == x2

        # TODO: Use utils.straight_line_path instead
        obstructions = []
        if VERTICAL:
            south = min(y1, y2)
            north = max(y1, y2)
            for i in range(north - south + 1):
                if self.__latest_world_model.cells[x1][south + i] == LOCAL_OBSTACLE:
                    obstructions.append(((x1, south + i), time_step + i))
        else:
            west = min(x1, x2)
            east = max(x1, x2)
            for i in range(east - west + 1):
                if self.__latest_world_model.cells[west + i][y1] == LOCAL_OBSTACLE:
                    obstructions.append(((west + i, y1), time_step + i))

        return obstructions

    def estimated_path(self, origin, waypoints):
        path = []
        time_step = self.__current_time_step
        if waypoints:
            for i in range(len(waypoints) - 1):
                leg = straight_line_path(origin, waypoints[i])
                path.extend(leg)
                origin = waypoints[i]
            last_leg = self.find_path_3D_search(origin, waypoints[-1][POS], initial_time_step=time_step, concede_to_agents=False)
            path.extend(last_leg)
            no_duplicates = list(collections.OrderedDict.fromkeys(path))
        return no_duplicates



    def receive_locution(self, sender_id, received_locution: Locution):
        log = ""
        print("Received locution {}".format(received_locution))
        if received_locution.act_type() == ActType.ASK:
            # It is a question. Requires reply.
            if received_locution.content_type() == ContentType.WAYPOINTS:
                # They are asking for our next waypoint.
                log = "{0} asks {1} about their next waypoints.".format(sender_id, self.__agent_id)
                Broadcaster().publish("/log/raw", log)

                turns = self.next_waypoints()
                next_turns = None
                if turns is not None:
                    next_turns = []
                    for i in range(self.__max_waypoints_per_locution):
                        if i >= len(self.next_waypoints()):
                            break
                        next_turns.append(turns[i])

                reply = Locution(ActType.INFORM, ContentType.WAYPOINTS, waypoints=next_turns)
                self.__simulator.send_locution(self.__agent_id, sender_id, reply)

        elif received_locution.act_type() == ActType.INFORM:
            if received_locution.content_type() == ContentType.WAYPOINTS:
                # They are informing their next waypoints.
                their_next_waypoints = received_locution.content()['waypoints']
                log = "{0} informs {1} that their next waypoints are {2}".format(sender_id, self.__agent_id, their_next_waypoints)
                Broadcaster().publish("/log/raw", log)

                # Check if the other agent is in collision route with any obstacle or agent.
                self.__other_agents_waypoints[sender_id] = their_next_waypoints
                their_position = self.find_agents_in_range()[sender_id]
                if their_position is None:
                    return
                if their_next_waypoints is None:
                    return
                obstructions = []
                self.__agents_estimated_plans[sender_id] = []
                start = their_position
                for waypoint in their_next_waypoints:
                    obs = self.straight_line_obstructions(start, waypoint)
                    if len(obs) > 0:
                        obstructions.append(obs)
                    start = waypoint
                if len(obstructions) > 0:
                    # Inform them about the last obstacle detected.
                    for i in range(self.__max_waypoints_per_locution):
                        if i >= len(obstructions):
                            break
                    inform = Locution(ActType.INFORM, ContentType.OBSTACLE, obstacle=obstructions[0])
                    self.__simulator.send_locution(self.__agent_id, sender_id, inform)
                else:
                    # TODO: Handle case where we have both obstructions and path conflicts.
                    test_path = self.estimated_path(their_position, their_next_waypoints)
                    self.__agents_estimated_plans[sender_id] = self.estimated_path(their_position, their_next_waypoints)

                    self.__agents_estimated_plan_lengths[sender_id] = len(self.__agents_estimated_plans[sender_id])
                    print("Estimated path of agent {}: {}".format(sender_id, self.__agents_estimated_plans[sender_id]))
                    conflict = find_conflicts_between_paths(self.__plan, self.__agents_estimated_plans[sender_id], self.__current_time_step, 4)
                    illegal_swap_time_step = illegal_position_swap(self.__plan, self.__agents_estimated_plans[sender_id], 4)
                    print("Conflict? {}".format(conflict))
                    print("Swap? {}".format(illegal_swap_time_step))

                    # If a conflict happens after an illegal swap, consider the swap as the conflict
                    if illegal_swap_time_step is not None:
                        if conflict is None or conflict[TIME_STEP] > illegal_swap_time_step:
                            conflict = [pos for pos in self.__plan if pos[TIME_STEP] == illegal_swap_time_step][0]


                    if conflict is not None and sender_id not in self.__negotiated_with:
                        # Start argumentation. Ask your opponent to change paths.
                        self.__negotiated_with.add(sender_id)
                        self.__current_conflict = conflict
                        if sender_id not in self.__conceding_to_agents:
                            locution = Locution(ActType.ARGUE, ContentType.ARGUMENT, argument_id=0, conflict=conflict)  # TODO: Add enum to argument_id
                            self.__simulator.send_locution(self.__agent_id, sender_id, locution)
                        else:
                            self.reroute_avoiding()


                # TODO: Do something smart with the sender's waypoint.

            elif received_locution.content_type() == ContentType.OBSTACLE:
                # They are letting us know about an obstacle.
                obstacles = received_locution.content()['obstacle']
                log = "{0} informs {1} about obstacles at positions {2}".format(sender_id, self.__agent_id, obstacles)
                Broadcaster().publish("/log/raw", log)

                obstacles_dict = {}
                for obstacle in obstacles:
                    obstacles_dict[obstacle[POS]] = LOCAL_OBSTACLE

                self.update_world_knowledge(obstacles_dict, self.__current_time_step, overwrite=True)

            elif received_locution.content_type() == ContentType.ANOTHER_AGENT:
                spotted_agent_id, spotted_agent_pos = received_locution.content()
                log = "{0} informs {1} about the presence of agent {2} at position {3}".format(sender_id, self.__agent_id,
                                                                                               spotted_agent_id, spotted_agent_pos)
                Broadcaster().publish("/log/raw", log)

                self.update_world_knowledge({spotted_agent_pos: spotted_agent_id}, self.__current_time_step, overwrite=True)

        elif received_locution.act_type() == ActType.ARGUE:
            if received_locution.content_type() == ContentType.ARGUMENT:
                self.__negotiated_with.add(sender_id)
                AF = self.__culture.argumentation_framework
                # Read useful information from their argument.
                their_locution_content = received_locution.content()
                their_argument_id = their_locution_content['argument_id']
                argument_text = AF.argument(their_argument_id).descriptive_text()
                log = "{0} argues to {1}: {2} ({3})".format(sender_id, self.__agent_id, argument_text, received_locution.content())
                Broadcaster().publish("/log/raw", log)


                # Time to fight back.
                argument_possibilities = AF.arguments_that_attack(their_argument_id)
                rebuttals = {}
                for argument_id in argument_possibilities:
                    print("Argument_id: {}".format(argument_id))
                    sender = self.__simulator.agent(sender_id)
                    if AF.argument(argument_id).generate(self, sender):
                        if argument_id not in self.__arguments_used_this_round:
                            rebuttals[argument_id] = AF.argument(argument_id)
                    # generate_argument(argument_id)
                # Remove arguments that have already been used.

                gen = (arg for arg in rebuttals.values() if arg is not None)
                acceptable_arguments = []
                for arg in gen:
                    acceptable_arguments.append(arg)
                    print("Plausible argument from {}: {}".format(their_argument_id, arg))

                if len(acceptable_arguments) > 0:
                    # Rebuttal.
                    # TODO: Remove randomness. Should pick best argument.
                    index = np.random.randint(0, len(acceptable_arguments))
                    chosen_arg_id = acceptable_arguments[index].id()
                    print("Acceptable arguments: {}".format(acceptable_arguments))
                    print("Chosen argument: {}".format(chosen_arg_id))
                    self.__arguments_used_this_round.add(chosen_arg_id)
                    # chosen_arg_id = acceptable_arguments[chosen_arg].id()
                    locution = Locution(ActType.ARGUE, ContentType.ARGUMENT, argument_id=chosen_arg_id)
                    self.__simulator.send_locution(self.__agent_id, sender_id, locution)
                else:
                    # Concede defeat.
                    self.__conceding_to_agents.add(sender_id)
                    log = "{0} convinced {1}.".format(sender_id, self.__agent_id)
                    Broadcaster().publish("/log/raw", log)
                    # Check if it knows the winner's intentions.
                    if sender_id not in self.__agents_estimated_plans:
                        locution = Locution(ActType.ASK, ContentType.WAYPOINTS)
                        self.__simulator.send_locution(self.__agent_id, sender_id, locution)
                    self.reroute_avoiding()
                    self.__negotiated_with = self.__conceding_to_agents
                    unsuccessful_arguments = self.__arguments_used_this_round
                    locution = Locution(ActType.CONCEDE, ContentType.MULTIPLE_ARGUMENTS, failed_arguments=list(unsuccessful_arguments))
                    self.__simulator.send_locution(self.__agent_id, sender_id, locution)
                    log = "{0} rerouted to {1}".format(self.__agent_id, self.__plan)
                    Broadcaster().publish("/log/raw", log)

        elif received_locution.act_type() == ActType.CONCEDE:
            cpu_agent_id = sender_id if sender_id != HUMAN else self.agent_id()
            Broadcaster().publish("/highlighted_agent", cpu_agent_id)
            if received_locution.content_type() == ContentType.MULTIPLE_ARGUMENTS and Agent.EXPLAINABLE:
                print("\n########## VICTORIOUS ARGUMENTS ###########\n")
                AF = self.__culture.argumentation_framework
                victorious_arguments = list(self.__arguments_used_this_round)
                winner = "<font color=\"red\">your</font>"
                loser = "<font color=\"green\">their</font>"
                if self.__agent_id != HUMAN:
                    winner = "<font color=\"green\">their</font>"
                    loser = "<font color=\"red\">your</font>"
                for argument_id in victorious_arguments:
                    print(self.__culture.argumentation_framework.argument(argument_id).descriptive_text().format(winner, loser))
                print("\n########## LOSER ARGUMENTS ###########\n")
                print(received_locution.content()['failed_arguments'])
                failed_arguments = received_locution.content()['failed_arguments']
                for argument_id in failed_arguments:
                    print(self.__culture.argumentation_framework.argument(argument_id).descriptive_text().format(winner, loser))

                if len(failed_arguments) > 0:
                    conjunctions = ["Although", "Even though"]
                    failed_arguments = sorted(failed_arguments)
                    failed_argument_text = AF.argument(failed_arguments[-1]).descriptive_text().format(loser, winner)
                    hint = conjunctions[np.random.randint(len(conjunctions))] + " " + failed_argument_text + ", "
                    rebuttals_to_failed_argument = AF.arguments_that_attack(failed_arguments[-1])
                    used_arguments = [argument for argument in victorious_arguments if argument in rebuttals_to_failed_argument]
                    used_argument_text = AF.argument(used_arguments[0]).descriptive_text().format(winner, loser)
                    hint += used_argument_text + "."
                else:
                    if len(victorious_arguments) > 0:
                        hint = AF.argument(victorious_arguments[0]).descriptive_text().format(winner, loser) + "."
                        split_words = hint.split()
                        if split_words[1] == "color=\"red\">your</font>":
                            split_words[0] = "<font color=\"red\">Your</font>"
                            del split_words[1]
                        elif split_words[1] == "color=\"green\">their</font>":
                            split_words[0] = "<font color=\"green\">Their</font>"
                            del split_words[1]
                        else:
                            split_words[0].capitalize()
                        hint = ' '.join(split_words)
                    else:
                        hint = "There are no arguments that challenge " + winner + " right of way."


                Broadcaster().publish("/new_hint", cpu_agent_id, hint)




            Broadcaster().publish("/model_updated")

    def reroute_avoiding(self):
        self.__plan = self.find_path_3D_search((self.__current_pos, self.__current_time_step), self.__goal)
        print("Agent {} Rerouting: {}".format(self.__agent_id, self.__plan))


    def clear_negotiation_status(self):
        self.__arguments_used_this_round = set()
        self.__negotiated_with = set()
        self.__current_conflict = None

    def current_pos(self):
        return self.__current_pos

    def latest_world_model(self):
        return self.__latest_world_model.cells

    def world_model_at(self, t):
        return self.__previous_world_models[t].cells

    def latest_plan(self):
        return self.__plan

    def plan_at(self, t):
        return self.__previous_plans.get(t, None)

    def optimal_plan_at(self, t):
        return self.__previous_optimal_plans.get(t, None)

    def goal(self):
        return self.__goal

