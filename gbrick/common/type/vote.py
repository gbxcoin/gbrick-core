import json
from gbrick.common.crypto.hash import *


class Vote:
    _num_version = 1

    def __init__(self, p_json_str: str=None, p_dict_obj: dict=None):
        self.num_version = Vote._num_version
        self.hash_vote = b''
        self.num_block_height = 0
        self.num_retry_count = 0
        self.hash_candidate_block = b''
        self.address_creator = b''
        self.byte_signature = b''
        self.timestamp = None

        if p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            self.from_dict(json.loads(p_json_str))

    def from_dict(self, p_dict: dict):
        self.num_version = p_dict.get('version')
        self.hash_vote = p_dict.get('vote_hash').encode('utf-8')
        self.num_block_height = p_dict.get('block_height')
        self.num_retry_count = p_dict.get('retry_count')
        self.hash_candidate_block = p_dict.get('candidate_block_hash').encode('utf-8')
        self.address_creator = p_dict.get('creator').encode('utf-8')
        self.byte_signature = p_dict.get('signature').encode('utf-8')

    def to_dict(self):
        json_obj = {'version': self.num_version
                    , 'vote_hash': self.hash_vote.decode('utf-8')
                    , 'block_height': self.num_block_height
                    , 'retry_count' : self.num_retry_count
                    , 'candidate_block_hash': self.hash_candidate_block.decode('utf-8')
                    , 'creator': self.address_creator.decode('utf-8')
                    , 'signature': self.byte_signature.decode('utf-8')}

        return json_obj

    def to_json_str(self):
        return json.dumps(self.to_dict())

    def to_hash(self):
        att = '{0}{1}{2}{3}'.format(self.num_version
                                    , self.num_block_height
                                    , self.hash_candidate_block
                                    , self.address_creator)

        return to_gbrick_hash(att)

    def get_key(self):
        return self.hash_vote

    def get_wave(self):
        return '{0}-{1}'.format(self.num_block_height, self.num_retry_count)

