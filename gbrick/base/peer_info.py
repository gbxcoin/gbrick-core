
'''
name            : gbrick::peer_info.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180225
date_modified   : 20180705
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import datetime
import logging
from enum import IntEnum


from gbrick.base import StubManager
from gbrick.protos import gbrick_pb2_grpc
from gbrick.tools.signature_helper import PublicVerifier


class PeerStatus(IntEnum):
    unknown = 0
    connected = 1
    disconnected = 2


class PeerInfo:

    def __init__(self, peer_id: str, group_id: str, target: str = "", status: PeerStatus = PeerStatus.unknown,
                 cert: bytes = b"", order: int = 0):

        self.__peer_id = peer_id
        self.__group_id = group_id
        self.__order: int = order
        self.__target: str = target

        self.__status_update_time = datetime.datetime.now()
        self.__status = status

        self.__cert: str = cert

    @property
    def peer_id(self) -> str:
        return self.__peer_id

    @property
    def group_id(self) -> str:
        return self.__group_id

    @property
    def order(self):
        return self.__order

    @order.setter
    def order(self, order: int):
        self.__order = order

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, target):
        self.__target = target

    @property
    def cert(self):
        return self.__cert

    @cert.setter
    def cert(self, cert):
        self.__cert = cert

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        if self.__status != status:
            self.__status_update_time = datetime.datetime.now()
            self.__status = status

    @property
    def status_update_time(self):
        return self.__status_update_time


class PeerObject:

    def __init__(self, peer_info: PeerInfo):
        self.__peer_info: PeerInfo = peer_info
        self.__stub_manager: StubManager = None
        self.__cert_verifier: PublicVerifier = None
        self.__no_response_count = 0

        self.__create_live_data()

    def __create_live_data(self):
        try:
            self.__stub_manager = StubManager(self.__peer_info.target, gbrick_pb2_grpc.PeerServiceStub)
        except Exception as e:
            logging.exception(f"Create Peer create stub_manager fail target : {self.__peer_info.target} \n"
                              f"exception : {e}")
        try:
            self.__cert_verifier = PublicVerifier(self.peer_info.cert)
        except Exception as e:
            logging.exception(f"create cert verifier error : {self.__peer_info.cert} \n"
                              f"exception {e}")

    @property
    def peer_info(self)-> PeerInfo:
        return self.__peer_info

    @property
    def stub_manager(self) -> StubManager:
        return self.__stub_manager

    @property
    def cert_verifier(self) -> PublicVerifier:
        return self.__cert_verifier

    @property
    def no_response_count(self):
        return self.__no_response_count

    def no_response_count_up(self):
        self.__no_response_count += 1

    def no_response_count_reset(self):
        self.__no_response_count = 0
