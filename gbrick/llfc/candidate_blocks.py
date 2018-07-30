'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Byung Kwon Bae
date_created    : 20180301
date_modified   : 20180705
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import collections
import logging

from gbrick import utils as util
from gbrick import define as Define
from gbrick.base import ObjectManager
from gbrick.llfc.vote import Vote


class NoExistBlock(Exception):

    pass


class NotCompleteValidation(Exception):

    def __init__(self, message, block=None):
        self.message = message
        self.block = block


class InvalidatedBlock(Exception):

    def __init__(self, message, block=None):
        self.message = message
        self.block = block


class CandidateBlocks:

    def __init__(self, peer_id, channel_name):

        self.__peer_id = peer_id
        self.__channel_name = channel_name
        self.__unconfirmed_blocks = collections.OrderedDict()  # $block_hash : [$vote, $block], ...  Ordered Dictionary
        self.__candidate_last_block = None

    def add_unconfirmed_block(self, block):

        logging.debug(f"CandidateBlocks:add_unconfirmed_block ({self.__channel_name})")
        block.peer_id = self.__peer_id

        vote = Vote(block.block_hash,
                    ObjectManager().peer_service.channel_manager.get_peer_manager(self.__channel_name))
        vote.add_vote(ObjectManager().peer_service.group_id, ObjectManager().peer_service.peer_id, None)

        self.__unconfirmed_blocks[block.block_hash] = [vote, block]
        self.__candidate_last_block = block
        return block.block_hash

    def reset_voter_count(self, block_hash):
        logging.debug(f"({self.__channel_name}) Reset voter count in candidate blocks")
        vote = Vote(block_hash, ObjectManager().peer_service.channel_manager.get_peer_manager(self.__channel_name))
        prev_vote, block = self.__unconfirmed_blocks[block_hash]
        vote.set_vote_with_prev_vote(prev_vote)
        self.__unconfirmed_blocks[block_hash] = [vote, block]


    def get_last_block(self, blockchain=None):
        if self.__candidate_last_block is not None:
            return self.__candidate_last_block

        if blockchain is not None:
            return blockchain.last_block

        return None

    def set_last_block(self, block):
         self.__candidate_last_block = block

    def vote_to_block(self, block_hash, is_validate, peer_id, group_id):

        if block_hash in self.__unconfirmed_blocks.keys():
            self.__unconfirmed_blocks[block_hash][0].add_vote(group_id, peer_id,
                                                              (Define.TEST_FAIL_VOTE_SIGN, None)[is_validate])

    def remove_broken_block(self, block_hash):

        return self.__unconfirmed_blocks.pop(block_hash)[1]

    def get_confirmed_block(self, block_hash=None):

        if block_hash is None:
            candidate_block = self.get_candidate_block()
            if candidate_block is None:
                return None
            block_hash = candidate_block.block_hash

        if block_hash not in self.__unconfirmed_blocks.keys():
            util.apm_event(self.__peer_id, {
                'event_type': 'NoExistBlock',
                'peer_id': self.__peer_id,
                'data': {
                    'message': 'No Exist block in candidate blocks by hash',
                    'block_hash': block_hash}})
            raise NoExistBlock("No Exist block in candidate blocks by hash: " + block_hash)

        if self.__unconfirmed_blocks[block_hash][0].get_result(block_hash, Define.VOTING_RATIO):
            logging.info("Confirmed block pop from candidate blocks hash: " + block_hash)
            return self.__unconfirmed_blocks.pop(block_hash)[1]
        else:
            if self.__unconfirmed_blocks[block_hash][0].is_failed_vote(block_hash, Define.VOTING_RATIO):
                logging.warning("This block fail to validate!!")
                self.remove_broken_block(block_hash)
                util.apm_event(self.__peer_id, {
                    'event_type': 'InvalidatedBlock',
                    'peer_id': self.__peer_id,
                    'data': {
                        'message': 'This block fail to validate',
                        'block_hash': candidate_block.block_hash}})
                raise InvalidatedBlock("This block fail to validate", candidate_block)
            else:
                logging.warning("There is Not Complete Validation.")
                util.apm_event(self.__peer_id, {
                    'event_type': 'NotCompleteValidation',
                    'peer_id': self.__peer_id,
                    'data': {
                        'message': 'There is Not Complete Validation.',
                        'block_hash': candidate_block.block_hash}})
                raise NotCompleteValidation("Not Complete Validation", candidate_block)

    def get_candidate_block(self):

        if self.__unconfirmed_blocks.__len__() > 0:
            return list(self.__unconfirmed_blocks.items())[0][1][1]

        return None

    def is_remain_blocks(self):
        return self.__unconfirmed_blocks.__len__() > 0
