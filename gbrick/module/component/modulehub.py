from abc import *
from gbrick.common.type.message import *


class IModule(metaclass=ABCMeta):
    @abstractmethod
    def set_hub(self, hub): raise NotImplementedError()

    @abstractmethod
    def push(self, message: Message): raise NotImplementedError()


class ModuleHub:
    def __init__(self):
        self.dict_module = {}

    def set_module(self, module_type, module: IModule):
        self.dict_module.__setitem__(module_type, module)

    def push(self, message: Message):
        self.dict_module.get(message.to).push(message)

'''
class ModuleHub:
    def __init__(self, sender_id: bytes=None):
        if sender_id is None:
            sender_id = b'x'
        self.sender_id = sender_id
        self.profile = GbrickProfile()
        self.profile.loads(PROFILE_PATH)

        self.dict_sender = {}

    def send_message(self, message: Message):
        json_message = message.to_json_str()
        sender: Sender = self.dict_sender.get(message.to)
        if sender is None:
            print('[ERROR] ModuleHub::send_message: Module Sender is None ModuleType: {0}'.format(message.to))
            print(self.dict_sender)
        response = sender.send(json_message)
        return response

    def push_message(self, message: Message):
        json_message = message.to_json_str()
        sender: Sender = self.dict_sender.get(message.to)
        sender.push(json_message)

    def set_module_sender(self, module_type, ip, port):
        sender = Sender(ip, port, module_type)
        self.dict_sender.__setitem__(module_type, sender)

    def set_module_sender_as_profile(self, profile: ModuleProfile):
        sender = Sender(profile.ip, profile.port, profile.id)
        self.dict_sender.__setitem__(profile.type, sender)
'''