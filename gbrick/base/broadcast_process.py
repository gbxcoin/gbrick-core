'''
name            : gbrick::broadcast_process.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180215
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''


import json
import logging
import pickle
import queue
from time import sleep
from enum import Enum

from gbrick import define as Define
from gbrick.base import ManageProcess, StubManager, PeerManager
from gbrick.protos import gbrick_pb2, gbrick_pb2_grpc
from gbrick.utils import define_code


class PeerProcessStatus(Enum):
    normal = 0
    leader_complained = 1


class TxItem:
    def __init__(self, tx_dump: bytes, channel_name: str):
        self.__tx_dump = tx_dump
        self.__channel_name = channel_name

    @property
    def tx_dump(self):
        return self.__tx_dump

    @property
    def channel_name(self):
        return self.__channel_name


class BroadcastProcess(ManageProcess):


    def __init__(self, process_name="Broadcast Process"):
        ManageProcess.__init__(self)
        self.__process_name = process_name

    def process_loop(self, manager_dic, manager_list):
        logging.info(f"({self.__process_name}) Start.")

        __audience = {}

        command = None
        stored_tx = queue.Queue()
        __process_variables = dict()
        __process_variables[Define.BC_PROCESS_VARIABLE_PEER_STATUS] = PeerProcessStatus.normal

        def __broadcast_tx(stored_tx_item: TxItem):
            result_add_tx = None

            for peer_target in list(__audience):
                stub_item = __audience[peer_target]
                stub_item.call_async(
                    "AddTx", gbrick_pb2.TxSend(
                        tx=stored_tx_item.tx_dump,
                        channel=stored_tx_item.channel_name)
                )

            return result_add_tx

        def create_tx_continue():
            while not stored_tx.empty():
                stored_tx_item = stored_tx.get()
                __broadcast_tx(stored_tx_item)

        def __broadcast_run(method_name, method_param):
            for peer_target in list(__audience):
                stub_item = __audience[peer_target]
                stub_item.call_async(method_name, method_param)

        def __handler_subscribe(subscribe_peer_target):
            if subscribe_peer_target not in __audience:
                stub_manager = StubManager.get_stub_manager_to_server(
                    subscribe_peer_target, gbrick_pb2_grpc.PeerServiceStub,
                    time_out_seconds=Define.CONNECTION_RETRY_TIMEOUT_WHEN_INITIAL,
                    is_allow_null_stub=True
                )
                __audience[subscribe_peer_target] = stub_manager

        def __handler_unsubscribe(unsubscribe_peer_target):
            try:
                del __audience[unsubscribe_peer_target]
            except KeyError:
                logging.warning("Already deleted peer: " + str(unsubscribe_peer_target))

        def __handler_update_audience(audience_param):
            peer_manager = PeerManager()
            peer_list_data = pickle.loads(audience_param)
            peer_manager.load(peer_list_data, False)

            for peer_id in list(peer_manager.peer_list[Define.ALL_GROUP_ID]):
                peer_each = peer_manager.peer_list[Define.ALL_GROUP_ID][peer_id]
                if peer_each.target != __process_variables[Define.BC_SELF_PEER_TARGET_KEY]:
                    logging.warning(f"broadcast process peer_targets({peer_each.target})")
                    __handler_subscribe(peer_each.target)

        def __handler_broadcast(broadcast_param):
            broadcast_method_name = broadcast_param[0]
            broadcast_method_param = broadcast_param[1]
            __broadcast_run(broadcast_method_name, broadcast_method_param)

        def __handler_status(status_param):
            logging.debug(f"({self.__process_name}) Status, param({status_param}) audience({len(__audience)})")

            status = dict()
            status['result'] = define_code.get_response_msg(define_code.Response.success)
            status['Audience'] = str(len(__audience))
            status_json = json.dumps(status)

            manager_dic["status"] = status_json

        def __handler_create_tx(create_tx_param):

            try:
                tx_item = TxItem(pickle.dumps(create_tx_param), create_tx_param.meta[Define.TS_CHANNEL_KEY])
            except Exception as e:
                logging.warning(f"tx in channel({create_tx_param.meta[Define.TS_CHANNEL_KEY]})")
                logging.warning(f"tx dumps fail ({e})")
                return

            if __process_variables[Define.BC_PROCESS_VARIABLE_PEER_STATUS] == PeerProcessStatus.leader_complained:
                stored_tx.put(tx_item)
                logging.warning("Leader is complained your tx just stored in queue by temporally: "
                                + str(stored_tx.qsize()))
            else:
                create_tx_continue()
                __broadcast_tx(tx_item)

        def __handler_connect_to_leader(connect_to_leader_param):
            __process_variables[Define.BC_LEADER_PEER_TARGET_KEY] = connect_to_leader_param
            __process_variables[Define.BC_PROCESS_VARIABLE_PEER_STATUS] = PeerProcessStatus.normal

        def __handler_connect_to_self_peer(connect_param):
            stub_to_self_peer = StubManager.get_stub_manager_to_server(
                connect_param, gbrick_pb2_grpc.InnerServiceStub,
                time_out_seconds=Define.CONNECTION_RETRY_TIMEOUT_WHEN_INITIAL,
                is_allow_null_stub=True
            )
            __process_variables[Define.BC_SELF_PEER_TARGET_KEY] = connect_param
            __process_variables[Define.BC_PROCESS_VARIABLE_STUB_TO_SELF_PEER] = stub_to_self_peer

        __handler_map = {
            Define.BC_CREATE_TX_COMMAND: __handler_create_tx,
            Define.BC_CONNECT_TO_LEADER_COMMAND: __handler_connect_to_leader,
            Define.BC_SUBSCRIBE_COMMAND: __handler_subscribe,
            Define.BC_UNSUBSCRIBE_COMMAND: __handler_unsubscribe,
            Define.BC_UPDATE_AUDIENCE_COMMAND: __handler_update_audience,
            Define.BC_BROADCAST_COMMAND: __handler_broadcast,
            Define.BC_MAKE_SELF_PEER_CONNECTION_COMMAND: __handler_connect_to_self_peer,
            Define.BC_STATUS_COMMAND: __handler_status
        }

        while command != ManageProcess.QUIT_COMMAND:
            try:
                if not manager_list:
                    sleep(Define.SLEEP_SECONDS_IN_SERVICE_LOOP)
                else:
                    command, param = manager_list.pop()

                    if command in __handler_map.keys():
                        __handler_map[command](param)
                        continue

                    if command == ManageProcess.QUIT_COMMAND:
                        logging.debug(f"({self.__process_name}) "
                                      f"peer({manager_dic[Define.BC_PROCESS_INFO_KEY]}) will quit soon.")
                    else:
                        logging.error(f"({self.__process_name}) received Unknown command: " +
                                      str(command) + " and param: " + str(param))
            except Exception as e:
                sleep(Define.SLEEP_SECONDS_IN_SERVICE_LOOP)
                logging.error(f"({self.__process_name}) not available reason({e})")
                break

        logging.info(f"({self.__process_name}) Ended.")
