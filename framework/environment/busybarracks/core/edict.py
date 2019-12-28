class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Broadcaster():

    def __init__(self):
        self.__subscriptions = {}

    def subscribe(self, topic, callable):
        if self.__subscriptions.get(topic, None) is None:
            self.__subscriptions[topic] = []
        self.__subscriptions[topic].append(callable)

    def publish(self, topic, *args):
        if self.__subscriptions.get(topic, None) is None:
            return
        for callable in self.__subscriptions[topic]:
            callable(*args)
