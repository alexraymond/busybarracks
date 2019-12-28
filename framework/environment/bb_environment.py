# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
import time

from collections import deque
from environment.environment import Environment
import numpy as np
import options
flags = options.get()

import os
import sys
bb_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'busybarracks')
sys.path.append(os.path.join(bb_path,'core'))

from game import Game

import warnings
warnings.filterwarnings('ignore')

MODULE_URL = {
	'USE_Transformer': {
		'local':'/Users/toor/Desktop/NLP/Tutorials/Sentence Embedding/Universal Sentence Encoder/slow', 
		'remote': 'https://tfhub.dev/google/universal-sentence-encoder-large/3',
	},
	'USE_DAN': {
		'local':'/Users/toor/Desktop/NLP/Tutorials/Sentence Embedding/Universal Sentence Encoder/fast',
		'remote': 'https://tfhub.dev/google/universal-sentence-encoder/2',
	},
	'USE_MLQA': {
		'local':'/Users/toor/Desktop/NLP/Tutorials/Sentence Embedding/Universal Sentence Encoder/multilingual-qa',
		'remote': 'https://tfhub.dev/google/universal-sentence-encoder-multilingual-qa/1',
	},
}

class DocEmbedder():
	__tf_placeholders_dict = None
	__session = None
	__docvec_dict = {}
	__tf_model = None
	
	@property
	def docvec_dict(self):
		return DocEmbedder.__docvec_dict
	
	## the attribute name and the method name must be same which is used to set the value for the attribute
	@docvec_dict.setter
	def docvec_dict(self, var):
		DocEmbedder.__docvec_dict = var
	
	@staticmethod
	def load_tf_model(tf_model):
		import tensorflow as tf
		tf.get_logger().setLevel('ERROR') # Reduce logging output.
		from tensorflow_hub import Module as TFHubModule
		import tf_sentencepiece
		
		# Create graph and finalize (finalizing optional but recommended).
		g = tf.Graph()
		with g.as_default():
			# We will be feeding 1D tensors of text into the graph.
			text_input = tf.placeholder(dtype=tf.string, shape=[None])
			model_dict = MODULE_URL[tf_model]
			model_url = model_dict['local'] if os.path.isdir(model_dict['local']) else model_dict['remote']
			print('## Loading TF model <{}> from: {}...'.format(tf_model,model_url))
			embed = TFHubModule(model_url, trainable=False)
			print('## TF model loaded')
			embedded_text = embed(text_input)
			init_op = tf.group([tf.global_variables_initializer(), tf.tables_initializer()])
		g.finalize() # Finalizes this graph, making it read-only.
		
		# Create session and initialize.
		session = tf.Session(graph=g, config=tf.ConfigProto(use_per_session_threads=False))
		session.run(init_op)
		tf_placeholders = {
			'embedded_text': embedded_text,
			'text_input': text_input
		}
		return tf_placeholders, session

	@staticmethod
	def cached_embed(queries):
		missing_queries = [q for q in queries if q not in DocEmbedder.__docvec_dict] 
		if len(missing_queries) > 0:
			embeddings = DocEmbedder.embed(missing_queries)
			DocEmbedder.__docvec_dict.update({doc:vec for doc,vec in zip(missing_queries, embeddings)})
		query_embeddings = [DocEmbedder.__docvec_dict[q] for q in queries]
		return query_embeddings
	
	@staticmethod
	def embed(doc_list):
		# Feed doc_list into current tf graph
		embedding = DocEmbedder.__session.run(
			DocEmbedder.__tf_placeholders_dict['embedded_text'], 
			feed_dict={DocEmbedder.__tf_placeholders_dict['text_input']: doc_list}
		)
		return embedding

	def __init__(self, tf_model=None):
		# Load TF model
		if tf_model is None:
			__tf_placeholders_dict = None
			__session = None
			__docvec_dict = {}
			__tf_model = None
		elif tf_model != DocEmbedder.__tf_model:
			if DocEmbedder.__tf_model is None:
				DocEmbedder.__tf_model = tf_model
				DocEmbedder.__tf_placeholders_dict, DocEmbedder.__session = DocEmbedder.load_tf_model(tf_model)
			else:
				raise ValueError('Cannot load {} in this process, because {} has been already loaded.'.format(tf_model, DocEmbedder.__tf_model))
		
