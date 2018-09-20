'''
name            : gbrick.module.component.gbrickprofile
description     : Profile of Node Information (id, port)
author          : Hyungjoo Yee
date_created    : 20180824
date_modified   : 20180824
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
import os
from gbrick.common.utils.singleton import *
from gbrick.module.component.moduleprofile import *
from gbrick.common.crypto.gcrypto import *
from gbrick.property import *


class GbrickProfile(metaclass=Singleton):
    FILE_NAME = 'gbrick.profile'

    def __init__(self):
        password = '4455'
        self.peer_port = None
        self.db_path = None
        self.profile: ModuleProfile = None
        self.address_coinbase = b''
        self.private_key = b''
        self.is_loaded = False

    def set_default(self):
        self.peer_port = 6600
        self.db_path = DB_PATH

    def loads(self, p_file_path: str):
        if self.is_loaded is True:
            return self

        if p_file_path is None or p_file_path.__len__() == 0:
            raise ValueError('file path is required')

        f = open('{0}/{1}'.format(p_file_path, self.FILE_NAME), 'r')
        str_profile_json = f.read()
        f.close()

        dict_profile = json.loads(str_profile_json)

        self.peer_port = dict_profile.get('peer_port')
        self.db_path = dict_profile.get('db_path')
        self.address_coinbase = dict_profile.get('coinbase')
        if self.address_coinbase is None or self.address_coinbase.__eq__(''):
            self.address_coinbase = create_account('{0}/keystore'.format(p_file_path), PASSWORD)
        else:
            self.address_coinbase = self.address_coinbase.encode('utf-8')
        self.private_key = load_keystore('{0}/keystore/{1}.keystore'.format(p_file_path, self.address_coinbase.decode('utf-8')), PASSWORD)

        self.is_loaded = True
        return self

    def write(self, p_file_path: str):
        if p_file_path is None or p_file_path.__len__() == 0:
            raise ValueError('file path is required')

        dict_profile = {}
        dict_profile.__setitem__('peer_port', self.peer_port)
        dict_profile.__setitem__('db_path', self.db_path)
        dict_profile.__setitem__('coinbase', self.address_coinbase.decode('utf-8'))

        str_profile_json = json.dumps(dict_profile)

        if not os.path.isdir(p_file_path):
            os.mkdir(p_file_path)

        f = open('{0}/{1}'.format(p_file_path, self.FILE_NAME), 'w')
        f.write(str_profile_json)
        f.close()

if __name__ == '__main__':
    #gp = GbrickProfile()
    #gp.set_default()
    #gp.write(PROFILE_PATH)
    g = GbrickProfile()
    g.loads(PROFILE_PATH)
    g.write(PROFILE_PATH)





    '''
name            : gbrick.module.component.gbrickprofile
description     : Profile of Node Information (id, port)
author          : Hyungjoo Yee
date_created    : 20180824
date_modified   : 20180824
version         : 1.0
python_version  : 3.6.5
Comments        :
import os
from gbrick.common.utils.singleton import *
from gbrick.module.component.moduleprofile import *
from gbrick.common.crypto.gcrypto import *
from gbrick.property import *


