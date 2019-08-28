from culture import Culture
from argument import Argument, ArgumentationFramework
from agent import Agent
from enum import Enum
import numpy as np

class MediumCulture(Culture):
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Medium"
        self.properties = {"Military Rank": 0,
                           "Tasked Status": "At Ease",
                           "Task Importance": 0,
                           "Special Ops": "No"}


    def create_arguments(self):
        """
        Defines set of arguments present in the culture.
        :return: Set of arguments.
        """
        args = []

        motion = Argument(0, "You must give way to me.")
        motion.set_generator(lambda gen: True)  # Propositional arguments are always valid.
        args.append(motion)

        arg1 = Argument(1, "My military rank is higher than yours.")

        def arg1_generator(my: Agent, their: Agent):
            return my["Military Rank"] > their["Military Rank"]

        arg1.set_generator(arg1_generator)
        args.append(arg1)

        arg2 = Argument(2, "However, I am currently performing a task and you are not.")

        def arg2_generator(my: Agent, their: Agent):
            return my["Tasked Status"] == "Tasked" and their["Tasked Status"] == "At Ease"

        arg2.set_generator(arg2_generator)
        args.append(arg2)

        arg3 = Argument(3, "However, my task is more important than yours.")

        def arg3_generator(my: Agent, their: Agent):
            return my["Task Importance"] > their["Military Rank"] and my["Task Importance"] > their["Task Importance"]

        arg3.set_generator(arg3_generator)
        args.append(arg3)

        arg4 = Argument(4, "I am a Special Ops officer, so my rank is 3 levels\n higher than it shows.")
        def arg4_generator(my: Agent, their: Agent):
            my_military_rank = my["Military Rank"] if my["Tasked Status"] == "At Ease" else my["Task Importance"]
            their_military_rank = their["Military Rank"] if their["Tasked Status"] == "At Ease" else their[
                "Task Importance"]
            return my["Special Ops"] == "Yes" and their["Special Ops"] == "No" and \
                   my_military_rank + 3 > their_military_rank

        arg4.set_generator(arg4_generator)
        args.append(arg4)

        self.argumentation_framework.add_arguments(args)

    def initialise_random_values(self, agent: Agent):
        rank = np.random.randint(1, 7)
        agent.assign_property_value("Military Rank", rank)

        tasked_status = "Tasked" if np.random.randint(0, 5) != 0 else "At Ease"
        agent.assign_property_value("Tasked Status", tasked_status)

        task_importance = np.random.randint(rank, 7)
        agent.assign_property_value("Task Importance", task_importance)
        
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
        arg4_id = 4

        self.argumentation_framework.add_attack(arg1_id, motion_id)
        self.argumentation_framework.add_attack(arg2_id, motion_id)
        self.argumentation_framework.add_attack(arg2_id, arg1_id)
        self.argumentation_framework.add_attack(arg2_id, arg3_id)
        self.argumentation_framework.add_attack(arg3_id, arg1_id)
        self.argumentation_framework.add_attack(arg3_id, motion_id)
        self.argumentation_framework.add_attack(arg4_id, arg3_id)
        self.argumentation_framework.add_attack(arg4_id, arg1_id)
        self.argumentation_framework.add_attack(arg4_id, motion_id)



