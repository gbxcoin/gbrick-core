
'''
name            : gbrick::gnc_service.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180215
date_modified   : 20180720
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging
import random
import time
import timeit

from gbrick import utils as util
from gbrick import define as Define
from gbrick.base import ObjectManager
from gbrick.service import RestServiceRS, CommonService
from gbrick.peer import ChannelManager
from gbrick.protos import gbrick_pb2_grpc
from gbrick.gncontroller import OuterService, AdminService, AdminManager

# gbrick_pb2 not import pickle error
import gbrick_pb2


class GNControllerService:

    def __init__(self, gnc_ip=None, cert_path=None, cert_pass=None, rand_seed=None):

        if gnc_ip is None:
            gnc_ip = Define.IP_GNC
        logging.info("Set GNC IP: " + gnc_ip)
        if cert_path is not None:
            logging.info("CA Certificate Path : " + cert_path)

        self.__common_service = CommonService(gbrick_pb2)
        self.__admin_manager = AdminManager("station")
        self.__channel_manager = None
        self.__rest_service = None

        # GNC has two status (active, standby) active means enable outer service
        # standby means stop outer service and heartbeat to the other RS (active)
        self.__is_active = False

        if Define.ENABLE_KMS:
            if rand_seed is None:
                util.exit_and_msg("KMS needs input random seed \n"
                                  "you can put seed -s --seed")
            self.__random_table = self.__create_random_table(rand_seed)


        # gRPC service for GNC
        self.__outer_service = OuterService()
        self.__admin_service = AdminService()

        # {group_id:[ {peer_id:IP} ] }
        self.peer_groups = {Define.ALL_GROUP_ID: []}
        self.auth = {}

        ObjectManager().rs_service = self

    def __del__(self):
        pass

    def launch_block_generator(self):
        pass

    def validate_group_id(self, group_id: str):
        return 0, "It's available group ID:"+group_id

    @property
    def admin_manager(self):
        return self.__admin_manager

    @property
    def channel_manager(self):
        return self.__channel_manager

    @property
    def common_service(self):
        return self.__common_service

    @property
    def random_table(self):
        return self.__random_table

    def __broadcast_new_peer(self, peer_request):

        logging.debug("Broadcast New Peer.... " + str(peer_request))
        if self.__common_service is not None:
            self.__common_service.broadcast("AnnounceNewPeer", peer_request)

    def check_peer_status(self):
        time.sleep(Define.SLEEP_SECONDS_IN_GNC_HEARTBEAT)
        util.logger.spam(f"rs_service:check_peer_status(Heartbeat.!.!) for reset Leader and delete no response Peer")

        for channel in self.__channel_manager.get_channel_list():
            delete_peer_list = self.__channel_manager.get_peer_manager(channel).check_peer_status()

            for delete_peer in delete_peer_list:
                logging.debug(f"delete peer {delete_peer.peer_id}")
                message = gbrick_pb2.PeerID(
                    peer_id=delete_peer.peer_id,
                    channel=channel,
                    group_id=delete_peer.group_id)
                self.__common_service.broadcast("AnnounceDeletePeer", message)

    def __create_random_table(self, rand_seed: int) -> list:
        """create random_table using random_seed
        table size define in Define.RANDOM_TABLE_SIZE

        :param rand_seed: random seed for create random table
        :return: random table
        """
        random.seed(rand_seed)
        random_table = []
        for i in range(Define.RANDOM_TABLE_SIZE):
            random_num: int = random.getrandbits(Define.RANDOM_SIZE)
            random_table.append(random_num)

        return random_table

    def serve(self, port=None):
        if port is None:
            port = Define.PORT_GNC
        stopwatch_start = timeit.default_timer()

        self.__channel_manager = ChannelManager(self.__common_service)

        if Define.ENABLE_REST_SERVICE:
            self.__rest_service = RestServiceRS(int(port))

        gbrick_pb2_grpc.add_GNControllerServicer_to_server(self.__outer_service, self.__common_service.outer_server)
        gbrick_pb2_grpc.add_AdminServiceServicer_to_server(self.__admin_service, self.__common_service.inner_server)

        logging.info("Start peer service at port: " + str(port))

        if Define.ENABLE_GNC_HEARTBEAT:
            self.__common_service.add_loop(self.check_peer_status)
        self.__common_service.start(port)

        stopwatch_duration = timeit.default_timer() - stopwatch_start
        logging.info(f"Start GNC start duration({stopwatch_duration})")

        self.__common_service.wait()

        if self.__rest_service is not None:
            self.__rest_service.stop()
