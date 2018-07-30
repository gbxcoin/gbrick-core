
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180206
date_modified   : 20180711
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import timeit
import uuid
from time import sleep

from gbrick.base import BroadcastProcess, StubManager
from gbrick.blockchain import *
from gbrick.service import RestService, CommonService
from gbrick.peer import SendToProcess, InnerService, OuterService, ChannelManager
from gbrick.peer.peer_authorization import PeerAuthorization
from gbrick.protos import gbrick_pb2, gbrick_pb2_grpc
from gbrick.utils import define_code


class PeerService:

    def __init__(self,
                 group_id=None,
                 gnc_ip=None,
                 gnc_port=None,
                 public_path=None,
                 private_path=None,
                 cert_pass=None):

        if gnc_ip is None:
            gnc_ip = Define.IP_GNC
        if gnc_port is None:
            gnc_port = Define.PORT_GNC
        if public_path is None:
            public_path = Define.PUBLIC_PATH
        if private_path is None:
            private_path = Define.PRIVATE_PATH
        if cert_pass is None:
            cert_pass = Define.DEFAULT_PW

        util.logger.spam(f"Your Peer Service runs on debugging MODE!")
        util.logger.spam(f"You can see many terrible garbage logs just for debugging, R U Really want it?")

        self.__send_to_process_thread = SendToProcess()

        self.__gnc_target = gnc_ip + ":" + str(gnc_port)
        logging.info("Set GNC target is " + self.__gnc_target)

        self.__stub_to_gnc = None

        self.__level_db = None
        self.__level_db_path = ""

        self.__peer_id = None
        self.__group_id = group_id
        if self.__group_id is None and Define.PEER_GROUP_ID != "":
            self.__group_id = Define.PEER_GROUP_ID

        self.__common_service = None
        self.__channel_manager: ChannelManager = None

        self.__rest_service = None
        #self.__timer_service = TimerService()

        # TODO
        self.__glogic = None
        self.__peer_target = None
        self.__inner_target = None
        self.__peer_port = 0

        # For Send tx to leader
        self.__tx_process = None

        if Define.ENABLE_KMS:
            rand_table = self.__get_random_table()
            self.__auth = PeerAuthorization(rand_table=rand_table)
        else:
            self.__auth = PeerAuthorization(public_path, private_path, cert_pass)

        # gRPC service for Peer
        self.__inner_service = InnerService()
        self.__outer_service = OuterService()

        self.__reset_voter_in_progress = False

    @property
    def common_service(self):
        return self.__common_service

    @property
    def timer_service(self):
        return self.__timer_service

    @property
    def channel_manager(self):
        return self.__channel_manager

    @property
    def send_to_process_thread(self):
        return self.__send_to_process_thread

    @property
    def tx_process(self):
        return self.__tx_process

    @property
    def peer_target(self):
        return self.__peer_target

    @property
    def auth(self):
        return self.__auth

    @property
    def stub_to_gnc(self) -> StubManager:
        if self.__stub_to_gnc is None:
            self.__stub_to_gnc = StubManager.get_stub_manager_to_server(
                self.__gnc_target,
                gbrick_pb2_grpc.GNControllerStub,
                Define.CONNECTION_RETRY_TIMEOUT_TO_RS)

        return self.__stub_to_gnc

    @property
    def peer_id(self):
        return self.__peer_id

    @property
    def group_id(self):
        if self.__group_id is None:
            self.__group_id = self.__peer_id
        return self.__group_id

    @property
    def peer_target(self):
        return self.__peer_target

    def __get_random_table(self) -> list:
        try:
            response = self.stub_to_gnc.call_in_time("GetRandomTable", gbrick_pb2.CommonRequest(request=""))
            if response.response_code == define_code.Response.success:
                random_table = json.loads(response.message)
            else:
                util.exit_and_msg(f"get random table fail \n"
                                  f"cause by {response.message}")
            return random_table
        except Exception as e:
            util.exit_and_msg(f"get random table and init peer_auth fail \n"
                              f"cause by : {e}")

    def rotate_next_leader(self, channel_name):
        """Find Next Leader Id from peer_list and reset leader to that peer"""

        # logging.debug("rotate next leader...")
        util.logger.spam(f"peer_service:rotate_next_leader")
        peer_manager = self.__channel_manager.get_peer_manager(channel_name)
        next_leader = peer_manager.get_next_leader_peer(is_only_alive=True)

        # Check Next Leader is available...
        if next_leader is not None and next_leader.peer_id != self.peer_id:
            try:
                stub_manager = peer_manager.get_peer_stub_manager(next_leader)
                response = stub_manager.call(
                    "GetStatus",
                    gbrick_pb2.StatusRequest(request="get_leader_peer"),
                    is_stub_reuse=True
                )

                # peer_status = json.loads(response.status)
                # if peer_status["peer_type"] != str(gbrick_pb2.BLOCK_GENERATOR):
                #     logging.warning("next rotate is not a leader")
                #     raise Exception

            except Exception as e:
                logging.warning(f"rotate next leader exceptions({e})")
                next_leader = peer_manager.leader_complain_to_rs(Define.ALL_GROUP_ID)

        if next_leader is not None:
            self.reset_leader(next_leader.peer_id, channel_name)
        else:
            util.logger.warning(f"peer_service:rotate_next_leader next_leader is None({next_leader})")

    def reset_leader(self, new_leader_id, channel: str):
        logging.info(f"RESET LEADER channel({channel}) leader_id({new_leader_id})")

        block_manager = self.__channel_manager.get_block_manager(channel)
        peer_manager = self.__channel_manager.get_peer_manager(channel)
        complained_leader = peer_manager.get_leader_peer()
        leader_peer = peer_manager.get_peer(new_leader_id, None)

        if leader_peer is None:
            logging.warning(f"in peer_service:reset_leader There is no peer by peer_id({new_leader_id})")
            return

        util.logger.spam(f"peer_service:reset_leader target({leader_peer.target})")

        peer_manager.set_leader_peer(leader_peer, None)

        self_peer_object = peer_manager.get_peer(self.__peer_id)
        peer_leader = peer_manager.get_leader_peer()
        peer_type = gbrick_pb2.PEER

        if self_peer_object.target == peer_leader.target:
            util.change_log_color_set(True)
            logging.debug("Set Peer Type Leader!")
            peer_type = gbrick_pb2.BLOCK_GENERATOR
            block_manager.get_blockchain().reset_made_block_count()

            response = peer_manager.get_peer_stub_manager(self_peer_object).call(
                "Request",
                gbrick_pb2.Message(
                    code=define_code.Request.status,
                    channel=channel
                ),
                is_stub_reuse=True
            )

            peer_status = json.loads(response.meta)
            if peer_status['peer_type'] == str(gbrick_pb2.BLOCK_GENERATOR):
                is_broadcast = True
            else:
                is_broadcast = False

            peer_manager.announce_new_leader(complained_leader.peer_id, new_leader_id, is_broadcast=is_broadcast)
        else:
            util.change_log_color_set()
            logging.debug("Set Peer Type Peer!")
            self.__common_service.subscribe(
                channel=channel,
                subscribe_stub=peer_manager.get_peer_stub_manager(peer_leader),
                peer_type=gbrick_pb2.BLOCK_GENERATOR
            )

        # update candidate blocks
        block_manager.get_candidate_blocks().set_last_block(block_manager.get_blockchain().last_block)
        block_manager.set_peer_type(peer_type)

        if self.__tx_process is not None:

            self.__tx_process_connect_to_leader(self.__tx_process, peer_leader.target)

    def show_peers(self, channel_name):
        logging.debug(f"peer_service:show_peers ({channel_name}): ")
        for peer in self.__channel_manager.get_peer_manager(channel_name).get_IP_of_peers_in_group():
            logging.debug("peer_target: " + peer)

    def service_stop(self):
        self.__channel_manager.stop_block_managers()
        self.__common_service.stop()

    def glogic_invoke(self, block, channel) -> dict:
        block_object = pickle.dumps(block)
        response = self.channel_manager.get_glogic_container_stub(channel).call(
            method_name="Request",
            message=gbrick_pb2.Message(code=define_code.Request.glogic_invoke, object=block_object),
            timeout=Define.GLOGIC_INVOKE_TIMEOUT,
            is_raise=True
        )
        # logging.debug("glogic Server says: " + str(response))
        if response.code == define_code.Response.success:
            return json.loads(response.meta)

    def __connect_to_all_channel(self) -> bool:
        """connect to gnc with all channel

        :return: is gnc connected
        """
        response = self.__get_channel_infos()
        is_gnc_connected = response is not None

        if is_gnc_connected:
            logging.info(f"Connect to channels({response.channel_infos})")
            channels = json.loads(response.channel_infos)
            glogic_container_port_diff = 0

            for channel in list(channels.keys()):
                logging.debug(f"Try join channel({channel})")
                self.__channel_manager.load_block_manager(peer_id=self.peer_id, channel=channel)
                self.__channel_manager.load_peer_manager(channel=channel)

                is_glogic_container_loaded = self.__channel_manager.load_glogic_container_each(
                    channel_name=channel,
                    glogic_package=channels[channel]["glogic_package"],
                    container_port=self.__peer_port + Define.PORT_DIFF_GLOGIC_CONTAINER + glogic_container_port_diff,
                    peer_target=self.__peer_target)

                if is_glogic_container_loaded is False:
                    util.exit_and_msg(f"peer_service:__connect_to_all_channel glogic container load Fail ({channel})")

                glogic_container_port_diff = glogic_container_port_diff + Define.PORT_DIFF_BETWEEN_GLOGIC_CONTAINER
                response = self.connect_to_gnc(channel=channel)
                if response is not None:
                    self.__channel_manager.save_peer_manager(
                        self.__channel_manager.get_peer_manager(channel),
                        channel
                    )

        return is_gnc_connected

    def __get_channel_infos(self):
        response = self.stub_to_gnc.call_in_times(
            method_name="GetChannelInfos",
            message=gbrick_pb2.GetChannelInfosRequest(
                peer_id=self.__peer_id,
                peer_target=self.__peer_target,
                group_id=self.group_id,
                cert=self.__auth.get_public_der()),
            retry_times=Define.CONNECTION_RETRY_TIMES_TO_RS,
            is_stub_reuse=True,
            timeout=Define.CONNECTION_TIMEOUT_TO_RS
        )

        return response

    def connect_to_gnc(self, channel: str, is_reconnect: bool=False) -> gbrick_pb2.ConnectPeerReply:

        logging.debug(f"try to connect to gnc channel({channel})")

        if self.stub_to_gnc is None:
            logging.warning("fail make stub to GNC!!")
            return None

        response = self.stub_to_gnc.call_in_times(
            method_name="ConnectPeer",
            message=gbrick_pb2.ConnectPeerRequest(
                channel=channel,
                peer_object=b'',
                peer_id=self.__peer_id,
                peer_target=self.__peer_target,
                group_id=self.group_id,
                cert=self.__auth.get_public_der()),
            retry_times=Define.CONNECTION_RETRY_TIMES_TO_RS,
            is_stub_reuse=True,
            timeout=Define.CONNECTION_TIMEOUT_TO_RS
        )

        if not is_reconnect:
            if response is not None and response.status == define_code.Response.success:
                peer_list_data = pickle.loads(response.peer_list)
                self.__channel_manager.get_peer_manager(channel).load(peer_list_data, False)
                logging.debug("peer list update: " +
                              self.__channel_manager.get_peer_manager(channel).get_peers_for_debug())
            else:
                logging.debug("using local peer list: " +
                              self.__channel_manager.get_peer_manager(channel).get_peers_for_debug())

        return response

    def add_unconfirm_block(self, block_unloaded, channel_name=None):
        if channel_name is None:
            channel_name = Define.GBRICK_DEFAULT_CHANNEL

        block = pickle.loads(block_unloaded)
        block_hash = block.block_hash

        response_code, response_msg = define_code.get_response(define_code.Response.fail_validate_block)

        # block 검증
        block_is_validated = False
        try:
            block_is_validated = Block.validate(block)
        except Exception as e:
            logging.error(e)

        if block_is_validated:
            confirmed, reason = \
                self.__channel_manager.get_block_manager(channel_name).get_blockchain().add_unconfirm_block(block)

            if confirmed:
                response_code, response_msg = define_code.get_response(define_code.Response.success_validate_block)
            elif reason == "block_height":

                self.__channel_manager.get_block_manager(channel_name).block_height_sync()

        return response_code, response_msg, block_hash

    def __tx_process_connect_to_leader(self, peer_process, leader_target):
        logging.debug("try... Peer Process connect_to_leader: " + leader_target)
        logging.debug("peer_process: " + str(peer_process))
        peer_process.send_to_process((Define.BC_CONNECT_TO_LEADER_COMMAND, leader_target))
        peer_process.send_to_process((Define.BC_SUBSCRIBE_COMMAND, leader_target))

    def __run_tx_process(self, inner_channel_info):
        tx_process = BroadcastProcess("Tx Process")
        tx_process.start()
        tx_process.send_to_process(("status", ""))

        wait_times = 0
        wait_for_process_start = None


        while wait_for_process_start is None:
            sleep(Define.SLEEP_SECONDS_FOR_SUB_PROCESS_START)
            logging.debug(f"wait start tx process....")
            wait_for_process_start = tx_process.get_receive("status")

            if wait_for_process_start is None and wait_times > Define.WAIT_SUB_PROCESS_RETRY_TIMES:
                util.exit_and_msg("Tx Process start Fail!")

        logging.debug(f"Tx Process start({wait_for_process_start})")
        tx_process.send_to_process((Define.BC_MAKE_SELF_PEER_CONNECTION_COMMAND, inner_channel_info))

        return tx_process

    def __stop_tx_process(self):
        if self.__tx_process is not None:
            self.__tx_process.stop()
            self.__tx_process.wait()

    def reset_voter_count(self):
        """peer_list

        :return:
        """
        # if self.__reset_voter_in_progress is not True:
        #     self.__reset_voter_in_progress = True
        #     logging.debug("reset voter count before: " +
        #                   str(ObjectManager().peer_service.peer_manager.get_peer_count()))
        #
        #     # TODO
        #     self.__channel_manager.get_peer_manager(
        #         Define.GBRICK_DEFAULT_CHANNEL).reset_peers(None, self.__common_service.remove_audience)
        #     logging.debug("reset voter count after: " +
        #                   str(ObjectManager().peer_service.peer_manager.get_peer_count()))
        #     self.__reset_voter_in_progress = False
        pass

    def set_chain_code(self, glogic):
        """glogic를 패스로 전달하지 않고 (serve(...)의 glogic 는 glogic 의 파일 Path 이다.)
        Object 를 직접 할당하기 위한 인터페이스로 serve 호출전에 지정되어야 한다.

        :param glogic: glogic Object
        """
        # TODO
        self.__glogic = glogic
        self.__glogic_info = dict()
        self.__glogic_info[define_code.MetaParams.GlogicInfo.glogic_id] = self.__glogic.id()
        self.__glogic_info[define_code.MetaParams.GlogicInfo.glogic_version] = self.__glogic.version()

    def __port_init(self, port):
        # service reset
        self.__peer_target = util.get_private_ip() + ":" + str(port)
        self.__inner_target = Define.IP_LOCAL + ":" + str(port)
        self.__peer_port = int(port)

        # glogic Service check Using Port
        # check Port Using
        if util.check_port_using(Define.IP_PEER, int(port)+Define.PORT_DIFF_GLOGIC_CONTAINER):
            util.exit_and_msg('glogic Service Port is Using '+str(int(port)+Define.PORT_DIFF_GLOGIC_CONTAINER))

    def __run_inner_services(self, port):
        if Define.ENABLE_REST_SERVICE:
            logging.debug(f'Launch Flask RESTful server. Port = {port}')
            self.__rest_service = RestService(int(port))

    def __make_peer_id(self):
        """
        identification uuid
        """
        try:
            uuid_bytes = bytes(self.__level_db.Get(Define.LEVEL_DB_KEY_FOR_PEER_ID))
            peer_id = uuid.UUID(bytes=uuid_bytes)
        except KeyError:  # It's first Run
            peer_id = None

        if peer_id is None:
            peer_id = uuid.uuid1()
            logging.info("make new peer_id: " + str(peer_id))
            self.__level_db.Put(Define.LEVEL_DB_KEY_FOR_PEER_ID, peer_id.bytes)

        self.__peer_id = str(peer_id)

    def timer_test_callback_function(self, message):
        logging.debug(f'timer test callback function :: ({message})')

    def __block_height_sync_channel(self, channel_name):

        block_sync_target_stub = None
        peer_manager = self.__channel_manager.get_peer_manager(channel_name)
        peer_leader = peer_manager.get_leader_peer()
        self_peer_object = peer_manager.get_peer(self.__peer_id)
        is_delay_announce_new_leader = False
        peer_old_leader = None

        if peer_leader.target != self.__peer_target:
            block_sync_target_stub = StubManager.get_stub_manager_to_server(
                peer_leader.target,
                gbrick_pb2_grpc.PeerServiceStub,
                time_out_seconds=Define.CONNECTION_RETRY_TIMEOUT
            )

            if block_sync_target_stub is None:
                logging.warning("You maybe Older from this network... or No leader in this network!")

                # TODO
                is_delay_announce_new_leader = True
                peer_old_leader = peer_leader
                peer_leader = self.__channel_manager.get_peer_manager(
                    channel_name).leader_complain_to_rs(Define.ALL_GROUP_ID, is_announce_new_peer=False)

                if peer_leader is not None:
                    block_sync_target_stub = StubManager.get_stub_manager_to_server(
                        peer_leader.target,
                        gbrick_pb2_grpc.PeerServiceStub,
                        time_out_seconds=Define.CONNECTION_RETRY_TIMEOUT
                    )

            if peer_leader is None or peer_leader.peer_id == self.__peer_id:
                peer_leader = self_peer_object
                self.__channel_manager.get_block_manager(channel_name).set_peer_type(gbrick_pb2.BLOCK_GENERATOR)
            else:
                self.__channel_manager.get_block_manager(channel_name).block_height_sync(block_sync_target_stub)
                # # TODO
                # last_block_peer_id = self.__channel_manager.get_block_manager().get_blockchain().last_block.peer_id
                #
                # if last_block_peer_id != "" and last_block_peer_id != self.__peer_list.get_leader_peer().peer_id:
                #     logging.debug("make leader stub after block height sync...")
                #     new_leader_peer = self.__peer_list.get_peer(last_block_peer_id)
                #
                #     if new_leader_peer is None:
                #         new_leader_peer = self.__peer_list.leader_complain_to_rs(Define.ALL_GROUP_ID)
                #
                #     self.__peer_list.set_leader_peer(new_leader_peer, None)
                #
                #     peer_leader = new_leader_peer
                # else:

                if block_sync_target_stub is None:
                    util.exit_and_msg("Fail connect to leader!!")

                self.show_peers(channel_name)

            if block_sync_target_stub is not None:
                self.__common_service.subscribe(channel_name, block_sync_target_stub, gbrick_pb2.BLOCK_GENERATOR)

            if is_delay_announce_new_leader:
                self.__channel_manager.get_peer_manager(
                    channel_name).announce_new_leader(peer_old_leader.peer_id, peer_leader.peer_id)

    def __start_base_services(self, glogic):
        """start base services >> common_service, channel_manager, tx_process

        :param glogic:
        :return:
        """
        inner_service_port = Define.PORT_INNER_SERVICE or (self.__peer_port + Define.PORT_DIFF_INNER_SERVICE)

        self.__common_service = CommonService(gbrick_pb2, inner_service_port)

        self.__channel_manager = ChannelManager(
            common_service=self.__common_service,
            level_db_identity=self.__peer_target
        )

        self.__tx_process = self.__run_tx_process(
            inner_channel_info=Define.IP_LOCAL + ":" + str(inner_service_port)
        )

    def serve(self, port, glogic=None):
        """start func of Peer Service ===================================================================

        :param port:
        :param glogic:
        """
        if glogic is None:
            glogic = Define.DEFAULT_GLOGIC_PACKAGE

        stopwatch_start = timeit.default_timer()
        peer_type = gbrick_pb2.PEER

        is_all_service_safe_start = True

        self.__port_init(port)
        self.__level_db, self.__level_db_path = util.init_level_db(self.__peer_target)
        self.__make_peer_id()
        self.__run_inner_services(port)
        self.__start_base_services(glogic=glogic)

        is_gnc_connected = self.__connect_to_all_channel()

        if is_gnc_connected is False:
            util.exit_and_msg("There is no peer_list, initial network is not allowed without RS!")

        # # start timer service.
        # if Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.lft:
        #     self.__timer_service.start()

        # TODO GBRICK-61
        _cert = None
        # TODO GBRICK-61 key load
        _private_key = None


        for channel in self.__channel_manager.get_channel_list():
            peer_leader = self.__channel_manager.get_peer_manager(channel).get_leader_peer(is_complain_to_rs=True)
            logging.debug(f"channel({channel}) peer_leader: " + str(peer_leader))

            # TODO
            if self.__peer_id == peer_leader.peer_id:
                if is_gnc_connected is True or self.__channel_manager.get_peer_manager(
                        channel).get_connected_peer_count(None) == 1:
                    util.change_log_color_set(True)
                    logging.debug(f"Set Peer Type Leader! channel({channel})")
                    peer_type = gbrick_pb2.BLOCK_GENERATOR

            # load glogic is glogic service start after    block height sync
            # is_all_service_safe_start &= self.__load_glogic(glogic)

            if peer_type == gbrick_pb2.BLOCK_GENERATOR:
                self.__channel_manager.get_block_manager(channel).set_peer_type(peer_type)
            elif peer_type == gbrick_pb2.PEER:
                self.__block_height_sync_channel(channel)

            # if Define.CONSENSUS_ALGORITHM == Define.ConsensusAlgorithm.llfc:
            #     self.__common_service.update_audience(self.channel_manager.get_peer_manager().dump())

        gbrick_pb2_grpc.add_PeerServiceServicer_to_server(self.__outer_service, self.__common_service.outer_server)
        gbrick_pb2_grpc.add_InnerServiceServicer_to_server(self.__inner_service, self.__common_service.inner_server)
        logging.info("Start peer service at port: " + str(port))

        self.__channel_manager.start_block_managers()
        self.__common_service.start(port, self.__peer_id, self.__group_id)

        if self.stub_to_gnc is not None:
            for channel in self.__channel_manager.get_channel_list():
                self.__common_service.subscribe(
                    channel=channel,
                    subscribe_stub=self.stub_to_gnc
                )

        for channel in self.__channel_manager.get_channel_list():
            channel_leader = self.__channel_manager.get_peer_manager(channel).get_leader_peer()
            if channel_leader is not None:
                util.logger.spam(f"connnect to channel({channel}) leader({channel_leader.target})")
                self.__tx_process_connect_to_leader(self.__tx_process, channel_leader.target)

        self.__send_to_process_thread.set_process(self.__tx_process)
        self.__send_to_process_thread.start()

        stopwatch_duration = timeit.default_timer() - stopwatch_start
        logging.info(f"Start Peer Service start duration({stopwatch_duration})")

        # service
        if is_all_service_safe_start:
            self.__common_service.wait()
        else:
            self.service_stop()

        self.__send_to_process_thread.stop()
        self.__send_to_process_thread.wait()

        # if self.__timer_service.is_run():
        #     self.__timer_service.stop()
        #     self.__timer_service.wait()

        logging.info("Peer Service Ended.")
        self.__channel_manager.stop_glogic_containers()
        if self.__rest_service is not None:
            self.__rest_service.stop()
        self.__stop_tx_process()
