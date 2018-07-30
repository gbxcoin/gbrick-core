'''
name            : gbrick::key.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180213
date_modified   : 20180421
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from Crypto.Cipher import AES
from Crypto.Util import Counter

import binascii
import hashlib

class Key:

    #get_private_key,get_public_key is,get_gbrick_address Test function
    #This is only Test

    def  __init__(self):
        self.random_gen = Crypto.Random.new().read
        self.private_key = RSA.generate(1024, self.random_gen)
        self.public_key = self.private_key.publickey()
        str_publick_key = binascii.hexlify(self.public_key.exportKey(format='DER')).decode('ascii');
        self.gbrick_address = self.hash_block(str_publick_key)

    def get_private_key(self):
        return self.private_key

    def get_public_key(self):
        return self.public_key

    def get_gbrick_address(self):
        return self.gbrick_address

    def hash_block(self,block):
        # sha = hashlib.sha256()
        # sha.update(str(block).encode('utf-8'))

        rip = hashlib.new('ripemd160')
        rip.update(str(block).encode('utf-8'))

        return rip.hexdigest()

    def aes_ctr_encrypt(text, key, params):
        iv = params["iv"]
        ctr = Counter.new(128, initial_value=iv, allow_wraparound=True)
        mode = AES.MODE_CTR
        encryptor = AES.new(key, mode, counter=ctr)
        return encryptor.encrypt(text)


    def aes_ctr_decrypt(text, key, params):
        iv = params["iv"]
        ctr = Counter.new(128, initial_value=iv, allow_wraparound=True)
        mode = AES.MODE_CTR
        encryptor = AES.new(key, mode, counter=ctr)
        return encryptor.decrypt(text)

