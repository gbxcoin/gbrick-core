'''
name            : gbrick.statedb.statedb
description     : World State DB
author          : Hyungjoo Yee
date_created    : 20180905
date_modified   : 20180905
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
import leveldb
import pickle
from gbrick.module.component.gbrickprofile import *
from gbrick.statedb.account import *
from gbrick.common.utils.singleton import *
from gbrick.common.type.genesisblock import *


@singleton
class StateDB:
    def __init__(self):
        self.profile = GbrickProfile().loads(PROFILE_PATH)

        if not os.path.isdir(self.profile.db_path):
            os.mkdir(self.profile.db_path)

        db_path = '{0}/db'.format(self.profile.db_path)
        if not os.path.isdir(db_path):
            os.mkdir(db_path)

        self.total_path = '{0}/db/{1}'.format(self.profile.db_path, 'state')
        self.db = leveldb.LevelDB(self.total_path, create_if_missing=True)
        self.num_height = 0
        self.hash_last_block = b''

        try:
            self.height = bytes_to_int(self.db.Get(b'height'))
        except Exception:
            print('no height')
            self.db.Put(b'height', int_to_bytes(self.num_height))

        try:
            self.hash_last_block = self.db.Get(b'last_block_hash')
        except Exception:
            print('no last block hash')
            self.db.Put(b'last_block_hash', b'')

    @staticmethod
    def to_raw(account: Account):
        return pickle.dumps(account.to_dict())

    @staticmethod
    def from_raw(raw: bytes) -> Account:
        return Account(pickle.loads(raw))

    def get_account(self, address_account: bytes) -> Account:
        try:
            raw = self.db.Get(address_account)
            account: Account = self.from_raw(raw)
            return account
        except Exception as e:
            print('[ERROR] StateDB::get_account: {0}'.format(address_account))
            return None

    def get_state(self, set_address_account: list) -> (int, bytes, dict):
        dict_result = {}

        for address_account in set_address_account:
            try:
                raw = self.db.Get(address_account)
                dict_result.__setitem__(address_account, self.from_raw(raw))
            except Exception:
                account = Account()
                account.address_account = address_account
                dict_result.__setitem__(address_account, account)

        height = bytes_to_int(self.db.Get(b'height'))
        hash_last_block = self.db.Get(b'last_block_hash')

        return height, hash_last_block, dict_result

    def update_state(self, num_height: int, hash_block: bytes, dict_account: dict):
        batch = leveldb.WriteBatch()
        batch.Put(b'height', int_to_bytes(num_height))
        batch.Put(b'last_block_hash', hash_block)

        for key in dict_account:
            batch.Put(key, self.to_raw(dict_account.get(key)))
            print('{0}, {1}'.format(key, dict_account.get(key)))

        self.db.Write(batch, sync=True)
        return True

    def update_genesis_block(self, g_block: GenesisBlock):
        print('[LOG] StateDB::update_genesis_block: {0}'.format(g_block.to_dict()))
        batch = leveldb.WriteBatch()
        batch.Put(b'height', int_to_bytes(0))
        batch.Put(b'last_block_hash', g_block.header.hash_block)
        for k in g_block.dict_assignment:
            acc = Account()
            acc.address_account = k.encode('utf-8')
            acc.balance = g_block.dict_assignment.get(k)
            batch.Put(acc.address_account, self.to_raw(acc))
        self.db.Write(batch, sync=True)
        return True

    '''
    def update_account(self, account: Account):
        raw = StateDB.to_raw(account)

        try:
            self.db.Put(account.address_account, raw)
        except Exception as e:
            print('[ERROR] StateDB::update_account: {0} \n// {1}'.format(e, account.to_json_str()))
            return False

        return True
    '''


if __name__ == '__main__':
    '''
    acc = Account()
    acc.address_account = b'1234'
    acc.type = AccountType.EOA
    acc.balance = 1000000000000000
    print(StateDB().update_state(1, b'abcd', {b'1234': acc}))
    '''
    #h, lbh, dict_state =StateDB().get_state([b'GX9375809dc0d77e00874eeea682d1f596c1a6535c'])
    #print(dict_state.get(b'GX9375809dc0d77e00874eeea682d1f596c1a6535c').to_dict())

    for i in StateDB().db.RangeIter():
        print(i)

    print(StateDB().from_raw(StateDB().db.Get(b'GX9375809dc0d77e00874eeea682d1f596c1a6535c')).to_dict())
    print(StateDB().from_raw(StateDB().db.Get(b'GXdd7e5b264224c3d79d6d86d92f06b39dd31e5663')).to_dict())