'''
name            : gbrick>signature_helper.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180227
date_modified   : 20180430
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging

import binascii
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils, rsa, padding
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
from cryptography.x509 import Certificate



class PublicVerifier:
    """ provide singnature verify function using public key"""
    def __init__(self, public):
        """ set public key
        :param public: der or public Object
        """
        if isinstance(public, bytes):
            self.__public_key = serialization.load_der_public_key(
                public,
                backend=default_backend()
            )
        elif isinstance(public, EllipticCurvePublicKey):
            self.__public_key = public
        else:
            raise ValueError("public must bytes or public_key Object")

    def verify_data(self, data, signature) -> bool:
        """Verifying data signed with private key

        :param data: Original data to be signed
        :param signature: Value of Signature
        :return: Result of verification (True/False)
        """
        pub_key = self.__public_key
        return self.verify_data_with_publickey(public_key=pub_key, data=data, signature=signature)

    def verify_hash(self, digest, signature) -> bool:
        """Verifying a hash signed with a private key

        :param digest: The hash to be singed
        :param signature: Value of Signature
        :return: Result of verification (True/False)
        """
        # if hex string
        if isinstance(digest, str):
            try:
                digest = binascii.unhexlify(digest)
            except Exception as e:
                logging.warning(f"verify hash must hex or bytes {e}")
                return False

        return self.verify_data_with_publickey(public_key=self.__public_key,
                                               data=digest,
                                               signature=signature,
                                               is_hash=True)

    @staticmethod
    def verify_data_with_publickey(public_key, data: bytes, signature: bytes, is_hash: bool=False) -> bool:
        """Verifying signed data

        :param public_key: Public Key for Verification
        :param data: Original data to be signed
        :param signature: Value of Signature
        :param is_hash: Is hashed before signature (True/False)
        :return: Result of verification (True/False)
        """
        hash_algorithm = hashes.SHA256()
        if is_hash:
            hash_algorithm = utils.Prehashed(hash_algorithm)

        if isinstance(public_key, ec.EllipticCurvePublicKeyWithSerialization):
            try:
                public_key.verify(
                    signature=signature,
                    data=data,
                    signature_algorithm=ec.ECDSA(hash_algorithm)
                )
                return True
            except InvalidSignature:
                logging.debug("InvalidSignatureException_ECDSA")

        elif isinstance(public_key, rsa.RSAPublicKeyWithSerialization):
            try:
                public_key.verify(
                    signature,
                    data,
                    padding.PKCS1v15(),
                    hash_algorithm
                )
                return True
            except InvalidSignature:
                logging.debug("InvalidSignatureException_RSA")
        else:
            logging.debug("Unknown PublicKey Type : %s", type(public_key))

        return False

    def get_public_der(self):
        """ convert public_key to der return public_key
        """
        return self.__public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


class PublicVerifierContainer:
    """ PublicVerifier Container for many usaged """

    __public_verifier = {}

    # TODO 
    
    @classmethod
    def get_public_verifier(cls, serialized_public: bytes) -> PublicVerifier:
        try:
            public_verifier = cls.__public_verifier[serialized_public]
        except KeyError as e:
            public_verifier = cls.__create_public_verifier(serialized_public)

        return public_verifier

    @classmethod
    def __create_public_verifier(cls, serialized_public: bytes) -> PublicVerifier:
        """ create Public Verifier use serialized_public
        deserialize public key
        :param serialized_public: der public key
        :return: PublicVerifier
        """

        public_verifier = PublicVerifier(serialized_public)
        cls.__public_verifier[serialized_public] = public_verifier

        return public_verifier