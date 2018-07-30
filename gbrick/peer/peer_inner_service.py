
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180205
date_modified   : 20180705
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import re
import grpc

from grpc._channel import _Rendezvous

from gbrick.base import ObjectManager
from gbrick.blockchain import *
from gbrick.protos import gbrick_pb2_grpc
from gbrick.utils import define_code

# gbrick_pb2 not import pickle error
import gbrick_pb2

# if platform.system() == 'Darwin':
#     sys.path.insert(0, "/Users/hangs/Documents/source/blockchain/gbrick_coin/gbrick/protos")
#     sys.path.append('../')
#     import gbrick_pb2
# else:
#     from gbrick.proto import gbrick_pb2


class InnerService(gbrick_pb2_grpc.InnerServiceServicer):
    """insecure gRPC service for inner process modules.
    """

    def __init__(self):
        self.__handler_map = {
            define_code.Request.status: self.__handler_status,
            define_code.Request.peer_peer_list: self.__handler_peer_list
        }

    @property
    def peer_service(self):
        return ObjectManager().peer_service

    def __handler_status(self, request, context):
        return gbrick_pb2.Message(code=define_code.Response.success)

    def __handler_peer_list(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        peer_manager = self.peer_service.channel_manager.get_peer_manager(channel_name)
        message = "All Group Peers count: " + str(len(peer_manager.peer_list[Define.ALL_GROUP_ID]))

        return gbrick_pb2.Message(
            code=define_code.Response.success,
            message=message,
            meta=str(peer_manager.peer_list))

    def Request(self, request, context):
        logging.debug("Peer Service got request: " + str(request))

        if request.code in self.__handler_map.keys():
            return self.__handler_map[request.code](request, context)

        return gbrick_pb2.Message(code=define_code.Response.not_treat_message_code)

    def GetStatus(self, request, context):

        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug("Inner Channel::Peer GetStatus : %s", request)
        peer_status = self.peer_service.common_service.getstatus(
            self.peer_service.channel_manager.get_block_manager(channel_name))

        return gbrick_pb2.StatusReply(
            status=json.dumps(peer_status),
            block_height=peer_status["block_height"],
            total_tx=peer_status["total_tx"],
            is_leader_complaining=peer_status['leader_complaint'])

    def GetGlogicStatus(self, request, context):

        logging.debug("Peer GetglogicStatus request : %s", request)
        glogic_status = json.loads("{}")
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        try:
            glogic_status_response = self.peer_service.channel_manager.get_glogic_container_stub(channel_name).call(
                "Request",
                gbrick_pb2.Message(code=define_code.Request.status)
            )
            logging.debug("Get glogic Status : " + str(glogic_status_response))
            if glogic_status_response.code == define_code.Response.success:
                glogic_status = json.loads(glogic_status_response.meta)

        except Exception as e:
            logging.debug("glogic Service Already stop by other reason. %s", e)

        return gbrick_pb2.StatusReply(
            status=json.dumps(glogic_status),
            block_height=0,
            total_tx=0)

    def Stop(self, request, context):

        if request is not None:
            logging.info('Peer will stop... by: ' + request.reason)

        try:
            response = self.peer_service.channel_manager.stop_glogic_containers()
            logging.debug("try stop glogic container: " + str(response))
        except Exception as e:
            logging.debug("glogic Service Already stop by other reason. %s", e)

        self.peer_service.service_stop()
        return gbrick_pb2.StopReply(status="0")

    def Echo(self, request, context):

        return gbrick_pb2.CommonReply(response_code=define_code.Response.success,
                                      message=request.request)

    def GetBlock(self, request, context):

        # Peer To Client
        block_hash = request.block_hash
        block = None

        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        block_manager = self.peer_service.channel_manager.get_block_manager(channel_name)

        if request.block_hash == "" and request.block_height == -1:
            block_hash = block_manager.get_blockchain().last_block.block_hash

        block_filter = re.sub(r'\s', '', request.block_data_filter).split(",")
        tx_filter = re.sub(r'\s', '', request.tx_data_filter).split(",")
        logging.debug("block_filter: " + str(block_filter))
        logging.debug("tx_filter: " + str(tx_filter))

        block_data_json = json.loads("{}")

        if block_hash != "":
            block = block_manager.get_blockchain().find_block_by_hash(block_hash)
        elif request.block_height != -1:
            block = block_manager.get_blockchain().find_block_by_height(request.block_height)

        if block is None:
            return gbrick_pb2.GetBlockReply(response_code=define_code.Response.fail_wrong_block_hash,
                                            block_hash=block_hash,
                                            block_data_json="",
                                            tx_data_json="")

        for key in block_filter:
            try:
                block_data_json[key] = str(getattr(block, key))
            except AttributeError:
                try:
                    getter = getattr(block, "get_" + key)
                    block_data_json[key] = getter()
                except AttributeError:
                    block_data_json[key] = ""

        tx_data_json_list = []
        for tx in block.confirmed_transaction_list:
            tx_data_json = json.loads("{}")
            for key in tx_filter:
                try:
                    tx_data_json[key] = str(getattr(tx, key))
                except AttributeError:
                    try:
                        getter = getattr(tx, "get_" + key)
                        tx_data_json[key] = getter()
                    except AttributeError:
                        tx_data_json[key] = ""
            tx_data_json_list.append(json.dumps(tx_data_json))

        block_hash = block.block_hash
        block_data_json = json.dumps(block_data_json)

        return gbrick_pb2.GetBlockReply(response_code=define_code.Response.success,
                                        block_hash=block_hash,
                                        block_data_json=block_data_json,
                                        tx_data_json=tx_data_json_list)

    def Query(self, request, context):

        # TODO
        if util.check_is_json_string(request.params):
            logging.debug(f'Query request with {request.params}')
            try:
                response_from_glogic_service = \
                    self.peer_service.channel_manager.get_glogic_container_stub(request.channel).call(
                        method_name="Request",
                        message=gbrick_pb2.Message(code=define_code.Request.glogic_query, meta=request.params),
                        timeout=Define.GLOGIC_QUERY_TIMEOUT,
                        is_raise=True
                    )
                response = response_from_glogic_service.meta
            except Exception as e:
                logging.error(f'Execute Query Error : {e}')
                if isinstance(e, _Rendezvous):
                    # timeout
                    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                        return gbrick_pb2.QueryReply(response_code=define_code.Response.timeout_exceed,
                                                     response="")
                return gbrick_pb2.QueryReply(response_code=define_code.Response.fail,
                                             response="")
        else:
            return gbrick_pb2.QueryReply(response_code=define_code.Response.fail_validate_params,
                                         response="")

        if util.check_is_json_string(response):
            # TODO
            response_code = define_code.Response.success
        else:
            response_code = define_code.Response.fail

        return gbrick_pb2.QueryReply(response_code=response_code,
                                        response=response)

    def Subscribe(self, request, context):

        if request.peer_id == "":
            return gbrick_pb2.CommonReply(
                response_code=define_code.get_response_code(define_code.Response.fail_wrong_subscribe_info),
                message=define_code.get_response_msg(define_code.Response.fail_wrong_subscribe_info)
            )
        else:
            self.peer_service.common_service.add_audience(request)

        return gbrick_pb2.CommonReply(response_code=define_code.get_response_code(define_code.Response.success),
                                      message=define_code.get_response_msg(define_code.Response.success))

    def UnSubscribe(self, request, context):

        self.peer_service.common_service.remove_audience(request.peer_id, request.peer_target)
        return gbrick_pb2.CommonReply(response_code=0, message="success")

    def NotifyLeaderBroken(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug("NotifyLeaderBroken: " + request.request)

        ObjectManager().peer_service.rotate_next_leader(channel_name)
        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")

        # # TODO
        # # send complain leader message to new leader candidate
        # leader_peer = self.peer_service.peer_manager.get_leader_peer()
        # next_leader_peer, next_leader_peer_stub = self.peer_service.peer_manager.get_next_leader_stub_manager()
        # if next_leader_peer_stub is not None:
        #     next_leader_peer_stub.call_in_time(
        #         "ComplainLeader",
        #         gbrick_pb2.ComplainLeaderRequest(
        #             complained_leader_id=leader_peer.peer_id,
        #             new_leader_id=next_leader_peer.peer_id,
        #             message="complain leader peer")
        #     )
        #     #
        #     # next_leader_peer_stub.ComplainLeader(gbrick_pb2.ComplainLeaderRequest(
        #     #     complained_leader_id=leader_peer.peer_id,
        #     #     new_leader_id=next_leader_peer.peer_id,
        #     #     message="complain leader peer"
        #     # ), Define.GRPC_TIMEOUT)
        #
        #     return gbrick_pb2.CommonReply(response_code=message_code.Response.success, message="success")
        # else:
        #     # TODO
        #     logging.warning("There is no next leader candidate")
        #     return gbrick_pb2.CommonReply(response_code=message_code.Response.fail,
        #                                      message="fail found next leader stub")

    def NotifyProcessError(self, request, context):
        """Peer Stop by Process Error
        """
        util.exit_and_msg(request.request)
        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")
