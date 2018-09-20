from gbrick.common.type.block import *
from gbrick.module.component.gbrickprofile import *


class GenesisBlock(Block):
    def __init__(self, p_json_str: str = None, p_dict_obj: dict = None):
        if p_json_str is None and p_dict_obj is None:
            super().__init__()
            self.hash_root_assignment = b''
            self.dict_assignment = {} # address(str): balance(int)

        elif p_dict_obj is not None:
            self.from_dict(p_dict_obj)

        elif p_json_str is not None:
            self.from_dict(json.loads(p_json_str))

    def from_dict(self, p_dict: dict):
        super().from_dict(p_dict)
        self.dict_assignment = p_dict.get('assignment')
        if not self.dict_assignment:
            self.dict_assignment = {}

    def to_dict(self):
        dict_obj = super().to_dict()
        dict_obj.__setitem__('assignment', self.dict_assignment)
        return dict_obj

    def to_json_str(self):
        dict_obj = self.to_dict()
        return json.dumps(dict_obj)

    def get_wave(self):
        return None

    def generate_assignment_root_hash(self):
        list_hash = []
        for k, v in self.dict_assignment:
            list_hash.append(to_gbrick_hash('{0}:{1}'.format(k, v)))

        return merkleroot(list_hash)

    def generate_file(self):
        f = open('{0}/{1}'.format(PROFILE_PATH, 'gbrick_genesis.block'), 'w')
        self.header.hash_block = self.to_hash()
        f.write(b.to_json_str())
        f.close()



if __name__ == '__main__':
    #create_account(PROFILE_PATH+'/keystore', 'smcore1234!@')
    # private_key = load_keystore(PROFILE_PATH+'/keystore/GX9375809dc0d77e00874eeea682d1f596c1a6535c.keystore', PASSWORD)
    # print(private_key)
    #
    # hash_val = to_gbrick_hash('a')
    # print(hash_val)
    # signature = signing(hash_val, private_key)
    # print(signature)
    #
    # print(verifying(hash_val, signature))

    b = GenesisBlock()
    b.dict_assignment.__setitem__('GX9375809dc0d77e00874eeea682d1f596c1a6535c', 1000000000000000000)
    b.generate_file()