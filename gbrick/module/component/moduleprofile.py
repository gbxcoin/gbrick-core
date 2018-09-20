'''
name            : gbrick.module.base.moduleprofile
description     : Information of Module
                  id: indendifier
                  name: name
                  address_coinbase: account of node
                  ip: ip address
                  port: port number
author          : Hyungjoo Yee
date_created    : 20180824
date_modified   : 20180824
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
import json
from gbrick.common.crypto.hash import *
from gbrick.define import *


class ModuleProfile:
    def __init__(self, p_dict: dict=None, p_json_str: str=None):
        if p_dict is not None:
            self.from_dict(p_dict)

        elif p_json_str is not None:
            self.from_json_str(p_json_str)

        else:
            self.id = b''
            self.type = ModuleType.NONE
            self.name = ''
            self.ip = '127.0.0.1'
            self.port = '6600'
            self.receiver_thread = 1

    def from_dict(self, p_dict: dict):
        self.id = p_dict.get('id').encode('utf-8')
        self.type = p_dict.get('type')
        self.name = p_dict.get('name')
        self.ip = p_dict.get('ip')
        self.port = p_dict.get('port')
        self.receiver_thread = p_dict.get('receiver_thread')

    def from_json_str(self, p_json_str: str):
        p_dict_obj = json.loads(p_json_str)
        self.from_dict(p_dict=p_dict_obj)

    def to_dict(self):
        result_dict = {'id': self.id.decode('utf-8')
                       , 'type': self.type
                       , 'name': self.name
                       , 'ip': self.ip
                       , 'port': self.port
                       , 'receiver_thread': self.receiver_thread}

        return result_dict

    def to_json_str(self):
        return json.dumps(self.to_dict())

    def to_hash(self):
        return to_gbrick_hash('{0}{1}{2}'.format(self.name, self.ip, self.port))
