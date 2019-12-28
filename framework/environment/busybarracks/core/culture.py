from argument import ArgumentationFramework
from game_agent import Agent

class Culture:
    def __init__(self):
        self.argumentation_framework = ArgumentationFramework()
        self.participating_agents = set()
        self.properties = {}
        self.name = None

        self.create_arguments()
        self.define_attacks()

    def create_arguments(self):
        pass

    def initialise_random_values(self, agent: Agent):
        pass

    def define_attacks(self):
        pass

    def add_participating_agent(self, agent):
        self.participating_agents.add(agent)

    def add_participating_agents(self, agents: list):
        for agent in agents:
            self.add_participating_agent(agent)
