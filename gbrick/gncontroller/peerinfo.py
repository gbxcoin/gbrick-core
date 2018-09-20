import json
from gbrick.define import *


class PeerInfo:
    def __init__(self, p_dict: dict=None, p_json_str: str=None):
        self.ip = ''
        self.port = ''
        self.id = b''
        self.type = NodeType.NORMAL

        if p_dict is not None:
            self.from_dict(p_dict=p_dict)

        elif p_json_str is not None:
            dict_obj = json.loads(p_json_str)
            self.from_dict(p_dict=dict_obj)

    def to_dict(self):
        dict_result = {'ip': self.ip
                       , 'port': self.port
                       , 'id': self.id.decode('utf-8')
                       , 'type': self.type}
        return dict_result

    def to_json_str(self):
        return json.dumps(self.to_dict())

    def from_dict(self, p_dict: dict):
        self.ip = p_dict.get('ip')
        self.port = p_dict.get('port')
        self.id = p_dict.get('id').encode('utf-8')
        self.type = p_dict.get('type')
