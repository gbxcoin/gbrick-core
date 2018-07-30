
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180205
date_modified   : 20180706
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import queue
import shutil

from time import sleep

from gbrick.base import CommonThread, ObjectManager
from gbrick.blockchain import *
from gbrick.utils import *
from gbrick import define as Define
from gbrick.llfc.candidate_blocks import CandidateBlocks
from gbrick.llfc.consensus_llfc import ConsensusLLFC
from gbrick.llfc.consensus_sieve import ConsensusSieve
from gbrick.protos import gbrick_pb2_grpc

# gbrick_pb2 not import pickle error
import gbrick_pb2

class BlockManager(CommonThread):

    def __init__(self, common_service, peer_id, channel_name, level_db_identity):
        self.__channel_name = channel_name
        self.__level_db = None
        self.__level_db_path = ""
        self.__level_db, self.__level_db_path = util.init_level_db(f"{level_db_identity}_{channel_name}")
        self.__txQueue = queue.Queue()
        self.__unconfirmedBlockQueue = queue.Queue()
        self.__candidate_blocks = None
        if ObjectManager().peer_service is not None:
            self.__candidate_blocks = CandidateBlocks(ObjectManager().peer_service.peer_id, channel_name)
        self.__common_service = common_service
        self.__blockchain = Blockchain(self.__level_db, channel_name)
        self.__total_tx = self.__blockchain.rebuild_blocks()
        self.__peer_type = None
        self.__block_type = BlockType.general
        self.__consensus = None
        self.__run_logic = None
        self.__block_height_sync_lock = False
        self.set_peer_type(gbrick_pb2.PEER)

    @property
    def channel_name(self):
        return self.__channel_name

    @property
    def peer_type(self):
        return self.__peer_type

    @property
    def consensus(self):
        return self.__consensus

    @property
    def block_type(self):
        return self.__block_type

    @block_type.setter
    def block_type(self, block_type):
        self.__block_type = block_type

    def get_level_db(self):
        return self.__level_db

    def clear_all_blocks(self):
        logging.debug(f"clear level db({self.__level_db_path})")
        shutil.rmtree(self.__level_db_path)

    def set_peer_type(self, peer_type):
        self.__peer_type = peer_type

        #llfc & sieve
        if self.__peer_type == gbrick_pb2.BLOCK_GENERATOR:
            if Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.llfc:
                self.__consensus = ConsensusLLFC(self)
            elif Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.sieve:
               self.__consensus = ConsensusSieve(self)

            self.__run_logic = self.__consensus.consensus
        else:
            self.__run_logic = self.__do_vote

    def get_total_tx(self):

        return self.__total_tx

    def get_blockchain(self):
        return self.__blockchain

    def get_candidate_blocks(self):
        return self.__candidate_blocks

    def broadcast_getstatus(self):

        logging.info("BroadCast GetStatus....")
        if self.__common_service is not None:
            self.__common_service.broadcast("GetStatus",
                                            (gbrick_pb2.StatusRequest(request="BlockGenerator BroadCast")))

    def broadcast_send_unconfirmed_block(self, block):

        logging.debug("BroadCast AnnounceUnconfirmedBlock...peers: " +
                      str(ObjectManager().peer_service.channel_manager.get_peer_manager(
                          self.__channel_name).get_peer_count()))

        dump = pickle.dumps(block)
        if len(block.confirmed_transaction_list) > 0:
            self.__blockchain.increase_made_block_count()
        if self.__common_service is not None:
            self.__common_service.broadcast("AnnounceUnconfirmedBlock",
                                            (gbrick_pb2.BlockSend(
                                                block=dump,
                                                channel=self.__channel_name)))

    def broadcast_announce_confirmed_block(self, block_hash, block=None):

        logging.info("BroadCast AnnounceConfirmedBlock....")
        if self.__common_service is not None:
            if block is not None:
                dump = pickle.dumps(block)
                self.__common_service.broadcast("AnnounceConfirmedBlock",
                                                (gbrick_pb2.BlockAnnounce(
                                                    block_hash=block_hash,
                                                    channel=self.__channel_name,
                                                    block=dump)))
            else:
                self.__common_service.broadcast("AnnounceConfirmedBlock",
                                                (gbrick_pb2.BlockAnnounce(
                                                    block_hash=block_hash,
                                                    channel=self.__channel_name)))

    def broadcast_audience_set(self):
        """Check Broadcast Audience and Return Status

        """
        self.__common_service.broadcast_audience_set()

    def add_tx(self, tx):
        """
        :param tx: transaction object
        """
        tx_unloaded = pickle.dumps(tx)
        self.__txQueue.put(tx_unloaded)

    def add_tx_unloaded(self, tx):
        """
        :param tx: transaction object
        """
        self.__txQueue.put(tx)

    def get_tx(self, tx_hash):

        return self.__blockchain.find_tx_by_key(tx_hash)

    def get_invoke_result(self, tx_hash):
        """ get invoke result by tx

        :param tx_hash:
        :return:
        """
        return self.__blockchain.find_invoke_result_by_tx_hash(tx_hash)

    def get_tx_queue(self):
        return self.__txQueue

    def get_count_of_unconfirmed_tx(self):

        return self.__txQueue.qsize()

    def confirm_block(self, block_hash):
        try:
            self.__total_tx += self.__blockchain.confirm_block(block_hash)
        except BlockchainError as e:
            logging.warning("BlockchainError, retry block_height_sync")
            self.block_height_sync()

    def add_unconfirmed_block(self, unconfirmed_block):
        # sieve
        if Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.sieve:
            if unconfirmed_block.prev_block_confirm:
                # logging.debug(f"block confirm by sieve: "
                #               f"hash({unconfirmed_block.prev_block_hash}) "
                #               f"block.channel({unconfirmed_block.channel_name})")

                self.confirm_block(unconfirmed_block.prev_block_hash)
            elif unconfirmed_block.block_type is BlockType.peer_list:
                logging.debug(f"peer manager block confirm by sieve: "
                              f"hash({unconfirmed_block.block_hash}) block.channel({unconfirmed_block.channel_name})")
                self.confirm_block(unconfirmed_block.block_hash)
            else:

                pass
        # elif Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.llfc:
        #     if unconfirmed_block.prev_block_confirm:
        #
        #         # turn off previous vote's timer when a general peer received new block for vote
        #         ObjectManager().peer_service.timer_service.stop_timer(unconfirmed_block.prev_block_hash)
        #         # logging.debug(f"block confirm by lft: "
        #         #               f"hash({unconfirmed_block.prev_block_hash}) "
        #         #               f"block.channel({unconfirmed_block.channel_name})")
        #
        #         self.confirm_block(unconfirmed_block.prev_block_hash)
        #     elif unconfirmed_block.block_type is BlockType.peer_list:
        #         logging.debug(f"peer manager block confirm by lft: "
        #                       f"hash({unconfirmed_block.block_hash}) block.channel({unconfirmed_block.channel_name})")
        #         self.confirm_block(unconfirmed_block.block_hash)
        #     else:

        #         pass

        self.__unconfirmedBlockQueue.put(unconfirmed_block)

    def add_block(self, block):
        self.__total_tx += block.confirmed_transaction_list.__len__()
        self.__blockchain.add_block(block)

    def block_height_sync(self, target_peer_stub=None):
        """block height sync with other peers
        """

        if self.__block_height_sync_lock is True:

            logging.warning("block height sync is already running...")
            return

        peer_target = ObjectManager().peer_service.peer_target
        peer_manager = ObjectManager().peer_service.channel_manager.get_peer_manager(self.__channel_name)
        block_manager = ObjectManager().peer_service.channel_manager.get_block_manager(self.__channel_name)

        self.__block_height_sync_lock = True
        if target_peer_stub is None:
            target_peer_stub = peer_manager.get_leader_stub_manager()

        ### Love&Hate Algorithm ###
        logging.info("try block height sync...with love&hate")

        # Make Peer Stub List [peer_stub, ...] and get max_height of network
        max_height = 0
        peer_stubs = []
        target_list = list(peer_manager.get_IP_of_peers_in_group())
        for peer_target_each in target_list:
            target = ":".join(peer_target_each.split(":")[1:])
            if target != peer_target:
                logging.debug(f"try to target({target})")
                channel = grpc.insecure_channel(target)
                stub = gbrick_pb2_grpc.PeerServiceStub(channel)
                try:
                    response = stub.GetStatus(gbrick_pb2.StatusRequest(
                        request="",
                        channel=self.__channel_name
                    ))
                    if response.block_height > max_height:
                        # Add peer as higher than this
                        max_height = response.block_height
                        peer_stubs.append(stub)
                except Exception as e:
                    logging.warning("Already bad.... I don't love you" + str(e))

        if len(peer_stubs) == 0:
            util.logger.warning(f"peer_service:block_height_sync there is no other peer to height sync!")
            self.__block_height_sync_lock = False
            return

        my_height = block_manager.get_blockchain().block_height

        if max_height > my_height:  # if my_height is bigger than max_height TODO
            logging.info(f"You need block height sync to: {max_height} yours: {my_height}")

            preload_blocks = {}  # height : block dictionary

            response = target_peer_stub.call(
                "GetLastBlockHash",
                gbrick_pb2.StatusRequest(request="", channel=self.__channel_name)
            )
            logging.debug(response)
            request_hash = response.block_hash

            max_try = max_height - my_height
            while block_manager.get_blockchain().last_block.block_hash \
                    != request_hash and max_try > 0:

                for peer_stub in peer_stubs:
                    response = None
                    try:
                        response = peer_stub.BlockSync(gbrick_pb2.BlockSyncRequest(
                            block_hash=request_hash,
                            channel=self.__channel_name
                        ), Define.GRPC_TIMEOUT)
                    except Exception as e:
                        logging.warning("There is a bad peer, I hate you: " + str(e))

                    if response is not None and response.response_code == define_code.Response.success:
                        util.logger.spam(f"response block_height({response.block_height})")
                        dump = response.block
                        block = pickle.loads(dump)

                        request_hash = block.prev_block_hash

                        # add block to preload_blocks
                        logging.debug("Add preload_blocks Height: " + str(block.height))
                        preload_blocks[block.height] = block

                        if response.max_block_height > max_height:
                            max_height = response.max_block_height

                        if (my_height + 1) == block.height:
                            max_try = 0
                            logging.info("Block Height Sync Complete.")
                            break
                        max_try -= 1
                    else:
                        peer_stubs.remove(peer_stub)
                        logging.warning("Make this peer to bad (error above or no response): " + str(peer_stub))

            if preload_blocks.__len__() > 0:
                while my_height < max_height:
                    add_height = my_height + 1
                    logging.debug("try add block height: " + str(add_height))
                    try:
                        block_manager.add_block(preload_blocks[add_height])
                        my_height = add_height
                    except KeyError as e:
                        logging.error("fail block height sync: " + str(e))
                        break
                    except exceptions.BlockError as e:
                        logging.error("Block Error Clear all block and restart peer.")
                        block_manager.clear_all_blocks()
                        util.exit_and_msg("Block Error Clear all block and restart peer.")

            if my_height < max_height:
                # block height sync retry
                logging.warning("fail block height sync in one time... try again...")
                self.__block_height_sync_lock = False
                self.block_height_sync(target_peer_stub)

        self.__block_height_sync_lock = False

    def run(self):

        logging.info(f"channel({self.__channel_name}) Block Manager thread Start.")

        while self.is_run():
            self.__run_logic()

        logging.info(f"channel({self.__channel_name}) Block Manager thread Ended.")

    def __do_vote(self):
        if not self.__unconfirmedBlockQueue.empty():
            unconfirmed_block = self.__unconfirmedBlockQueue.get()
            logging.debug("we got unconfirmed block ....")
        else:
            sleep(Define.SLEEP_SECONDS_IN_SERVICE_LOOP)
            # logging.debug("No unconfirmed block ....")
            return

        logging.info("PeerService received unconfirmed block: " + unconfirmed_block.block_hash)

        if unconfirmed_block.confirmed_transaction_list.__len__() == 0 and \
                unconfirmed_block.block_type is not BlockType.peer_list:
            # logging.warning("This is vote block by siever")
            pass
        else:
            # block validate
            block_is_validated = False
            try:
                block_is_validated = Block.validate(unconfirmed_block, self.__txQueue)
            except Exception as e:
                logging.error(e)

            if block_is_validated:
                confirmed, reason = self.__blockchain.add_unconfirm_block(unconfirmed_block)
                if confirmed:
                    # block is confirmed
                    pass
                elif reason == "block_height":
                    self.block_height_sync()

            self.__common_service.vote_unconfirmed_block(
                unconfirmed_block.block_hash, block_is_validated, self.__channel_name)

            # if Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.llfc:
            #     # turn on timer when peer type is general after vote
            #     # TODO: set appropriate callback function and parameters
            #     timer = Timer(
            #         unconfirmed_block.block_hash,
            #         Define.TIMEOUT_FOR_PEER_VOTE,
            #         ObjectManager().peer_service.timer_test_callback_function,
            #         ["test after vote by block_manager"]
            #     )
            #     ObjectManager().peer_service.timer_service.add_timer(unconfirmed_block.block_hash, timer)
