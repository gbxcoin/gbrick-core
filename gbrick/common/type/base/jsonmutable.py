from abc import *


class JsonMutable(metaclass=ABCMeta):
    @abstractmethod
    def to_dict(self): raise NotImplementedError

    @abstractmethod
    def to_json_str(self): raise NotImplementedError

    @abstractmethod
    def from_dict(self, p_dict: dict): raise NotImplementedError