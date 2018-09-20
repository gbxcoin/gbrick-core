'''
name            : gbrick.common.type.base.blockbase
description     : Block & Block Header Abstract Class
author          : Hyungjoo Yee
date_created    : 20180801
date_modified   : 20180817
version         : 1.0
python_version  : 3.6.5
Comments        :
'''

from abc import *
from gbrick.common.utils.merkletree import *
from gbrick.common.type.transaction import *


class BlockHeaderBase:
    '''
    p_json_str : initialize block from json string
    p_json_obj : initialize block from dictionary
    '''
    def __init__(self, p_json_str: str=None, p_dict_obj: dict=None):
        self.hash_prev_block = b''
        self.hash_block = b''
        self.num_height = 0
        self.hash_transaction_root = b''
        self.address_creator = b''
        self.byte_signature = b''
        self.timestamp = None

        if p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            dict_json = json.loads(p_json_str)
            self.from_dict(dict_json)

    # change block statedb from dictionary
    def from_dict(self, p_dict: dict):
        self.hash_prev_block = p_dict.get('prev_hash').encode('utf-8')
        self.hash_block = p_dict.get('block_hash').encode('utf-8')
        self.num_height = p_dict.get('height')
        self.hash_transaction_root = p_dict.get('tx_root_hash').encode('utf-8')
        self.address_creator = p_dict.get('creator').encode('utf-8')
        self.byte_signature = p_dict.get('signature').encode('utf-8')

    # create dictionary from Block Object
    def to_dict(self) -> dict:
        dict_obj = {'prev_hash': self.hash_prev_block.decode('utf-8')
                    , 'block_hash': self.hash_block.decode('utf-8')
                    , 'height': self.num_height
                    , 'tx_root_hash': self.hash_transaction_root.decode('utf-8')
                    , 'creator': self.address_creator.decode('utf-8')
                    , 'signature': self.byte_signature.decode('utf-8')}

        return dict_obj

    # create json string from Block Object
    def to_json_str(self):
        return json.dumps(self.to_dict())

    # prepare to call function 'to_hash()'
    def pre_hash(self):
        att = '{0}{1}{2}{3}'.format(self.hash_prev_block
                                    , self.num_height
                                    , self.hash_transaction_root
                                    , self.address_creator)

        return att

    @abstractmethod
    def to_hash(self): raise NotImplementedError

    # implements IHasKey
    @abstractmethod
    def get_key(self): raise NotImplementedError
    @abstractmethod
    def get_wave(self): raise NotImplementedError


class BlockBase:
    def __init__(self, p_json_str: str=None, p_dict_obj: dict=None):
        self.list_transactions = []

        if p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            dict_json = json.loads(p_json_str)
            self.from_dict(dict_json)

    @abstractmethod
    def from_dict(self, p_dict_obj: dict):
        self.header = BlockHeaderBase(p_dict_obj=p_dict_obj.get('header'))
        self.list_transactions = []
        dict_transaction_list = p_dict_obj.get('transaction_list')
        for i in dict_transaction_list:
            t = Transaction(p_dict_obj=i)
            self.list_transactions.append(t)

    def to_dict(self) -> dict:
        list_transaction_dict = []
        for i in self.list_transactions:
            o = i.to_dict()
            list_transaction_dict.append(o)

        dict_obj = {'header': self.header.to_dict()
                    , 'transaction_list': list_transaction_dict}

        return dict_obj

    @abstractmethod
    def to_json_str(self): pass

    @abstractmethod
    def to_hash(self): pass

    def verify_block(self) -> bool:
        # 헤더의 블록해시 값과 계산된 블록해시값이 일치하는지 검사
        if self.to_hash() != self.header.hash_block:
            return False

        return True

    def generate_tx_root_hash(self):
        list_tx_hash = []
        for i in self.list_transactions:
            list_tx_hash.append(i.to_hash())

        return merkleroot(list_tx_hash)

    @abstractmethod
    def get_wave(self):
        return self.header.get_wave()

    @abstractmethod
    def get_key(self):
        return self.header.get_key()

