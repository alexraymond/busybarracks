from enum import Enum
from argument import Argument

class ActType(Enum):
    INFORM = 1
    ASK = 2
    ARGUE = 3
    CONCEDE = 4


class ContentType(Enum):
    NONE = 0
    OBSTACLE = 1
    WAYPOINTS = 2
    OWN_LOCATION = 3
    ANOTHER_AGENT = 4
    ARGUMENT = 5
    MULTIPLE_ARGUMENTS = 6

class Locution:
    def __init__(self, act_type, content_type, **kwargs):
        self.__act_type = act_type
        self.__content_type = content_type
        self.__content = kwargs

    def act_type(self):
        return self.__act_type

    def content_type(self):
        return self.__content_type

    def content(self):
        return self.__content

    def set_content(self, content):
        self.content = content

