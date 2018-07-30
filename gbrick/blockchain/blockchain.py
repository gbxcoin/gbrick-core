'''
name            : Gbrick>blockchain.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180202
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import leveldb
import json

from gbrick import utils as util
import gbrick.define as Define
from gbrick.base import ObjectManager
from gbrick.blockchain.block import BlockStatus, Block
from gbrick.utils.exceptions import *
from gbrick.glogic.glogic_base import *
from gbrick.utils import define_code
from gbrick.glogic import GlogicResponse


class Blockchain:

    def __init__(self, blockchain_db=None, channel_name=None):
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL
        self.__block_height = 0
        self.__last_block = None
        self.__channel_name = channel_name

        self.__peer_id = None
        if ObjectManager().peer_service is not None:
            self.__peer_id = ObjectManager().peer_service.peer_id

        self.__confirmed_block_db = blockchain_db


        if self.__confirmed_block_db is None:
            try:
                self.__confirmed_block_db = leveldb.LevelDB(Define.DEFAULT_LEVEL_DB_PATH)
            except leveldb.LevelDBError:
                raise leveldb.LevelDBError("Fail To Create Level DB(path): " + Define.DEFAULT_LEVEL_DB_PATH)

        try:
            last_block_key = self.__confirmed_block_db.Get(Define.BC_LAST_BLOCK_KEY, True)
        except KeyError:
            last_block_key = None
        logging.debug("LAST BLOCK KEY : %s", last_block_key)

        if last_block_key:
            self.__last_block = Block(channel_name=self.__channel_name)
            block_dump = self.__confirmed_block_db.Get(last_block_key)
            self.__last_block.deserialize_block(block_dump)
            logging.debug("restore from last block hash(" + str(self.__last_block.block_hash) + ")")
            logging.debug("restore from last block height(" + str(self.__last_block.height) + ")")
        else:
            self.__add_genesisblock()

        self.__block_height = self.__last_block.height
        self.__made_block_count = 0

    @property
    def block_height(self):
        return self.__block_height

    @property
    def last_block(self):
        return self.__last_block

    @property
    def made_block_count(self):
        return self.__made_block_count

    def increase_made_block_count(self):
        self.__made_block_count += 1

    def reset_made_block_count(self):
        self.__made_block_count = 0

    def rebuild_blocks(self):
        logging.info("re-build blocks from DB....")

        block = Block(channel_name=self.__channel_name)
        prev_block_hash = self.__last_block.block_hash
        total_tx = 0

        while prev_block_hash != "":
            block_dump = self.__confirmed_block_db.Get(prev_block_hash.encode(encoding='UTF-8'))
            block.deserialize_block(block_dump)

            total_tx += block.confirmed_transaction_list.__len__()

            prev_block_hash = block.prev_block_hash

        logging.info("rebuilt blocks, total_tx: " + str(total_tx))
        logging.info("block hash("
                     + self.__last_block.block_hash
                     + ") and height("
                     + str(self.__last_block.height) + ")")

        return total_tx

    def __find_block_by_key(self, key):
        block = Block(channel_name=self.__channel_name)

        try:
            block_bytes = self.__confirmed_block_db.Get(key)
            block.deserialize_block(block_bytes)
        except KeyError:
            block = None

        return block

    def find_block_by_hash(self, block_hash):
        return self.__find_block_by_key(block_hash.encode(encoding='UTF-8'))

    def find_block_by_height(self, block_height):

        key = self.__confirmed_block_db.Get(Define.BC_BLOCK_HEIGHT_KEY +
                                            block_height.to_bytes(Define.BLOCK_HEIGHT_BYTES_LEN, byteorder='big'))
        return self.__find_block_by_key(key)

    def add_block(self, block: Block):

        if block.block_status is not BlockStatus.confirmed:
            raise BlockInValidError("Invalid Block")
        elif self.__last_block is not None and self.__last_block.height > 0:
            if self.__last_block.block_hash != block.prev_block_hash:
                logging.debug("self.last_block.block_hash: " + self.__last_block.block_hash)
                logging.debug("block.prev_block_hash: " + block.prev_block_hash)
                raise BlockError("The last block is different from the hash of the previous block")

        if block.height == 0 or ObjectManager().peer_service is None:
            success_result = {'code': int(define_code.Response.success)}
            invoke_results = self.__create_invoke_result_specific_case(block.confirmed_transaction_list, success_result)
        else:
            try:
                invoke_results = ObjectManager().peer_service.glogic_invoke(block, self.__channel_name)

            except Exception as e:

                glogic_container_exception_result = {'code': GlogicResponse.GLOGIC_CONTAINER_EXCEPTION, 'message': str(e)}
                invoke_results = self.__create_invoke_result_specific_case(block.confirmed_transaction_list
                                                                           , glogic_container_exception_result)

        self.__add_tx_to_block_db(block, invoke_results)

        block_hash_encoded = block.block_hash.encode(encoding='UTF-8')

        batch = leveldb.WriteBatch()
        batch.Put(block_hash_encoded, block.serialize_block())
        batch.Put(Define.BC_LAST_BLOCK_KEY, block_hash_encoded)
        batch.Put(
            Define.BC_BLOCK_HEIGHT_KEY +
            block.height.to_bytes(Define.BLOCK_HEIGHT_BYTES_LEN, byteorder='big'),
            block_hash_encoded)
        self.__confirmed_block_db.Write(batch)

        self.__last_block = block
        self.__block_height = self.__last_block.height

        logging.debug("ADD BLOCK Height : %i", block.height)
        logging.debug("ADD BLOCK Hash : %s", block.block_hash)
        logging.debug("ADD BLOCK MERKLE TREE Hash : %s", block.merkle_tree_root_hash)
        logging.debug("ADD BLOCK Prev Hash : %s ", block.prev_block_hash)

        util.apm_event(self.__peer_id, {
            'event_type': 'AddBlock',
            'peer_id': self.__peer_id,
            'data': {
                'block_height': self.__block_height,
                'block_type': block.block_type.name}})

        return True

    def __create_invoke_result_specific_case(self, confirmed_transaction_list, invoke_result):
        invoke_results = {}
        for tx in confirmed_transaction_list:
            invoke_results[tx.get_tx_hash()] = invoke_result
        return invoke_results

    def __add_tx_to_block_db(self, block, invoke_results):

        logging.debug("try add all tx in block to block db, block hash: " + block.block_hash)

        for tx in block.confirmed_transaction_list:
            tx_hash = tx.get_tx_hash()
            invoke_result = invoke_results[tx_hash]

            tx_info = dict()
            tx_info['block_hash'] = block.block_hash
            tx_info['result'] = invoke_result

            self.__confirmed_block_db.Put(
                tx.get_tx_hash().encode(encoding=Define.HASH_KEY_ENCODING),
                json.dumps(tx_info).encode(encoding=Define.PEER_DATA_ENCODING))

    def find_tx_by_key(self, tx_hash_key):

        try:
            tx_info_json = self.__find_tx_info(tx_hash_key)
        except KeyError as e:

            logging.warning("blockchain::find_tx_by_key KeyError: " + str(e))
            return None
        if tx_info_json is None:
            logging.warning("tx not found")
            return None
        block_key = tx_info_json['block_hash']
        logging.debug("block_key: " + str(block_key))

        block = self.find_block_by_hash(block_key)
        logging.debug("block: " + block.block_hash)
        if block is None:
            logging.error("There is No Block, block_hash: " + block.block_hash)
            return None

        tx_index = block.find_transaction_index(tx_hash_key)
        logging.debug("tx_index: " + str(tx_index))
        if tx_index < 0:
            logging.error("block.find_transaction_index index error, index: " + tx_index)
            return None

        tx = block.confirmed_transaction_list[tx_index]
        logging.debug("find tx: " + tx.get_tx_hash())

        return tx

    def find_invoke_result_by_tx_hash(self, tx_hash):

        try:
            tx_info = self.__find_tx_info(tx_hash)
        except KeyError as e:

            logging.warning("blockchain::find invoke_result KeyError: " + str(e))
            return {'code': GlogicResponse.NOT_INVOKED}

        return tx_info['result']

    def __find_tx_info(self, tx_hash_key):
        try:
            tx_info = self.__confirmed_block_db.Get(
                tx_hash_key.encode(encoding=Define.HASH_KEY_ENCODING))
            tx_info_json = json.loads(tx_info, encoding=Define.PEER_DATA_ENCODING)

        except UnicodeDecodeError as e:
            logging.warning("blockchain::find_tx_by_key UnicodeDecodeError: " + str(e))
            return None

        return tx_info_json

    def __add_genesisblock(self):

        logging.info("Make Genesis Block....")
        block = Block(channel_name=self.__channel_name)
        block.block_status = BlockStatus.confirmed
        block.generate_block()
        self.add_block(block)
        # Genesis block hash : af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc


    def add_unconfirm_block(self, unconfirmed_block):

        logging.debug(f"blockchain:add_unconfirmed_block ({self.__channel_name})")

        if (self.__last_block.height + 1) != unconfirmed_block.height:
            logging.error("The height of the block chain is different.")
            return False, "block_height"
        elif unconfirmed_block.prev_block_hash != self.__last_block.block_hash:
            logging.error("last block hash is different %s vs %s ",
                          unconfirmed_block.prev_block_hash,
                          self.__last_block.block_hash)
            return False, "prev_block_hash"
        elif unconfirmed_block.block_hash != unconfirmed_block.generate_block(self.__last_block):
            logging.error("%s is not same as the generate block hash", unconfirmed_block.block_hash)
            return False, "generate_block_hash"

        # Save unconfirmed_block
        self.__confirmed_block_db.Put(Define.BC_UNCONFIRM_BLOCK_KEY, unconfirmed_block.serialize_block())
        return True, "No reason"

    def confirm_block(self, confirmed_block_hash):

        logging.debug(f"BlockChain:confirm_block channel({self.__channel_name})")

        try:
            unconfirmed_block_byte = self.__confirmed_block_db.Get(Define.BC_UNCONFIRM_BLOCK_KEY)
        except KeyError:
            except_msg = f"there is no unconfirmed block in this peer block_hash({confirmed_block_hash})"
            logging.warning(except_msg)
            raise BlockchainError(except_msg)

        unconfirmed_block = Block(channel_name=self.__channel_name)
        unconfirmed_block.deserialize_block(unconfirmed_block_byte)

        if unconfirmed_block.block_hash != confirmed_block_hash:
            logging.warning("It's not possible to add block while check block hash is fail-")
            raise BlockchainError('The block hash is different from confirm')

        logging.debug("unconfirmed_block.block_hash: " + unconfirmed_block.block_hash)
        logging.debug("confirmed_block_hash: " + confirmed_block_hash)
        logging.debug("unconfirmed_block.prev_block_hash: " + unconfirmed_block.prev_block_hash)

        unconfirmed_block.block_status = BlockStatus.confirmed

        self.add_block(unconfirmed_block)
        self.__confirmed_block_db.Delete(Define.BC_UNCONFIRM_BLOCK_KEY)

        return unconfirmed_block.confirmed_transaction_list.__len__()
    
