'''
name            : gbrick::common_service.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180205
date_modified   : 20180711
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging
import queue
import time
from concurrent import futures

import grpc

from gbrick import utils as util
from gbrick import define as Define
from gbrick.base import BroadcastProcess, CommonThread, ObjectManager
from gbrick.utils import define_code

# gbrick_pb2 not import pickle error
import gbrick_pb2


class CommonService(CommonThread):
    """Manage common part of 'Peer' and 'Gbrick Network Contriller' especially broadcast service"""

    def __init__(self, gRPC_module, inner_service_port=None):
        self.__peer_id = None if ObjectManager().peer_service is None else ObjectManager().peer_service.peer_id

        # for peer_service, it refers to peer_inner_service / for rs_service, it refers to rs_admin_service
        self.inner_server = grpc.server(futures.ThreadPoolExecutor(max_workers=Define.MAX_WORKERS))
        self.outer_server = grpc.server(futures.ThreadPoolExecutor(max_workers=Define.MAX_WORKERS))

        # members for private, It helps simplicity of code intelligence
        self.__gRPC_module = gRPC_module
        self.__port = 0
        self.__inner_service_port = inner_service_port
        self.__peer_target = None
        if inner_service_port is not None:  # It means this is Peer's CommonService not RS.
            peer_port = inner_service_port - Define.PORT_DIFF_INNER_SERVICE
            self.__peer_target = util.get_private_ip() + ":" + str(peer_port)
        self.__subscriptions = queue.Queue()  # tuple with (channel, stub)
        self.__group_id = ""

        # broadcast process
        self.__broadcast_process = self.__run_broadcast_process()

        self.__loop_functions = []

    @property
    def broadcast_process(self):
        return self.__broadcast_process

    def getstatus(self, block_manager):
        """Get Status of Blockchain

        :param block_manager:
        :return:
        """
        logging.debug("CommonService.getstatus")

        block_height = 0
        total_tx = 0

        status_data = dict()

        if block_manager is not None:
            status_data["made_block_count"] = block_manager.get_blockchain().made_block_count
            if block_manager.get_blockchain().last_block is not None:
                block_height = block_manager.get_blockchain().last_block.height
                logging.debug("getstatus block hash(block_manager.get_blockchain().last_block.block_hash): "
                              + str(block_manager.get_blockchain().last_block.block_hash))
                logging.debug("getstatus block hash(block_manager.get_blockchain().block_height): "
                              + str(block_manager.get_blockchain().block_height))
                logging.debug("getstatus block height: " + str(block_height))
                # Score와 상관없이 TransactionTx는 블럭매니저가 관리 합니다.
                total_tx = block_manager.get_total_tx()

            status_data["status"] = "Service is online: " + str(block_manager.peer_type)
            status_data["peer_type"] = str(block_manager.peer_type)
        else:
            status_data["status"] = "Service is online: 2"
            status_data["peer_type"] = "2"

        # TODO Not use anymore, It will be deleted after update REST API
        status_data["audience_count"] = "0"

        status_data["consensus"] = str(Define.CONSENSUS_ALGORITHM.name)
        status_data["peer_id"] = str(self.__peer_id)
        status_data["block_height"] = block_height
        status_data["total_tx"] = total_tx
        status_data["peer_target"] = self.__peer_target
        if ObjectManager().peer_service is not None:
            # TODO The tx service is not used anymore. The code below should be rewirtten to fit the intent
            # status_data["leader_complaint"] = ObjectManager().peer_service.tx_service.peer_status.value
            status_data["leader_complaint"] = 1

        return status_data

    def __run_broadcast_process(self):
        broadcast_process = BroadcastProcess()
        broadcast_process.start()
        broadcast_process.send_to_process(("status", ""))

        wait_times = 0
        wait_for_process_start = None

        # TODO 
        # time.sleep(Define.WAIT_SECONDS_FOR_SUB_PROCESS_START)

        while wait_for_process_start is None:
            time.sleep(Define.SLEEP_SECONDS_FOR_SUB_PROCESS_START)
            logging.debug(f"wait start broadcast process....")
            wait_for_process_start = broadcast_process.get_receive("status")

            if wait_for_process_start is None and wait_times > Define.WAIT_SUB_PROCESS_RETRY_TIMES:
                util.exit_and_msg("Broadcast Process start Fail!")

        logging.debug(f"Broadcast Process start({wait_for_process_start})")

        if self.__peer_target is not None:
            broadcast_process.send_to_process(
                (Define.BC_MAKE_SELF_PEER_CONNECTION_COMMAND, self.__peer_target))

        return broadcast_process

    def __stop_broadcast_process(self):
        self.__broadcast_process.stop()
        self.__broadcast_process.wait()

    def __subscribe(self, channel, port, subscribe_stub, is_unsubscribe=False):
        # self.__peer_target = util.get_private_ip() + ":" + str(port)
        # logging.debug("peer_info: " + self.__peer_target)
        # logging.debug("subscribe_stub type: " + str(subscribe_stub.stub.__module__))

        # Subscribe does not use the type data of the peer, but it is a required value of the PeerRequest and allocates any type information.
        subscribe_peer_type = gbrick_pb2.PEER

        try:
            if is_unsubscribe:
                subscribe_stub.call(
                    "UnSubscribe",
                    self.__gRPC_module.PeerRequest(
                        channel=channel,
                        peer_target=self.__peer_target, peer_type=subscribe_peer_type,
                        peer_id=self.__peer_id, group_id=self.__group_id
                    ),
                    is_stub_reuse=True
                )
            else:
                subscribe_stub.call(
                    "Subscribe",
                    self.__gRPC_module.PeerRequest(
                        channel=channel,
                        peer_target=self.__peer_target, peer_type=subscribe_peer_type,
                        peer_id=self.__peer_id, group_id=self.__group_id
                    ),
                    is_stub_reuse=True
                )

            logging.info(("Subscribe", "UnSubscribe")[is_unsubscribe])
        except Exception as e:
            logging.info("gRPC Exception: " + type(e).__name__)
            logging.error("Fail " + ("Subscribe", "UnSubscribe")[is_unsubscribe])

    def __un_subscribe(self, channel, port, subscribe_stub):
        self.__subscribe(channel, port, subscribe_stub, True)

    def add_audience(self, peer_info):
        """Register the Peer that to receive the broadcast
        :param peer_info: SubscribeRequest
        """
        # prevent to show certificate content
        # logging.debug("Try add audience: " + str(peer_info))
        if ObjectManager().peer_service is not None:
            ObjectManager().peer_service.tx_process.send_to_process(
                (Define.BC_SUBSCRIBE_COMMAND, peer_info.peer_target))
        self.__broadcast_process.send_to_process((Define.BC_SUBSCRIBE_COMMAND, peer_info.peer_target))

    def remove_audience(self, peer_id, peer_target):
        logging.debug("Try remove audience: " + str(peer_target))
        if ObjectManager().peer_service is not None:
            ObjectManager().peer_service.tx_process.send_to_process((Define.BC_UNSUBSCRIBE_COMMAND, peer_target))
        self.__broadcast_process.send_to_process((Define.BC_UNSUBSCRIBE_COMMAND, peer_target))

    def update_audience(self, peer_manager_dump):
        self.__broadcast_process.send_to_process((Define.BC_UPDATE_AUDIENCE_COMMAND, peer_manager_dump))

    def broadcast(self, method_name, method_param, response_handler=None):
        """Call with same parameters to the same gRPC method of all registered peers
        """
        # logging.warning("broadcast in process ==========================")
        self.__broadcast_process.send_to_process((Define.BC_BROADCAST_COMMAND, (method_name, method_param)))

    def broadcast_audience_set(self):
        self.__broadcast_process.send_to_process((Define.BC_STATUS_COMMAND, "audience set"))

    def start(self, port, peer_id="", group_id=""):
        self.__port = port
        if self.__inner_service_port is None:
            self.__inner_service_port = port + Define.PORT_DIFF_INNER_SERVICE
        self.__peer_id = peer_id
        self.__group_id = group_id
        CommonThread.start(self)
        self.__broadcast_process.set_to_process(Define.BC_PROCESS_INFO_KEY, f"peer_id({self.__peer_id})")

    def subscribe(self, channel, subscribe_stub, peer_type=None):
        if subscribe_stub is None:
            util.logger.spam(f"common_service:subscribe subscribe_stub is None!")
            return

        self.__subscribe(channel=channel, port=self.__port, subscribe_stub=subscribe_stub)
        self.__subscriptions.put((channel, subscribe_stub))

        if peer_type == gbrick_pb2.BLOCK_GENERATOR or peer_type == gbrick_pb2.PEER:
            # for boradcasting transaction, add it to audience if peer is leader
            self.__broadcast_process.send_to_process((Define.BC_SUBSCRIBE_COMMAND, subscribe_stub.target))

    def vote_unconfirmed_block(self, block_hash, is_validated, channel):
        logging.debug(f"vote_unconfirmed_block ({channel})")

        if is_validated:
            vote_code, message = define_code.get_response(define_code.Response.success_validate_block)
        else:
            vote_code, message = define_code.get_response(define_code.Response.fail_validate_block)

        block_vote = gbrick_pb2.BlockVote(
            vote_code=vote_code,
            channel=channel,
            message=message,
            block_hash=block_hash,
            peer_id=self.__peer_id,
            group_id=ObjectManager().peer_service.group_id)

        self.broadcast("VoteUnconfirmedBlock", block_vote)

    def start_server(self, server, listen_address):
        server.add_insecure_port(listen_address)
        server.start()
        logging.info("Server now listen: " + listen_address)

    def add_loop(self, loop_function):
        self.__loop_functions.append(loop_function)

    def __run_loop_functions(self):
        for loop_function in self.__loop_functions:
            loop_function()

    def run(self):
        self.start_server(self.outer_server, '[::]:' + str(self.__port))
        # Bind Only loopback address (ip4) - TODO IP6
        self.start_server(self.inner_server, Define.INNER_SERVER_BIND_IP + ':' + str(self.__inner_service_port))

        # When subscribing the Block Generator, the Block Generator requests the peer to create channel
        # Therefore, after the peer's gRPC server is completely started, it should send a subscribe request to the Block Generator.
        time.sleep(Define.WAIT_GRPC_SERVICE_START)

        try:
            while self.is_run():
                self.__run_loop_functions()
                time.sleep(Define.SLEEP_SECONDS_IN_SERVICE_NONE)
        except KeyboardInterrupt:
            logging.info("Server Stop by KeyboardInterrupt")
        finally:
            while not self.__subscriptions.empty():
                channel, subscribe_stub = self.__subscriptions.get()
                logging.info(f"Un subscribe to channel({channel}) server({subscribe_stub.target})")
                self.__un_subscribe(channel, self.__port, subscribe_stub)

            self.__stop_broadcast_process()

            if self.__inner_service_port is not None:
                self.inner_server.stop(0)
            self.outer_server.stop(0)

        logging.info("Server thread Ended.")
