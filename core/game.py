import time
from world import World
from interactive_argument import InteractiveArgument
from edict import Broadcaster
from utils import *

class Game():
	direction_char_dict = {
		MoveDirection.UP: 'U',
		MoveDirection.DOWN: 'D',
		MoveDirection.LEFT: 'L',
		MoveDirection.RIGHT: 'R',
		MoveDirection.WAIT: 'W',
	}

	def __init__(self, width, height, filename=None, player_id=None):
		self.player_id = player_id
		self.simulator = World(width, height, filename, player_id)

		print("Starting grid with dimensions {} {}".format(width, height))

		self.agent_selected = None

		# TODO: Re-add progress widget later
		# #######################################
		# # Creating simulation progress widget #
		# #######################################
		self.step_slider = 0
		self.step_slider_max = self.simulator.simulation_size()

		self.update_step(0)

		self.start_timer()
		self.hint_label = ''
		self.property_label = ''

		#######################
		# Edict subscriptions #
		#######################

		Broadcaster().subscribe("/property_label/raw", self.set_property_label)
		Broadcaster().subscribe("/score_changed", self.set_score)
		Broadcaster().subscribe("/first_move", self.start_timer)
		Broadcaster().subscribe("/new_hint", self.set_hint_label)

		Broadcaster().subscribe("/cell_pressed", self.cell_pressed)
		Broadcaster().subscribe("/human_collision", self.show_collision_dialogue)
		Broadcaster().subscribe("/advance_simulation", self.advance_simulation)
		Broadcaster().subscribe("/game_over", self.show_game_over)
		# Broadcaster().subscribe("/model_updated", self.update_agents)

	def get_reward(self):
		return self.current_score - self.time_penalty

	def get_goal(self):
		return self.simulator.get_goal()

	def do_agent_action(self, current_direction):
		if current_direction not in self.direction_char_dict:
			return
		self.current_direction = current_direction
		direction_char = self.direction_char_dict[current_direction]
		Broadcaster().publish("/direction_chosen", self.current_direction)
		Broadcaster().publish("/new_event", direction_char)
		Broadcaster().publish("/advance_simulation")
		print("Action performed!")
		#print('Agents in range: ',self.simulator.get_agents_in_range())
		if len(self.simulator.get_agents_in_range()) < 2:
			self.hint_label = ''
			self.property_label = ''

	def get_cell_information(self, x, y):
		Broadcaster().publish("/cell_pressed", (x,y))

	def set_hint_label(self, cpu_agent_id, text):
		prefix = "Hint (Agent {}): ".format(cpu_agent_id)
		self.hint_label = prefix + text

	def set_property_label(self, text):
		print("Setting property label")
		self.property_label = text

	def start_timer(self):
		self.is_over = False
		self.time = 0
		self.timer = 1000
		self.current_score = 100
		self.time_penalty = 0

	def countdown_timer_label(self):
		self.time += 1
		if self.time % 10 == 0:
			self.time_penalty += 1
			Broadcaster().publish("/score_changed", self.current_score)
			Broadcaster().publish("/time_penalty")

	def set_score(self, score):
		self.current_score = score
		print("Score: " + str(score))

	def show_game_over(self):
		self.is_over = True
		self.simulator.save_results()
		print("Congratulations! You have reached the goal.")

	def rewind_simulation(self):
		self.step_slider = 0

	def skip_to_end_simulation(self):
		self.step_slider = self.step_slider_max

	def reset_human_direction(self):
		Broadcaster().publish("/direction_chosen", self.current_direction)
		self.update_agents()

	def advance_simulation(self):
		if self.current_step() == self.step_slider_max:
			self.run_step()
			return
		self.step_slider = self.current_step() + 1

	def retreat_simulation(self):
		if self.current_step() > 0:
			self.step_slider = self.current_step() - 1

	def cell_pressed(self, coord):
		cell_value = self.simulator.cell_at(coord, self.step_slider)
		if cell_value > 0:  # If cell pressed is agent.
			self.agent_selected = cell_value
			# Request properties to display in side panel.
			Broadcaster().publish("/highlighted_agent", self.agent_selected)
		else:
			self.agent_selected = None

	def run_step(self):
		success = self.simulator.simulate_step()
		if success:
			self.update_step(self.step_slider + 1)
			self.reset_human_direction()  # TODO: Remove hideous workaround

	def show_collision_dialogue(self):
		print("You have collided with another officer and it was your fault. Lose 5 points.")

	def update_agents(self):
		step = self.current_step()
		print("Update agents for step {}".format(step))
		self.simulator.update_agents(step)
		agents = self.simulator.agents()
		# FIXME: Should pass agents instead of creating all those data structures.
		world_models = {}
		plans = {}
		optimal_plans = {}
		visibilities = {}
		positions = {}
		goals = {}
		for agent in agents.values():
			positions[agent.agent_id()] = agent.current_pos()
			world_models[agent.agent_id()] = agent.world_model_at(step)
			plans[agent.agent_id()] = agent.plan_at(step)
			optimal_plans[agent.agent_id()] = agent.optimal_plan_at(step)
			visibilities[agent.agent_id()] = agent.visibility_radius()
			goals[agent.agent_id()] = agent.goal()

	def update_step(self, step=-1):
		if step == -1:
			step = self.step_slider
		maximum = self.simulator.simulation_size() - 1
		self.step_slider_max = maximum
		self.step_slider = step
		self.update_agents() # TODO: Remove duplicate call
		self.simulator.communicate()
		self.update_agents()

	def current_step(self):
		return self.step_slider
