import json
import time
from gbrick.define import *
from gbrick.common.crypto.gcrypto import *
from gbrick.common.crypto.hash import *



class Transaction:
    _num_version = 1

    def __init__(self, p_json_str: str=None, p_dict_obj: dict=None):
        self.num_version = Transaction._num_version
        self.hash_transaction = b''
        self.enum_transaction_type = TransactionType.TRANSFER
        self.num_account_nonce = 0
        self.address_sender = b''
        self.address_recipient = b''
        self.amount_value = 0
        self.amount_fee = 0
        self.message = ''
        self.byte_signature = b''
        self.timestamp = time.time()

        if p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            dict_json = json.loads(p_json_str)
            self.from_dict(dict_json)

    def from_dict(self, p_dict: dict):
        self.num_version = p_dict.get('version')
        self.hash_transaction = p_dict.get('tx_hash').encode('utf-8')
        self.enum_transaction_type = p_dict.get('type')
        self.num_account_nonce = p_dict.get('nonce')
        self.address_sender = p_dict.get('from').encode('utf-8')
        self.address_recipient = p_dict.get('to').encode('utf-8')
        self.amount_value = p_dict.get('value')
        self.amount_fee = p_dict.get('fee')
        self.message = p_dict.get('message')
        self.byte_signature = p_dict.get('signature').encode('utf-8')
        self.timestamp = p_dict.get('timestamp')

    def to_dict(self):
        dict_obj = {'version': self.num_version
                    , 'tx_hash': self.hash_transaction.decode('utf-8')
                    , 'type': self.enum_transaction_type
                    , 'nonce': self.num_account_nonce
                    , 'from': self.address_sender.decode('utf-8')
                    , 'to': self.address_recipient.decode('utf-8')
                    , 'value': self.amount_value
                    , 'fee': self.amount_fee
                    , 'message': self.message
                    , 'signature': self.byte_signature.decode('utf-8')
                    , 'timestamp': self.timestamp}

        return dict_obj

    def to_json_str(self):
        return json.dumps(self.to_dict())

    def to_hash(self):
        att = '{0}{1}{2}{3}{4}{5}{6}{7}{8}'.format(self.num_version
                                                , self.enum_transaction_type
                                                , self.num_account_nonce
                                                , self.address_sender
                                                , self.address_recipient
                                                , self.amount_value
                                                , self.amount_fee
                                                , self.message
                                                , self.timestamp
                                                )

        return to_gbrick_hash(att)

    def create_signature(self, private_key_path=None, msg_hash=None):
        if private_key_path is None:
            raise ValueError("private key is {}".format(private_key_path))
        if msg_hash is None:
            signature = signing(self.hash_transaction, private_key_path)
        elif msg_hash:
            signature = signing(msg_hash, private_key_path)
        self.byte_signature = signature

    def get_key(self):
        return self.hash_transaction

'''
[
    {
        "transaction_id" : "aslfg04ndowf0-3hs0gwf9ha0w9s2309whfsofb320842w"
        "transaction_type" : 1
        "account_nonce" : 0
        "sender" : ""
        "actions : 
            [
                {
                    "user_nonce" : None
                    "user_id" : 지갑주소 값 ?
                }
            ]
        "signature" : None
    }
]
'''

