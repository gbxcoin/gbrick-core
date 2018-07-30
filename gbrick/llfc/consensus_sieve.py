
'''
name            : gbrick::consensus_sieve.py
description     : Gbrick Blockchain
author          : Byung Kwon Bae
date_created    : 20180311
date_modified   : 20180717
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from time import sleep

from gbrick.base import ObjectManager
from gbrick.blockchain import *
from gbrick.llfc import candidate_blocks
from gbrick.llfc.consensus_base import ConsensusBase
from gbrick import define as Define

class ConsensusSieve(ConsensusBase):

    def __throw_out_block(self, target_block):

        self._block.prev_block_confirm = False
        self._block.prev_block_hash = target_block.prev_block_hash
        self._block.height = target_block.height
        self._current_vote_block_hash = ""
        
    def consensus(self):

        confirmed_block = None
        try:
            confirmed_block = self._candidate_blocks.get_confirmed_block()
        except candidate_blocks.NoExistBlock as e:
            logging.error(e)
        except candidate_blocks.NotCompleteValidation as e:
            logging.warning(f"This block need more validation vote from Peers block "
                            f"hash({str(e.block.block_hash)}) channel({self._channel_name})")

            self._blockmanager.broadcast_audience_set()

            if util.diff_in_seconds(e.block.time_stamp) > Define.BLOCK_VOTE_TIMEOUT:
                logging.warning("Time Outed Block not confirmed duration: " + str(util.diff_in_seconds(e.block.time_stamp)))

                self._candidate_blocks.remove_broken_block(e.block.block_hash)
            else:
                peer_service = ObjectManager().peer_service
                if peer_service is not None:
                    peer_service.reset_voter_count()

                self._candidate_blocks.reset_voter_count(str(e.block.block_hash))
                time.sleep(Define.INTERVAL_WAIT_PEER_VOTE)
        except candidate_blocks.InvalidatedBlock as e:
            logging.error("InvalidatedBlock!! hash: " + str(e.block.block_hash))
            logging.debug("InvalidatedBlock!! prev_hash: " + str(e.block.prev_block_hash))
            logging.debug("This block status: " + str(self._block.confirmed_transaction_list.__len__()))

            self.__throw_out_block(e.block)

        if confirmed_block is not None:
            logging.info(f"Block Validation is Complete "
                         f"hash({confirmed_block.block_hash}) channel({self._channel_name})")

            self._block.prev_block_confirm = True
            confirmed_block.block_status = BlockStatus.confirmed
            self._blockmanager.add_block(confirmed_block)
            self._current_vote_block_hash = ""

        if self._current_vote_block_hash == "":

            if self._block is not None and self._block.confirmed_transaction_list.__len__() > 0:

                self._block.generate_block(self._candidate_blocks.get_last_block(self._blockchain))
                self._block.sign(ObjectManager().peer_service.auth)
                self._candidate_blocks.add_unconfirmed_block(self._block)

                # logging.warning("blockchain.last_block_hash: " + self._blockchain.last_block.block_hash)
                # logging.warning("block.block_hash: " + self._block.block_hash)
                # logging.warning("block.prev_block_hash: " + self._block.prev_block_hash)

                self._gen_block()
            candidate_block = self._candidate_blocks.get_candidate_block()
            peer_manager = ObjectManager().peer_service.channel_manager.get_peer_manager(self._channel_name)

            if candidate_block is not None:

                self._current_vote_block_hash = candidate_block.block_hash

                logging.info("candidate block hash: " + self._current_vote_block_hash)
                util.logger.spam(f"consensus_siever:consensus try peer_manager.get_next_leader_peer().peer_id")

                candidate_block.next_leader_peer = peer_manager.get_next_leader_peer().peer_id
                self._blockmanager.broadcast_send_unconfirmed_block(candidate_block)

                return
            elif self._block is not None and \
                    (self._block.prev_block_confirm is True) and \
                    (self._block.confirmed_transaction_list.__len__() == 0):

                self._block.prev_block_hash = confirmed_block.block_hash
                self._block.block_type = BlockType.vote
                self.made_block_count -= 1

                logging.debug(f"made_block_count({self.made_block_count})")

                self._block.next_leader_peer = peer_manager.get_next_leader_peer().peer_id
                self._blockmanager.broadcast_send_unconfirmed_block(self._block)

                if self.made_block_count < Define.LEADER_BLOCK_CREATION_LIMIT:  # or not self._txQueue.empty():
                    self._gen_block()
                else:
                    self._stop_gen_block()
                    util.logger.spam(f"consensus_siever:consensus channel({self._channel_name}) "
                                     f"\ntry ObjectManager().peer_service.rotate_next_leader(self._channel_name)")
                    ObjectManager().peer_service.rotate_next_leader(self._channel_name)

        self._makeup_block()

        sleep(Define.SLEEP_SECONDS_IN_SERVICE_LOOP)
