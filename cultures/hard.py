from culture import Culture
from argument import Argument, ArgumentationFramework
from agent import Agent
from enum import Enum
import numpy as np

class HardCulture(Culture):
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Hard"
        self.properties = {"rank": 0,
                           "tasked_status": False,
                           "task_importance": 0,
                           "admin_rank": 0,
                           "special_ops": False,
                           "forces": "Admin"
                           }


    def create_arguments(self):
        """
        Defines set of arguments present in the culture.
        :return: Set of arguments.
        """
        args = []

        motion = Argument(0, "You must give way to me.")
        motion.set_generator(lambda gen: True)  # Propositional arguments are always valid.
        args.append(motion)

        arg1 = Argument(1, "My rank is higher than yours.")
        def arg1_generator(my: Agent, their: Agent):
            return my.rank > their.rank
        arg1.set_generator(arg1_generator)
        args.append(arg1)

        arg2 = Argument(2, "I am currently performing a task and you are not.")
        def arg2_generator(my: Agent, their: Agent):
            return my.tasked_status is True and their.tasked_status is False
        arg2.set_generator(arg2_generator)
        args.append(arg2)

        arg3 = Argument(3, "I have been tasked by someone with a higher rank.")
        def arg3_generator(my: Agent, their: Agent):
            return my.task_importance > their.rank and my.task_importance > their.task_importance
        arg3.set_generator(arg3_generator)
        args.append(arg3)

        self.argumentation_framework.add_arguments(args)

    def initialise_random_values(self, agent: Agent):
        rank = np.random.randint(1, 7)
        agent.assign_property_value("rank", rank)

        tasked_status = True if np.random.randint(0, 5) != 0 else False
        agent.assign_property_value("tasked_status", tasked_status)

        task_importance = np.random.randint(rank, 7)
        agent.assign_property_value("task_importance", task_importance)

    class ArgumentID(Enum):
        CHANGE_YOUR_ROUTE = 0
        RANK_IS_HIGHER = 1
        I_AM_TASKED = 2
        TASK_IMPORTANCE = 3

    def define_attacks(self):
        """
        Defines attack relationships present in the culture.
        :return: Attack relationships.
        """
        motion_id = 0
        arg1_id = 1
        arg2_id = 2
        arg3_id = 3

        self.argumentation_framework.add_attack(arg1_id, motion_id)
        self.argumentation_framework.add_attack(arg2_id, motion_id)
        self.argumentation_framework.add_attack(arg2_id, arg1_id)
        self.argumentation_framework.add_attack(arg2_id, arg3_id)
        self.argumentation_framework.add_attack(arg3_id, arg1_id)
        self.argumentation_framework.add_attack(arg3_id, motion_id)



