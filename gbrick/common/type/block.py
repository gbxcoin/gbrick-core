import os
from gbrick.common.type.base.blockbase import BlockBase
from gbrick.common.type.blockheader import BlockHeader
from gbrick.common.utils.merkletree import *
from gbrick.common.type.vote import Vote
from gbrick.common.type.transaction import *
from gbrick.property import *


class Block(BlockBase):
    def __init__(self, p_json_str: str=None, p_dict_obj: dict=None):
        if p_json_str is None and p_dict_obj is None:
            BlockBase.__init__(self)
            self.header = BlockHeader()
            self.list_vote = []

        elif p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            self.from_dict(json.loads(p_json_str))

    def from_dict(self, p_dict: dict):
        self.header = BlockHeader(p_dict_obj=p_dict.get('header'))

        self.list_transactions = []
        dict_transaction_list = p_dict.get('transaction_list')
        for i in dict_transaction_list:
            t = Transaction(p_dict_obj=i)
            self.list_transactions.append(t)

        self.list_vote = []
        dict_vote_list = p_dict.get('vote_list')
        for i in dict_vote_list:
            v = Vote(p_dict_obj=i)
            self.list_vote.append(v)

    def to_dict(self):
        dict_obj = super().to_dict()

        dict_vote_list = []
        for i in self.list_vote:
            o = i.to_dict()
            dict_vote_list.append(o)

        dict_obj.__setitem__('vote_list', dict_vote_list)

        return dict_obj

    def to_json_str(self):
        dict_obj = self.to_dict()
        return json.dumps(dict_obj)

    def add_vote(self, p_vote: Vote):
        self.list_vote.append(p_vote)
        self.header.hash_vote_root = None

    def add_votes(self, p_vote_list: list):
        self.list_vote.extend(p_vote_list)
        self.header.hash_vote_root = None

    def add_transactions(self, p_tx_list: list):
        self.list_transactions.extend(p_tx_list)
        self.header.hash_transaction_root = None

    def to_hash(self):
        return self.header.to_hash()

    def to_candidate_hash(self):
        return to_gbrick_hash(self.header.pre_candidate_hash())

    def generate_vote_root_hash(self):
        list_vote_hash = []
        for i in self.list_vote:
            list_vote_hash.append(i.to_hash())

        return merkleroot(list_vote_hash)

    # implements IHasKe
    def get_key(self):
        return self.header.hash_candidate_block


if __name__ == '__main__':
    if not os.path.isdir(PROFILE_PATH):
        os.mkdir(PROFILE_PATH)

    f = open('{0}/{1}'.format(PROFILE_PATH, 'gbrick_genesis.block'), 'w')
    b = Block()
    b.header.hash_block = b.to_hash()
    f.write(b.to_json_str())
    f.close()