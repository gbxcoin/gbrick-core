
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Byung Kwon Bae
date_created    : 20180305
date_modified   : 20180706
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from abc import ABCMeta, abstractmethod

from gbrick.base import ObjectManager
from gbrick.blockchain import *
from gbrick import define as Define

class ConsensusBase(metaclass=ABCMeta):

    def __init__(self, blockmanager):
        self._made_block_count = 0
        self._block = None
        self._blockmanager = blockmanager
        self._channel_name = blockmanager.channel_name
        self._blockchain = self._blockmanager.get_blockchain()
        self._txQueue = self._blockmanager.get_tx_queue()
        self._current_vote_block_hash = ""
        self._candidate_blocks = self._blockmanager.get_candidate_blocks()
        self._gen_block()

    @abstractmethod
    def consensus(self):
        pass

    @property
    def block(self):
        return self._block

    @property
    def made_block_count(self):
        return self._made_block_count

    @made_block_count.setter
    def made_block_count(self, value):
        self._made_block_count = value

    def _gen_block(self):
        self._made_block_count += 1
        self._block = Block(channel_name=self._channel_name, made_block_count=self._made_block_count)

    def _stop_gen_block(self):
        self._made_block_count = 0
        self._block = None

    def _makeup_block(self):
        tx_count = 0
        peer_manager_block = None
        while not self._txQueue.empty():
            tx_unloaded = self._txQueue.get()
            tx = pickle.loads(tx_unloaded)

            if isinstance(tx, Transaction):
                # logging.debug("txQueue get tx: " + tx.get_tx_hash())
                tx_count += 1
            else:
                logging.error("Load Transaction Error!")
                continue

            if tx.type is TransactionType.peer_list:
                peer_manager_block = Block(channel_name=self._channel_name)
                peer_manager_block.block_type = BlockType.peer_list
                peer_manager_block.peer_manager = tx.get_data()
                break
            elif self._block is None:
                logging.error("Leader Can't Add tx...")
            else:
                tx_confirmed = self._block.put_transaction(tx)

            if tx_count >= Define.MAX_BLOCK_TX_NUM:
                break

        if self._block is not None and len(self._block.confirmed_transaction_list) > 0:
            block_dump = pickle.dumps(self._block)
            block_dump_size = len(block_dump)

            if block_dump_size > (Define.MAX_BLOCK_KBYTES * 1024):
                divided_block = Block(channel_name=self._channel_name, is_divided_block=True)
                do_divide = False

                next_tx = (self._block.confirmed_transaction_list.pop(0), None)[
                    len(self._block.confirmed_transaction_list) == 0]
                expected_block_size = len(pickle.dumps(divided_block))

                while next_tx is not None:
                    tx_dump = pickle.dumps(next_tx)
                    expected_block_size += len(tx_dump)

                    if expected_block_size < (Define.MAX_BLOCK_KBYTES * 1024):
                        divided_block.put_transaction(next_tx)
                        next_tx = (self._block.confirmed_transaction_list.pop(0), None)[
                            len(self._block.confirmed_transaction_list) == 0]
                        if next_tx is None:
                            do_divide = True
                    else:
                        do_divide = True

                    if do_divide:
                        logging.warning("Block divide, add unconfirmed block to candidate blocks")
                        divided_block.generate_block(self._candidate_blocks.get_last_block(self._blockchain))
                        self._candidate_blocks.add_unconfirmed_block(divided_block)

                        divided_block = Block(channel_name=self._channel_name, is_divided_block=True)
                        expected_block_size = len(pickle.dumps(divided_block))
                        do_divide = False

        if peer_manager_block is not None:
            peer_manager_block.generate_block(self._candidate_blocks.get_last_block(self._blockchain))
            peer_manager_block.sign(ObjectManager().peer_service.auth)

