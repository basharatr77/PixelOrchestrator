from abc import ABC, abstractmethod


class Transport(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self):
        pass

    @abstractmethod
    def execute(self, command):
        pass

    @abstractmethod
    def get_device_info(self):
        pass
