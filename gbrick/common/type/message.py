import json


class Message:

    def __init__(self, p_dict: dict=None, p_json_str: str=None):
        self.to = None
        self.type = None
        self.data = None

        if p_dict is not None:
            self.from_dict(p_dict)

        elif p_json_str is not None:
            self.from_json_str(p_json_str)

    def from_dict(self, p_dict):
        self.to = p_dict.get('to')
        self.type = p_dict.get('type')
        self.data = p_dict.get('data')

    def to_dict(self):
        dict_obj = {'to': self.to,
                    'type': self.type,
                    'data': self.data}

        return dict_obj

    def from_json_str(self, p_json_str):
        dict_obj = json.loads(p_json_str)
        self.from_dict(dict_obj)

    def to_json_str(self):
        return json.dumps(self.to_dict())



