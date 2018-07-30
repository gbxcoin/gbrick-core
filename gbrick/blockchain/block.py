'''
name            : Gbrick>blockchain.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180201
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import struct
import hashlib
import pickle
from enum import Enum

import gbrick.define as Define
from gbrick import utils as util
from gbrick.base import ObjectManager
from gbrick.blockchain import TransactionStatus, TransactionType, Transaction
from gbrick.utils.exceptions import *
from gbrick.glogic.glogic_base import *


class BlockStatus(Enum):
    unconfirmed = 0
    confirmed = 1

class BlockType(Enum):
    general = 1
    vote = 2
    peer_list = 3
    glogic = 4

class Block:

    def __init__(self, channel_name, made_block_count=0, is_divided_block=False):
        # Block header
        self.version = "0.1a"
        self.prev_block_hash = Define.GENESIS_PREVHASH
        self.prev_block_confirm = False
        self.merkle_tree_root_hash = Define.MERKLE_TREE_ROOTHASH
        self.merkle_tree = []
        self.time_stamp = Define.GENESIS_TIMESTAMP
        self.__channel_name = channel_name

        self.peer_id = ""
        self.__made_block_count = made_block_count
        self.__is_divided_block = is_divided_block
        self.__next_leader_peer_id = ""
        self.__peer_manager = None

        self.confirmed_transaction_list = []
        self.block_hash = ""
        self.height = 0
        self.block_status = BlockStatus.unconfirmed
        self.__block_type = BlockType.general

        self.merkle_tree = []
        self.merkle_tree_root_hash = ""
        self.height = 0
        self.time_stamp = 0
        self.__signature = b''

    @property
    def channel_name(self):
        return self.__channel_name

    @property
    def block_type(self):
        return self.__block_type

    @block_type.setter
    def block_type(self, block_type):
        if block_type is not BlockType.general:
            self.__made_block_count -= 1

        self.__block_type = block_type

    @property
    def made_block_count(self):
        return self.__made_block_count

    @property
    def is_divided_block(self):
        return self.__is_divided_block

    @is_divided_block.setter
    def is_divided_block(self, value):
        self.__is_divided_block = value

    @property
    def signature(self):
        return self.__signature

    @property
    def next_leader_peer(self):
        return self.__next_leader_peer_id

    @next_leader_peer.setter
    def next_leader_peer(self, peer_id):
        self.__next_leader_peer_id = peer_id

    @property
    def peer_manager(self):
        return self.__peer_manager

    @peer_manager.setter
    def peer_manager(self, peer_manager):
        self.__peer_manager = peer_manager


    def put_transaction(self, tx):
        if type(tx) is list:
            result = True
            for t in tx:
                result &= self.put_transaction(t)
            return result
        elif not isinstance(tx, Transaction):
            logging.error("not Transaction Type %s", type(tx))
            return False

        if tx.status == TransactionStatus.unconfirmed:
            # check transaction
            # logging.debug("Transaction Hash %s", tx.get_tx_hash())
            if Transaction.validate(tx):
                tx.status = TransactionStatus.confirmed
            else:
                return False

        if tx not in self.confirmed_transaction_list:
            self.confirmed_transaction_list.append(tx)
        return True

    @staticmethod
    def __calculate_merkle_tree_root_hash(block):

        mt_list = [tx.get_tx_hash() for tx in block.confirmed_transaction_list]
        block.merkle_tree.extend(mt_list)

        while True:
            tree_length = len(mt_list)
            tmp_mt_list = []

            if tree_length <= 1:
                break

            elif tree_length % 2 == 1:
                mt_list.append(mt_list[tree_length-1])
                tree_length += 1

            for row in range(int(tree_length/2)):
                idx = row * 2
                mk_sum = b''.join([mt_list[idx].encode(encoding='UTF-8'), mt_list[idx+1].encode(encoding='UTF-8')])
                mk_hash = hashlib.sha256(mk_sum).hexdigest()
                tmp_mt_list.append(mk_hash)

            mt_list = tmp_mt_list
            block.merkle_tree.extend(mt_list)

        if len(mt_list) == 1:
            block.merkle_tree_root_hash = mt_list[0]

        return block.merkle_tree_root_hash

    def serialize_block(self):

        return pickle.dumps(self, pickle.DEFAULT_PROTOCOL)

    def deserialize_block(self, block_dumps):

        dump_obj = pickle.loads(block_dumps)
        if type(dump_obj) == Block:
            self.__dict__ = dump_obj.__dict__

    def find_transaction_index(self, transaction_hash):
        for idx, tx in enumerate(self.confirmed_transaction_list):
            if tx.get_tx_hash() == transaction_hash:
                return idx
        return -1

    @staticmethod
    def validate(block, tx_queue=None) -> bool:

        mk_hash = Block.__calculate_merkle_tree_root_hash(block)
        if block.height == 0 and len(block.confirmed_transaction_list) == 0:
            return True

        if len(block.confirmed_transaction_list) > 0:

            if mk_hash != block.merkle_tree_root_hash:
                raise BlockInValidError('Merkle Tree Root hash is not same')

        if block.block_hash != Block.__generate_hash(block):
            raise BlockInValidError('block Hash is not same generate hash')

        leader = ObjectManager().peer_service.channel_manager.get_peer_manager(block.__channel_name).get_leader_object()
        if not leader.cert_verifier.verify_hash(block.block_hash, block.signature):
            raise BlockInValidError('block signature invalid')

        if block.time_stamp == 0:
            raise BlockError('block time stamp is 0')

        if len(block.prev_block_hash) == 0:
            raise BlockError('Prev Block Hash not Exist')

        confirmed_tx_list = []
        for tx in block.confirmed_transaction_list:
            if Transaction.validate(tx):
                confirmed_tx_list.append(tx.tx_hash)
            else:
                raise BlockInValidError(f"block ({block.block_hash}) validate fails \n"
                                        f"tx {tx.tx_hash} is invalid")

        if tx_queue is not None:
            block.__tx_validate_with_queue(tx_queue, confirmed_tx_list)

        return True

    def __tx_validate_with_queue(self, tx_queue, confirmed_tx_list):
        remain_tx = []

        while not tx_queue.empty():
            tx_unloaded = tx_queue.get()
            tx = pickle.loads(tx_unloaded)

            if tx.tx_hash not in confirmed_tx_list:

                if tx.type == TransactionType.general:
                    remain_tx.append(tx_unloaded)

        if len(remain_tx) != 0:
            logging.warning(f"after tx validate, remain tx({len(remain_tx)})")

            for tx_unloaded in remain_tx:
                ObjectManager().peer_service.channel_manager.get_block_manager(
                    self.__channel_name).add_tx_unloaded(tx_unloaded)

    def generate_block(self, prev_block=None):

        if prev_block is None:
            self.prev_block_hash = ""
            self.height = 0
            self.time_stamp = 0
        elif self.time_stamp == 0:
            if self.prev_block_hash == "":
                self.prev_block_hash = prev_block.block_hash
                self.height = prev_block.height + 1
            self.time_stamp = util.get_time_stamp()

        if len(self.confirmed_transaction_list) > 0:
            Block.__calculate_merkle_tree_root_hash(self)
        self.block_hash = Block.__generate_hash(self)

        return self.block_hash

    @staticmethod
    def __generate_hash(block):

        block_hash_data = b''.join([block.prev_block_hash.encode(encoding='UTF-8'),
                                    block.merkle_tree_root_hash.encode(encoding='UTF-8'),
                                    struct.pack('Q', block.time_stamp)])
        block_hash = hashlib.sha256(block_hash_data).hexdigest()
        return block_hash

    def mk_merkle_proof(self, index):

        nodes = [tx.get_tx_hash().encode(encoding='UTF-8') for tx in self.confirmed_transaction_list]
        if len(nodes) % 2 and len(nodes) > 2:
            nodes.append(nodes[-1])
        layers = [nodes]

        while len(nodes) > 1:
            new_nodes = []
            for i in range(0, len(nodes) - 1, 2):
                new_nodes.append(
                    hashlib.sha256(b''.join([nodes[i], nodes[i + 1]])).hexdigest().encode(encoding='UTF-8'))
            if len(new_nodes) % 2 and len(new_nodes) > 2:
                new_nodes.append(new_nodes[-1])
            nodes = new_nodes
            layers.append(nodes)

        merkle_siblings = \
            [layers[i][(index >> i) ^ 1] for i in range(len(layers)-1)]

        return {
            "transaction": self.confirmed_transaction_list[index].get_tx_hash(),
            "siblings": [x.decode('utf-8') for x in merkle_siblings],
            "block": self
        }

    @staticmethod
    def merkle_path(block, index):

        header = {}
        proof = block.mk_merkle_proof(index)
        header['merkle_root'] = block.merkle_tree_root_hash
        siblings = proof['siblings']
        logging.debug("SLBLINGS : %s", siblings)
        target_tx = block.confirmed_transaction_list[index].get_tx_hash()
        siblings = [x.encode(encoding='UTF-8') for x in siblings]
        resulthash = target_tx.encode(encoding='UTF-8')

        for i in range(len(siblings)):
            _proof = siblings[i]
            if index % 2 == 1:
                left = _proof
                right = resulthash
            else:
                left = resulthash
                right = _proof
            resulthash = hashlib.sha256(b''.join([left, right])).hexdigest().encode(encoding='UTF-8')
            index = int(index / 2)

        logging.debug('PROOF RESULT: %s , MK ROOT: %s', resulthash, block.merkle_tree_root_hash)

        return resulthash == block.merkle_tree_root_hash.encode(encoding='UTF-8')

    def sign(self, peer_auth):
        self.__signature = peer_auth.sign_data(self.block_hash, is_hash=True)

