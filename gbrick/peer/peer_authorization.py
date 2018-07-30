
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180212
date_modified   : 20180705
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import datetime
import logging
import binascii

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec, utils

from gbrick import utils as util
from gbrick.tools import PublicVerifier
from gbrick import define as Define


class PeerAuthorization(PublicVerifier):
    __peer_pri = None
    __ca_cert = None
    __token = None

    # RequestPeer
    __peer_info = None

    def __init__(self, public_file="", pri_file="", cert_pass="", rand_table=None):

        try:
            if Define.ENABLE_KMS:
                self.__peer_pri = self.__key_derivation(rand_table)
                super().__init__(self.__peer_pri.public_key())

            else:
                logging.debug(f"public file : {public_file}")
                logging.debug(f"private file : {pri_file}")

                with open(public_file, "rb") as der:
                    public_bytes = der.read()
                    super().__init__(public_bytes)

                self.__load_private(pri_file, cert_pass)

        except Exception as e:
            util.exit_and_msg(f"key load fail cause : {e}")

    def __load_private(self, pri_file, cert_pass):
        """
        :param pri_file
        :param cert_pass
        :return:
        """
        with open(pri_file, "rb") as der:
            private_bytes = der.read()
            try:
                self.__peer_pri = serialization.load_der_private_key(private_bytes, cert_pass, default_backend())
            except ValueError as e:
                logging.exception(f"error {e}")
                util.exit_and_msg("Invalid Password")


        sign = self.sign_data(b'TEST')
        if self.verify_data(b'TEST', sign) is False:
            util.exit_and_msg("Invalid Signature(Peer Certificate load test)")

    def set_peer_info(self, peer_id, peer_target, group_id, peer_type):
        self.__peer_info = b''.join([peer_id.encode('utf-8'),
                                     peer_target.encode('utf-8'),
                                     group_id.encode('utf-8')]) + bytes([peer_type])

    def sign_data(self, data, is_hash=False):

        hash_algorithm = hashes.SHA256()
        if is_hash:
            hash_algorithm = utils.Prehashed(hash_algorithm)
            if isinstance(data, str):
                try:
                    data = binascii.unhexlify(data)
                except Exception as e:
                    logging.error(f"hash data must hex string or bytes \n exception : {e}")
                    return None

        if not isinstance(data, (bytes, bytearray)):
            logging.error(f"data must be bytes \n")
            return None

        if isinstance(self.__peer_pri, ec.EllipticCurvePrivateKeyWithSerialization):
            return self.__peer_pri.sign(
                data,
                ec.ECDSA(hash_algorithm))
        elif isinstance(self.__peer_pri, rsa.RSAPrivateKeyWithSerialization):
            return self.__peer_pri.sign(
                data,
                padding.PKCS1v15(),
                hash_algorithm
            )
        else:
            logging.error("Unknown PrivateKey Type : %s", type(self.__peer_pri))
            return None

    def generate_request_sign(self, rand_key):

        tbs_data = self.__peer_info + bytes.fromhex(rand_key)
        return self.sign_data(tbs_data)

    def get_token_time(self, token):

        token_time = token[2:18]
        token_date = int(token_time, 16)
        current_date = int(datetime.datetime.now().timestamp() * 1000)
        if current_date < token_date:
            return bytes.fromhex(token_time)

        return None

    @staticmethod
    def __key_derivation(rand_table):
        """ key derivation using rand_table and Define.FIRST_SEED Define.SECOND_SEED

        :param rand_table:
        :return: private_key
        """

        hash_value = rand_table[Define.FIRST_SEED] + rand_table[Define.SECOND_SEED] + Define.MY_SEED
        return ec.derive_private_key(hash_value, ec.SECP256K1(), default_backend())
