'''
name           : Gbrick>blockchain.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180201
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import binascii
import time
import collections
import struct
import hashlib
import logging

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from collections import OrderedDict
from enum import Enum

#from gbrick.blockchain import blockchain
#from gbrick.db import dbWorking
from gbrick import define as Define
from gbrick import utils as util
from gbrick.tools.signature_helper import PublicVerifierContainer

class TransactionStatus(Enum):
    unconfirmed = 1
    confirmed = 2


class TransactionType(Enum):
    general = 1
    peer_list = 2

class Transaction:

    def __init__(self):
        self.__transaction_status = TransactionStatus.unconfirmed
        self.__transaction_type = TransactionType.general
        self.__meta = collections.OrderedDict()  # peer_id, glogic_id, glogic_ver ...
        self.__data = []
        self.__time_stamp = 0
        self.__transaction_hash = ""
        self.__public_key = b""
        self.__signature = b""

    @property
    def tx_hash(self):
        return self.__transaction_hash

    @property
    def status(self):
        return self.__transaction_status

    @status.setter
    def status(self, tx_status):
        self.__transaction_status = tx_status

    @property
    def type(self):
        return self.__transaction_type

    @type.setter
    def type(self, tx_type):
        self.__transaction_type = tx_type

    @property
    def signature(self):
        return self.__signature

    @property
    def public_key(self):
        return self.__public_key

    @property
    def meta(self):
        return self.__meta.copy()

    def put_meta(self, key, value):
        self.__meta[key] = value

    def init_meta(self, peer_id, glogic_id, glogic_ver, channel_name: str):
        self.put_meta(Define.TS_PEER_ID_KEY, peer_id)
        self.put_meta(Define.TS_GLOGIC_ID_KEY, glogic_id)
        self.put_meta(Define.TS_GLOGIC_VERSION_KEY, glogic_ver)
        self.put_meta(Define.TS_CHANNEL_KEY, channel_name)

    def get_data(self):
        return self.__data

    def get_data_string(self):
        return self.__data.decode(Define.PEER_DATA_ENCODING)

    def put_data(self, data, time_stamp=None):

        if isinstance(data, str):
            self.__data = bytearray(data, 'utf-8')
        else:
            self.__data = data

        if time_stamp is None:
            self.__time_stamp = int(time.time()*1000000)
        else:
            self.__time_stamp = time_stamp

        return self.__generate_hash()

    def get_timestamp(self):
        return self.__time_stamp

    def __generate_hash(self):

        _meta_byte = util.dict_to_binary(self.__meta)
        _time_byte = struct.pack('Q', self.__time_stamp)
        _txByte = b''.join([_meta_byte, self.__data, _time_byte])
        self.__transaction_hash = hashlib.sha256(_txByte).hexdigest()

        return self.__transaction_hash


    def get_tx_hash(self):
        return self.__transaction_hash

    @staticmethod
    def generate_transaction_hash(tx):

        _meta_byte = util.dict_to_binary(tx.meta)
        _data_byte = tx.get_data()
        _time_byte = struct.pack('Q', tx.get_timestamp())
        _txByte = b''.join([_meta_byte, _data_byte, _time_byte])
        _txhash = hashlib.sha256(_txByte).hexdigest()

        return _txhash

    def sign_hash(self, peer_authorization) -> bool:

        signature = peer_authorization.sign_data(self.tx_hash, is_hash=True)
        self.__public_key = peer_authorization.get_public_der()

        if signature:
            self.__signature = signature
            return True
        else:
            logging.error(f"sign transaction {self.tx_hash} fail")
            return False

    @staticmethod
    def validate(tx, is_exception_log=True) -> bool:

        try:
            if Transaction.generate_transaction_hash(tx) != tx.get_tx_hash():
                Transaction.__logging_tx_validate("hash validate fail", tx)
                return False

            public_verifier = PublicVerifierContainer.get_public_verifier(tx.public_key)

            if public_verifier.verify_hash(tx.get_tx_hash(), tx.signature):
                return True
            else:
                if is_exception_log:
                    Transaction.__logging_tx_validate("signature validate fail", tx)
                return False

        except Exception as e:
            if is_exception_log:
                Transaction.__logging_tx_validate(str(e), tx)
            return False

    @staticmethod
    def __logging_tx_validate(fail_message, tx):
        logging.error("validate tx fail \ntx hash : " + tx.get_tx_hash() +
                      "\ntx meta : " + str(tx.meta) +
                      "\ntx data : " + str(tx.get_data()) +
                      "\ntx signature : " + str(tx.signature) +
                      "\n cause by : " + fail_message)
