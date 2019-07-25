from culture import Culture
from argument import Argument, ArgumentationFramework
from agent import Agent

class EasyCulture(Culture):
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Easy"
        self.properties = {"rank": 0,
                           "tasked_status": False}



    def create_arguments(self):
        """
        Defines set of arguments present in the culture.
        :return: Set of arguments.
        """

        motion = Argument(0, "You must change your route.")
        motion.set_generator(lambda gen: True)  # Propositional arguments are always valid.

        arg1 = Argument(1, "My rank is higher than yours.")
        def arg1_generator(my: Agent, their: Agent):
            if not (hasattr(my, "rank") and hasattr(their, "rank")):
                print("EasyCulture::arg1_generator: Attribute 'rank' not found.")
                return False
            return my.rank > their.rank
        arg1.set_generator(arg1_generator)

        arg2 = Argument(2, "I am currently performing a task and you are not.")
        def arg2_generator(my: Agent, their: Agent):
            if not (hasattr(my, "tasked_status") and hasattr(their, "tasked_status")):
                print("EasyCulture::arg2_generator: Attribute 'tasked_status' not found.")
                return False
            return my.tasked_status == True and their.tasked_status == False
        arg2.set_generator(arg2_generator)

        self.argumentation_framework.add_arguments([motion, arg1, arg2])

    def define_attacks(self):
        """
        Defines attack relationships present in the culture.
        :return: Attack relationships.
        """
        motion_id = 0
        arg1_id = 1
        arg2_id = 2

        self.argumentation_framework.add_attack(arg1_id, motion_id)
        self.argumentation_framework.add_attack(arg2_id, motion_id)
        self.argumentation_framework.add_attack(arg2_id, arg1_id)