class GbrickProfile(metaclass=Singleton):
    FILE_NAME = 'gbrick.profile'

    def __init__(self):
        self.peer_port = None
        self.db_path = None
        self.private_key = load_keystore()
        self.address_coinbase = b''
        self.prof_p2p: ModuleProfile = None
        self.prof_consensus: ModuleProfile = None
        self.prof_blockchain: ModuleProfile = None
        self.prof_wagon: ModuleProfile = None
        self.prof_state: ModuleProfile = None

        self.is_loaded = False

    def set_default(self):
        self.peer_port = ModulePort.NONE
        self.db_path = DB_PATH

        self.prof_p2p = ModuleProfile()
        self.prof_p2p.ip = '127.0.0.1'
        self.prof_p2p.port = ModulePort.P2P
        self.prof_p2p.type = ModuleType.P2P
        self.prof_p2p.name = 'P2P'
        self.prof_p2p.receiver_thread = 10
        self.prof_p2p.id = self.prof_p2p.to_hash()

        self.prof_consensus = ModuleProfile()
        self.prof_consensus.ip = '127.0.0.1'
        self.prof_consensus.port = ModulePort.CONSENSUS
        self.prof_consensus.type = ModuleType.CONSENSUS
        self.prof_consensus.name = 'Consensus'
        self.prof_consensus.receiver_thread = 1
        self.prof_consensus.id = self.prof_consensus.to_hash()

        self.prof_blockchain = ModuleProfile()
        self.prof_blockchain.ip = '127.0.0.1'
        self.prof_blockchain.port = ModulePort.BLOCKCHAIN
        self.prof_blockchain.type = ModuleType.BLOCKCHAIN
        self.prof_blockchain.name = 'Blockchain'
        self.prof_blockchain.receiver_thread = 10
        self.prof_blockchain.id = self.prof_blockchain.to_hash()

        self.prof_wagon = ModuleProfile()
        self.prof_wagon.ip = '127.0.0.1'
        self.prof_wagon.port = ModulePort.WAGON
        self.prof_wagon.type = ModuleType.WAGON
        self.prof_wagon.name = 'Wagon'
        self.prof_wagon.receiver_thread = 1
        self.prof_wagon.id = self.prof_wagon.to_hash()

        self.prof_state = ModuleProfile()
        self.prof_state.ip = '127.0.0.1'
        self.prof_state.port = ModulePort.STATE
        self.prof_state.type = ModuleType.STATE
        self.prof_state.name = 'State'
        self.prof_state.receiver_thread = 10
        self.prof_state.id = self.prof_state.to_hash()

    def loads(self, p_file_path: str):
        if self.is_loaded is True:
            return self

        if p_file_path is None or p_file_path.__len__() == 0:
            raise ValueError('file path is required')

        f = open('{0}/{1}'.format(p_file_path, self.FILE_NAME), 'r')
        str_profile_json = f.read()
        f.close()

        dict_profile = json.loads(str_profile_json)

        self.peer_port = dict_profile.get('peer_port')
        self.db_path = dict_profile.get('db_path')
        self.address_coinbase = dict_profile.get('coinbase').encode('utf-8')

        self.prof_p2p = ModuleProfile(dict_profile.get('p2p'))
        self.prof_consensus =  ModuleProfile(dict_profile.get('consensus'))
        self.prof_blockchain = ModuleProfile(dict_profile.get('blockchain'))
        self.prof_wagon = ModuleProfile(dict_profile.get('wagon'))
        self.prof_state = ModuleProfile(dict_profile.get('state'))
        self.is_loaded = True
        return self

    def write(self, p_file_path: str):
        if p_file_path is None or p_file_path.__len__() == 0:
            raise ValueError('file path is required')

        dict_profile = {}
        dict_profile.__setitem__('peer_port', self.peer_port)
        dict_profile.__setitem__('db_path', self.db_path)
        dict_profile.__setitem__('coinbase', self.address_coinbase.decode('utf-8'))
        dict_profile.__setitem__('p2p', self.prof_p2p.to_dict())
        dict_profile.__setitem__('consensus', self.prof_consensus.to_dict())
        dict_profile.__setitem__('blockchain', self.prof_blockchain.to_dict())
        dict_profile.__setitem__('wagon', self.prof_wagon.to_dict())
        dict_profile.__setitem__('statedb', self.prof_state.to_dict())

        str_profile_json = json.dumps(dict_profile)

        if not os.path.isdir(p_file_path):
            os.mkdir(p_file_path)

        f = open('{0}/{1}'.format(p_file_path, self.FILE_NAME), 'w')
        f.write(str_profile_json)
        f.close()

if __name__ == '__main__':
    gp = GbrickProfile()
    gp.set_default()
    gp.write(PROFILE_PATH)

    '''
