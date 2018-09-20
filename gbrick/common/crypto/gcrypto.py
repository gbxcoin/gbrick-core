import json
import binascii
import os
from ecdsa import SECP256k1, SigningKey, VerifyingKey
from gbrick.common.crypto.secp256k1 import *
from gbrick.common.crypto.aes import *
from gbrick.property import *


def create_account(file_path: str=None, password: str=None):
    if file_path and password:
        private_key = SigningKey.generate(curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        address_value = generate_address(public_key=public_key.to_string())

        pem = private_key.to_pem()
        cipher = AESCipher(password.encode())
        enc = cipher.encrypt(pem)

        if not os.path.isdir(file_path):
            os.mkdir(file_path)

        save_path = '{0}/{1}.keystore'.format(file_path, address_value)
        with open(save_path, 'wb') as f:
            f.write(enc)

        return address_value
    else:
        raise ValueError('File Path and Password is required')


def load_keystore(file_path: str=None, password: str=None):
    if file_path and password:
        try:
            with open(file_path, 'rb') as f:
                enc = f.read()

            cipher = AESCipher(password.encode())
            pem = cipher.decrypt(enc).decode()
            private_key = SigningKey.from_pem(pem)
            return private_key.to_string()
        except Exception as e:
            print('Wrong Password')

# path = directory?
def generate_private(create_key_path=None):
    # raise ValueError("There is no directory {}".format(path))
    if create_key_path:
        private = SigningKey.generate(curve=SECP256k1)
        with open('{0}/{1}'.format(create_key_path,), 'wb') as f:
            f.write(private.to_pem())
    else:
        raise ValueError('Path is None')


def generate_public(private_key_path=None, create_key_path=None):
    if private_key_path and create_key_path:
        seed = load_private(private_key_path)
        public = seed.get_verifying_key()
        with open(create_key_path, 'wb') as f:
            f.write(public.to_pem())
    else:
        raise ValueError('Path is None')


def load_private(private_key_path, password):
    if private_key_path:
        with open(private_key_path, 'rb') as f:
            encryptor = AES.new(sha3_str(password.encode('utf-8')), AES.MODE_CBC)
            private = SigningKey.from_pem(encryptor.decrypt(f.read()))
            print(private.to_pem())
    else:
        raise ValueError('Path is None')
    return private.to_string()

import hashlib
def generate_address(public_key: bytes):
    _sender = hashlib.sha256(public_key).digest()[12:]
    # bin 40bytes
    _result = 'GX'+binascii.hexlify(_sender).decode()
    assert len(_result) == 42
    # return is string
    return _result

def signing(msg_hash, private_key):
    v, r, s = sign(msg_hash, private_key)
    v = str(v).encode()
    signature = int_to_bytes32(r) + int_to_bytes32(s) + v
    assert len(signature) == 66
    signature = binascii.hexlify(signature)
    assert verifying(msg_hash, signature)
    return signature


def verifying(msg_hash, sig):
    # msg_hash : b'', sig : b''
    signature = binascii.unhexlify(sig)
    r, s = signature[:32], signature[32:64]
    v = signature[64:]
    v = int_to_bytes32(int(v))
    v, r, s = bytes_to_int(v), bytes_to_int(r), bytes_to_int(s)
    p, q = recover(msg_hash, (v, r, s))
    _public = int_to_bytes32(p) + int_to_bytes32(q)
    _sender = generate_address(_public)
    return _sender


if __name__ == '__main__':
    #res = generate_keystore(file_path=KEY_PATH)
    #print(res)
    account, privk = create_account('/Users/smcore/Documents/gbrick_test/gbrick1/keystore', '1234')


    msghash = hashlib.sha256('aaa'.encode()).digest()
    sig = signing(msghash, privk)
    #print('sig', sig)
    print('verifying account : ', verifying(msghash, sig))
    print('account : ', account)
