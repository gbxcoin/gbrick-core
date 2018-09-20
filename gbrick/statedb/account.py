'''
name            : gbrick.statedb.account
description     : Account State Data Object (EOA, GLogic, etc..)
author          : Hyungjoo Yee
date_created    : 20180905
date_modified   : 20180905
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
import json
from gbrick.define import *
from gbrick.common.type.base.jsonmutable import *


class Account(JsonMutable):
    def __init__(self, p_dict: dict=None, p_json_str: str=None):
        self.address_account = b''
        self.version = 0
        self.type = AccountType.EOA
        self.balance = 0
        self.nonce = 0
        self.state = {}

        if p_dict is not None:
            self.from_dict(p_dict)

        elif p_json_str is not None:
            self.from_dict(json.loads(p_json_str))

    def to_dict(self):
        dict_obj = {'address': self.address_account.decode('utf-8'),
                    'version': self.version,
                    'type': self.type,
                    'balance': self.balance,
                    'nonce': self.nonce,
                    'state': self.state}
        return dict_obj

    def to_json_str(self):
        return json.dumps(self.to_dict())

    def from_dict(self, p_dict: dict):
        self.address_account = p_dict.get('address').encode('utf-8')
        self.version = p_dict.get('version')
        self.type = p_dict.get('type')
        self.balance = p_dict.get('balance')
        self.nonce = p_dict.get('nonce')
        self.state = p_dict.get('state')