class BBEnvironment(Environment):
	filename = os.path.join(bb_path,'grid','DX.grd')
	max_step = 100
	state_scaler = 1.
	
	def get_action_shape(self):
		return [(1,len(self.actions_set))] # take 1 action of n possible types
		
	def get_state_shape(self):
		return [
			(self.max_x, self.max_y, 3),
			(1, 512, 2),
		]
	
	def __init__(self, id):
		self.id = id
		# setup environment
		self.max_x, self.max_y = map(int, open(self.filename, "r").readline().split())
		self.actions_set = list(Game.direction_char_dict.keys())
		self.__game_view_shape, self.__property_view_shape = self.get_state_shape()
		self.__grid_shape = self.__game_view_shape[:-1]
		self.__doc_embedder = DocEmbedder('USE_DAN')
		self.__game_thread = None
		self.__input_queue = Queue()
		self.__output_queue = Queue()

	def stop(self):
		if self.__game_thread is not None:
			self.__input_queue.put(None)
			self.__game_thread.join()
			self.__game_thread.terminate()
			self.__game_thread = None

	def reset(self, data_id=None):
		self.stop()
		self.__game_thread = Process(
			target=self.game_worker, 
			args=(self.__input_queue, self.__output_queue, self.max_x, self.max_y, self.filename)
		)
		self.__game_thread.start()
		#time.sleep(0.1)
		self.last_observation = self.__output_queue.get()
		self.last_state = self.normalize(self.last_observation['state'])
		self.last_reward = 0
		self.last_action = None
		self.step = 0
		#print(self.id, self.step)
		return self.last_state	
		
	def normalize(self, state_dict):
		goal_slice = np.zeros(self.__grid_shape)
		goal_x, goal_y = state_dict['goal']
		goal_slice[goal_x,goal_y] = 1
		wall_slice = np.clip(-state_dict['grid'], 0,1)
		enemy_slice = np.clip(state_dict['grid']-1, 0,float('inf'))
		player_slice = np.array(state_dict['grid'])
		player_slice[player_slice != 1] = 0
		game_view = (goal_slice,wall_slice,player_slice)
		game_view = np.reshape(game_view, self.__game_view_shape)
		property_view = self.__doc_embedder.cached_embed((state_dict['property'], state_dict['hint']))
		property_view = np.reshape(property_view, self.__property_view_shape)
		return (game_view, property_view)
	
	def get_screen(self):
		return {'ASCII': list(map(lambda x:list(map(str,x)), self.last_observation['state']['grid']))}
		
	def process(self, action_vector):
		self.__input_queue.put(self.actions_set[action_vector[0]])
		if self.__game_thread.is_alive():
			self.last_observation = self.__output_queue.get()
			is_terminal = self.last_observation['is_over']
			self.last_state = self.normalize(self.last_observation['state'])
			self.last_reward = self.last_observation['reward'] if not is_terminal else 1
			self.last_action = action_vector
		else:
			is_terminal = True
		# complete step
		self.step += 1
		#print(self.id, self.step, is_terminal)
		# Check steps constraints, cannot exceed given limit
		if self.step > self.max_step:
			is_terminal = True
		return self.last_state, self.last_reward, is_terminal, None

	@staticmethod
	def game_worker(input_queue, output_queue, max_x, max_y, filename):
		def get_observation_dict(game):
			step = game.current_step()
			return {
				'state': {
					'grid': game.simulator.grid_at(step),
					'goal': game.get_goal(),
					'property': game.property_label,
					'hint': game.hint_label,
				},
				'score': game.get_score(),
				'step': step,
				'is_over': game.is_over,
			}
		game = Game(max_x, max_y, filename)
		last_score = game.get_score()
		observation_dict = get_observation_dict(game)
		observation_dict['reward'] = observation_dict['score']-last_score
		output_queue.put(observation_dict)
		try:
			while not game.is_over:
				action = input_queue.get()
				if action is None:   # If you send `None`, the thread will exit.
					break
				game.do_agent_action(action)
				step = game.current_step()
				observation_dict = get_observation_dict(game)
				observation_dict['reward'] = observation_dict['score']-last_score
				output_queue.put(observation_dict) # step will always be > 0
				last_score = game.get_score()
		except:
			pass
	