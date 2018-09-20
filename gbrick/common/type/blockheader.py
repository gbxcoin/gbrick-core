import json
from .base.blockbase import BlockHeaderBase
from gbrick.common.crypto.hash import *


class BlockHeader(BlockHeaderBase):
    _block_version = 1

    def __init__(self, p_json_str: str=None, p_dict_obj: dict=None):
        self.num_version = BlockHeader._block_version
        self.num_retry_count = 0
        self.hash_candidate_block = b''
        self.hash_vote_root = b''

        if p_json_str is None and p_dict_obj is None:
            BlockHeaderBase.__init__(self)

        elif p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            self.from_dict(json.loads(p_json_str))

    def from_dict(self, p_dict: dict):
        super().from_dict(p_dict)
        self.num_version = p_dict.get('version')
        self.num_retry_count = p_dict.get('retry_count')
        self.hash_candidate_block = p_dict.get('candidate_block_hash').encode('utf-8')
        self.hash_vote_root = p_dict.get('vote_root_hash').encode('utf-8')

    def to_dict(self) -> dict:
        dict_obj = super().to_dict()
        dict_obj.setdefault('version', self.num_version)
        dict_obj.setdefault('retry_count', self.num_retry_count)
        dict_obj.setdefault('candidate_block_hash', self.hash_candidate_block.decode('utf-8'))
        dict_obj.setdefault('vote_root_hash', self.hash_vote_root.decode('utf-8'))
        return dict_obj

    def pre_hash(self):
        att = '{0}{1}{2}{3}{4}'.format(super().pre_hash()
                                       , str(self.num_version)
                                       , str(self.num_retry_count)
                                       , str(self.hash_candidate_block)
                                       , str(self.hash_vote_root))
        return att

    def to_hash(self):
        return to_gbrick_hash(self.pre_hash())

    def pre_candidate_hash(self):
        att = super().pre_hash()
        return att

    def to_candidate_hash(self):
        return to_gbrick_hash(self.pre_candidate_hash())

    def get_key(self):
        if self.hash_block != b'':
            return self.hash_block

        elif self.hash_candidate_block != b'':
            return self.hash_candidate_block

        return None

    def get_wave(self):
        wave = '{0}-{1}'.format(self.num_height, self.num_retry_count)
        return wave
