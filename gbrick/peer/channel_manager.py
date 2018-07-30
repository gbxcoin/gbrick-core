
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180203
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import json
import leveldb
import logging
import pickle

import time

import gbrick.utils as util
from gbrick import define as Define
from gbrick.base import StubManager, ObjectManager, PeerManager
from gbrick.service import CommonService
from gbrick.peer import BlockManager
from gbrick.protos import gbrick_pb2_grpc, gbrick_pb2
from gbrick.utils import define_code


class ChannelManager:

    def __init__(self, common_service: CommonService, level_db_identity="station"):
        self.__common_service = common_service
        self.__level_db_identity = level_db_identity
        self.__peer_managers = {}  # key(channel_name):value(peer_manager)
        self.__block_managers = {}  # key(channel_name):value(block_manager), This available only peer
        self.__glogic_containers = {}
        self.__glogic_stubs = {}
        self.__glogic_infos = {}
        if ObjectManager().rs_service is not None:
            self.__load_peer_managers()

    def load_block_manager(self, peer_id=None, channel=None):
        if channel is None:
            channel = Define.GBRICK_DEFAULT_CHANNEL
        logging.debug(f"load_block_manager_each channel({channel})")
        try:
            self.__block_managers[channel] = BlockManager(
                common_service=self.__common_service,
                peer_id=peer_id,
                channel_name=channel,
                level_db_identity=self.__level_db_identity
            )
        except leveldb.LevelDBError as e:
            util.exit_and_msg("LevelDBError(" + str(e) + ")")

    def get_channel_list(self) -> list:
        return list(self.__peer_managers)

    def get_peer_manager(self, channel_name=None) -> PeerManager:
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL
        return self.__peer_managers[channel_name]

    def get_block_manager(self, channel_name=None) -> BlockManager:
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL
        try:
            return self.__block_managers[channel_name]
        except KeyError as e:
            util.logger.warning(f"channel_manager:get_block_manager there is no channel({channel_name})")
            return None

    def start_block_managers(self):
        for block_manager in self.__block_managers:
            self.__block_managers[block_manager].start()

    def stop_block_managers(self):
        for block_manager in self.__block_managers:
            self.__block_managers[block_manager].stop()

    def remove_peer(self, peer_id, group_id):
        for peer_manager in self.__peer_managers:
            self.__peer_managers[peer_manager].remove_peer(peer_id, group_id)

    def set_peer_type(self, peer_type):
        """Set peer type when peer start only

        :param peer_type:
        :return:
        """
        for block_manager in self.__block_managers:
            self.__block_managers[block_manager].set_peer_type(peer_type)

    def save_peer_manager(self, peer_manager, channel_name=None):
        """peer_list save in leveldb

        :param peer_manager:
        :param channel_name:
        """
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL
        level_db_key_name = str.encode(Define.LEVEL_DB_KEY_FOR_PEER_LIST)

        try:
            dump = peer_manager.dump()
            level_db = self.__block_managers[channel_name].get_level_db()
            level_db.Put(level_db_key_name, dump)

        except AttributeError as e:
            logging.warning("Fail Save Peer_list: " + str(e))

    def __load_peer_managers(self):
        for channel in ObjectManager().rs_service.admin_manager.get_channel_list():
            self.load_peer_manager(channel)

    def load_peer_manager(self, channel=None):
        """
        :return: peer_manager
        """

        if channel is None:
            channel = Define.GBRICK_DEFAULT_CHANNEL
        peer_manager = PeerManager(channel)

        level_db_key_name = str.encode(Define.LEVEL_DB_KEY_FOR_PEER_LIST)

        if Define.IS_LOAD_PEER_MANAGER_FROM_DB:
            try:
                level_db = self.__block_managers[channel].get_level_db()
                peer_list_data = pickle.loads(level_db.Get(level_db_key_name))
                peer_manager.load(peer_list_data)
                logging.debug("load peer_list_data on yours: " + peer_manager.get_peers_for_debug())
            except KeyError:
                logging.warning("There is no peer_list_data on yours")

        self.__peer_managers[channel] = peer_manager

    def authorized_channels(self, peer_id) -> list:
        authorized_channels = []

        # TODO
        # for channel in self.__peer_managers:
        #     logging.warning(f"channel is ({channel})")
        #     peer_manager = self.__peer_managers[channel]
        #
        #     if peer_manager is not None and peer_manager.get_peer(peer_id):
        #         authorized_channels.append(channel)

        # TODO
        for channel in list(self.__peer_managers):
            logging.warning(f"channel is ({channel})")
            authorized_channels.append(channel)

        logging.warning(f"authorized channels ({authorized_channels})")

        return authorized_channels

    def load_glogic_container_each(self, channel_name: str, glogic_package: str, container_port: int, peer_target: str):
        """create glogic container and save glogic_info and glogic_stub

        :param channel_name: channel name
        :param glogic_package: load glogic package name
        :param container_port: glogic container port
        :return:
        """
        glogic_info = None
        # retry_times = 1
        #
        # while glogic_info is None:
        #     if util.check_port_using(Define.IP_PEER, container_port) is False:
        #         util.logger.spam(f"channel_manager:load_glogic_container_each init GlogicService port({container_port})")
        #         self.__glogic_containers[channel_name] = GlogicService(container_port)
        #         self.__glogic_stubs[channel_name] = StubManager.get_stub_manager_to_server(
        #             Define.IP_PEER + ':' + str(container_port),
        #             gbrick_pb2_grpc.ContainerStub,
        #             is_allow_null_stub=True
        #         )
        #     glogic_info = self.__load_glogic(glogic_package, self.get_glogic_container_stub(channel_name), peer_target)
        #
        #     if glogic_info is not None or retry_times >= Define.GLOGIC_LOAD_RETRY_TIMES:
        #         break
        #     else:
        #         util.logger.spam(f"channel_manager:load_glogic_container_each glogic_info load fail retry({retry_times})")
        #         retry_times += 1
        #         time.sleep(Define.GLOGIC_LOAD_RETRY_INTERVAL)
        #
        # if glogic_info is None:
        #     return False

        self.__glogic_infos[channel_name] = glogic_info

        return True

    # def __load_glogic(self, glogic_package_name: str, glogic_container_stub: StubManager, peer_target: str):
    #
    #     util.logger.spam(f"peer_service:__load_glogic --start--")
    #     logging.info("LOAD GLOGIC AND CONNECT TO GLOGIC SERVICE!")
    #     params = dict()
    #     params[define_code.MetaParams.GlogicLoad.repository_path] = Define.DEFAULT_GLOGIC_REPOSITORY_PATH
    #     params[define_code.MetaParams.GlogicLoad.glogic_package] = glogic_package_name
    #     params[define_code.MetaParams.GlogicLoad.base] = Define.DEFAULT_GLOGIC_BASE
    #     params[define_code.MetaParams.GlogicLoad.peer_id] = \
    #         None if ObjectManager().peer_service is None else ObjectManager().peer_service.peer_id
    #     meta = json.dumps(params)
    #     #logging.debug(f"load glogic params : {meta}")
    #
    #     if glogic_container_stub is None:
    #         util.exit_and_msg(f"there is no __stub_to_glogicservice!")
    #
    #     util.logger.spam(f"peer_service:__load_glogic --1--")
    #     # glogic Load is so slow ( load time out is more than GRPC_CONNECTION_TIMEOUT)
    #     response = glogic_container_stub.call(
    #         "Request",
    #         gbrick_pb2.Message(code=define_code.Request.glogic_load, meta=meta),
    #         Define.GLOGIC_LOAD_TIMEOUT
    #     )
    #     logging.debug("try glogic load on glogic service: " + str(response))
    #     if response is None:
    #         return None
    #
    #     util.logger.spam(f"peer_service:__load_glogic --2--")
    #     response_connect = glogic_container_stub.call(
    #         "Request",
    #         gbrick_pb2.Message(code=define_code.Request.glogic_connect, message=peer_target),
    #         Define.GRPC_CONNECTION_TIMEOUT
    #     )
    #     logging.debug("try connect to glogic service: " + str(response_connect))
    #     if response_connect is None:
    #         return None
    #
    #     if response.code == define_code.Response.success:
    #         logging.debug("Get glogic from glogic Server...")
    #         glogic_info = json.loads(response.meta)
    #     else:
    #         util.exit_and_msg("Fail Get glogic from glogic Server...")
    #     logging.info("LOAD GLOGIC DONE!")
    #
    #     util.logger.spam(f"peer_service:__load_glogic --end--")
    #
    #     return glogic_info

    def get_glogic_container_stub(self, channel_name=None) -> StubManager:
        """get glogic_stub corresponding to channel_name

        :param channel_name: channel_name default value is Define.GBRICK_DEFAULT_CHANNEL
        :return: glogic stub implements inner service
        :raise: KeyError: not exist stub corresponding to channel_name
        """
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL
        return self.__glogic_stubs[channel_name]

    def get_glogic_info(self, channel_name: str = None) -> dict:
        """get glogic_info corresponding to channel_name

        :param channel_name: channel_name
        :return: glogic_info
        :raise: KeyError: not exist stub corresponding to channel_name
        """
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL
        return self.__glogic_infos[channel_name]

    def stop_glogic_containers(self):
        """stop all glogic containers and init all properties

        :return:
        """
        for channel in self.__glogic_containers.keys():
            self.__glogic_containers[channel].stop()

        self.__glogic_containers = {}
        self.__glogic_infos = {}
        self.__glogic_stubs = {}
