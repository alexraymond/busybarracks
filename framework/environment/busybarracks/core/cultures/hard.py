from culture import Culture
from argument import Argument, ArgumentationFramework
from game_agent import Agent
from enum import Enum
import numpy as np

class HardCulture(Culture):
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Hard"
        self.properties = {"Military Rank": 0,
                           "Tasked Status": "At Ease",
                           "Task Importance": 0,
                           "Corporate Rank": 0,
                           "Special Ops": "No",
                           "Department": "Admin"
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

        arg1 = Argument(1, "{0} Military Rank is higher than {1}s")
        def arg1_generator(my: Agent, their: Agent):
            return my["Military Rank"] > their["Military Rank"]
        arg1.set_generator(arg1_generator)
        args.append(arg1)

        arg2 = Argument(2, "{0} status is Tasked and {1} status is At Ease")
        def arg2_generator(my: Agent, their: Agent):
            return my["Tasked Status"] == "Tasked" and their["Tasked Status"] == "At Ease"
        arg2.set_generator(arg2_generator)
        args.append(arg2)

        arg3 = Argument(3, "{0} task is more important than {1}s")
        def arg3_generator(my: Agent, their: Agent):
            return my["Tasked Status"] == "Tasked" and \
                   my["Task Importance"] > their["Military Rank"] and \
                   my["Task Importance"] > their["Task Importance"]
        arg3.set_generator(arg3_generator)
        args.append(arg3)
        
        arg4 = Argument(4, "{0} combined rank is higher than {1} rank and task importance")
        def arg4_generator(my: Agent, their: Agent):
            my_military_rank = my["Military Rank"] if my["Tasked Status"] == "At Ease" else my["Task Importance"]
            my_overall_rank = my["Corporate Rank"] + my_military_rank
            their_military_rank = their["Military Rank"] if their["Tasked Status"] == "At Ease" else their["Task Importance"]
            their_overall_rank = their["Corporate Rank"] + their_military_rank
            return my_overall_rank > their["Task Importance"] and my_overall_rank > their_overall_rank
        arg4.set_generator(arg4_generator)
        args.append(arg4)
        
        arg5 = Argument(5, "{0} department is Admin (corporate rank + 2)")
        def arg5_generator(my: Agent, their: Agent):
            my_military_rank = my["Military Rank"] if my["Tasked Status"] == "At Ease" else my["Task Importance"]
            my_overall_rank = my["Corporate Rank"] + 2 + my_military_rank
            their_military_rank = their["Military Rank"] if their["Tasked Status"] == "At Ease" else their[
                "Task Importance"]
            their_overall_rank = their["Corporate Rank"] + their_military_rank
            return my["Department"] == "Admin" and \
                   my_overall_rank > their["Task Importance"] and\
                   my_overall_rank > their_overall_rank
        arg5.set_generator(arg5_generator)
        args.append(arg5)
        
        arg6 = Argument(6, "{0} combined rank is 3 levels higher because of Special Ops status")
        def arg6_generator(my: Agent, their: Agent):
            my_military_rank = my["Military Rank"] if my["Tasked Status"] == "At Ease" else my["Task Importance"]
            my_overall_rank = my["Corporate Rank"] + my_military_rank + 3
            their_military_rank = their["Military Rank"] if their["Tasked Status"] == "At Ease" else their[
                "Task Importance"]
            if their["Special Ops"] == "Yes" and their["Department"] != "Admin":
                their_military_rank += 3
            their_overall_rank = their["Corporate Rank"] + their_military_rank
            return my["Special Ops"] == "Yes" and \
                   my_overall_rank > their["Task Importance"] and \
                   my_overall_rank > their_overall_rank
        arg6.set_generator(arg6_generator)
        args.append(arg6)
        
        arg7 = Argument(7, "corporate ranks don't matter because both of you are from the same department")
        def arg7_generator(my: Agent, their: Agent):
            return my["Department"] == their["Department"]
        arg7.set_generator(arg7_generator)
        args.append(arg7)
        
        arg8 = Argument(8, "this rule does not apply because of {0} Special Ops status")
        def arg8_generator(my: Agent, their: Agent):
            return my["Special Ops"] == "Yes"
        arg8.set_generator(arg8_generator)
        args.append(arg8)
        
        arg9 = Argument(9, "{1} Special Ops benefits don't apply because {1} department is Admin")
        def arg9_generator(my: Agent, their: Agent):
            return their["Department"] == "Admin"
        arg9.set_generator(arg9_generator)
        args.append(arg9)
        
        self.argumentation_framework.add_arguments(args)

    def initialise_random_values(self, agent: Agent):
        rank = np.random.randint(1, 7)
        agent.assign_property_value("Military Rank", rank)

        tasked_status = "Tasked" if np.random.randint(0, 5) != 0 else "At Ease"
        agent.assign_property_value("Tasked Status", tasked_status)

        task_importance = np.random.randint(rank, 7)
        agent.assign_property_value("Task Importance", task_importance)

        corporate_rank = np.random.randint(1, 7)
        agent.assign_property_value("Corporate Rank", corporate_rank)

        special_ops = "Yes" if np.random.randint(0, 3) == 0 else "No"
        agent.assign_property_value("Special Ops", special_ops)

        categories = ["Army", "Navy", "Air Force", "Admin"]
        agent.assign_property_value("Department", categories[np.random.randint(0, 4)])

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
        a1 = 1
        a2 = 2
        a3 = 3
        a4 = 4
        a5 = 5
        a6 = 6
        a7 = 7
        a8 = 8
        a9 = 9

        self.argumentation_framework.add_attack(a1, motion_id)
        self.argumentation_framework.add_attack(a2, motion_id)
        self.argumentation_framework.add_attack(a3, motion_id)
        self.argumentation_framework.add_attack(a4, motion_id)
        self.argumentation_framework.add_attack(a5, motion_id)
        self.argumentation_framework.add_attack(a6, motion_id)
        self.argumentation_framework.add_attack(a2, a1)
        self.argumentation_framework.add_attack(a2, a3)
        self.argumentation_framework.add_attack(a3, a1)
        self.argumentation_framework.add_attack(a4, a3)
        self.argumentation_framework.add_attack(a4, a1)
        self.argumentation_framework.add_attack(a5, a4)
        self.argumentation_framework.add_attack(a6, a4)
        self.argumentation_framework.add_attack(a7, a4)
        self.argumentation_framework.add_attack(a7, a5)
        self.argumentation_framework.add_attack(a8, a2)
        self.argumentation_framework.add_attack(a9, a8)
        self.argumentation_framework.add_attack(a9, a6)
        self.argumentation_framework.add_attack(a4, a9)
        self.argumentation_framework.add_attack(a1, a7)
        self.argumentation_framework.add_attack(a2, a7)
        self.argumentation_framework.add_attack(a3, a7)
        self.argumentation_framework.add_attack(a6, a7)
        self.argumentation_framework.add_attack(a5, a9)
        self.argumentation_framework.add_attack(a2, a5)
        self.argumentation_framework.add_attack(a2, a4)



