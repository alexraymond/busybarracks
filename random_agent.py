import sys
sys.path.append('./core')

import random
from game import Game

import sys
filename = sys.argv[1]
player_id = sys.argv[2]

file = open(filename, "r")
dimensions = file.readline().split()
if len(dimensions) == 2:
	max_x, max_y = map(int,dimensions)
	actions_set = list(Game.direction_char_dict.keys())
	game = Game(max_x, max_y, filename, player_id)
	while not game.is_over:
		game.do_agent_action(random.choice(actions_set))
		print('State:')
		print('	- Grid:', game.simulator.grid_at(game.current_step()))
		print('	- Goal:', game.get_goal())
		print('	- Property:', game.property_label)
		print('	- Hint:', game.hint_label)
		print('Reward:', game.get_reward())
		print('Agents in Range:', game.simulator.get_agents_in_range())
