'''
name            : gbrick::gnc_outer_service.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180215
date_modified   : 20180720
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import json
import logging
import pickle

from gbrick import utils as util
from gbrick import define as Define
from gbrick.base import ObjectManager,PeerStatus, PeerInfo
from gbrick.protos import gbrick_pb2_grpc
from gbrick.utils import define_code

import gbrick_pb2 as gbrick__pb2


class OuterService(gbrick_pb2_grpc.GNControllerServicer):

    def __init__(self):
        self.__handler_map = {
            define_code.Request.status: self.__handler_status,
            define_code.Request.peer_get_leader: self.__handler_get_leader_peer,
            define_code.Request.peer_complain_leader: self.__handler_complain_leader,
            define_code.Request.rs_set_configuration: self.__handler_set_configuration,
            define_code.Request.rs_get_configuration: self.__handler_get_configuration
        }

    def __handler_status(self, request, context):
        return gbrick__pb2.Message(code=define_code.Response.success)

    def __handler_get_leader_peer(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if not request.channel else request.channel
        leader_peer = ObjectManager().rs_service.channel_manager.get_peer_manager(
            channel_name).get_leader_peer(group_id=request.message, is_peer=False)
        if leader_peer is not None:
            logging.debug(f"leader_peer ({leader_peer.peer_id})")
            peer_dump = pickle.dumps(leader_peer)

            return gbrick__pb2.Message(code=define_code.Response.success, object=peer_dump)

        return gbrick__pb2.Message(code=define_code.Response.fail_no_leader_peer)

    def __handler_complain_leader(self, request, context):

        logging.debug("in complain leader (GNC)")
        leader_peer = ObjectManager().rs_service.channel_manager.get_peer_manager(
            Define.GBRICK_DEFAULT_CHANNEL).complain_leader(group_id=request.message)
        if leader_peer is not None:
            logging.warning(f"leader_peer after complain({leader_peer.peer_id})")
            peer_dump = pickle.dumps(leader_peer)
            return gbrick__pb2.Message(code=define_code.Response.success, object=peer_dump)

        return gbrick__pb2.Message(code=define_code.Response.fail_no_leader_peer)

    def __handler_get_configuration(self, request, context):

        if request.meta == '':
            result = Define.get_all_configurations()
        else:
            meta = json.loads(request.meta)
            conf_name = meta['name']
            result = Define.get_configuration(conf_name)

        if result is None:
            return gbrick__pb2.Message(
                code=define_code.Response.fail,
                message="'" + conf_name + "' is an incorrect configuration name."
            )
        else:
            json_result = json.dumps(result)
            return gbrick__pb2.Message(
                code=define_code.Response.success,
                meta=json_result
            )

    def __handler_set_configuration(self, request, context):

        meta = json.loads(request.meta)

        if Define.set_configuration(meta['name'], meta['value']):
            return gbrick__pb2.Message(code=define_code.Response.success)
        else:
            return gbrick__pb2.Message(
                code=define_code.Response.fail,
                message='"' + meta['name'] + '" does not exist in the gbrick configuration list.'
            )

    def Request(self, request, context):
        logging.debug("GNControllerService got request: " + str(request))

        if request.code in self.__handler_map.keys():
            return self.__handler_map[request.code](request, context)

        return gbrick__pb2.Message(code=define_code.Response.not_treat_message_code)

    def GetStatus(self, request, context):

        logging.debug("GNC GetStatus : %s", request)
        peer_status = ObjectManager().rs_service.common_service.getstatus(None)
        return gbrick__pb2.StatusReply(
            status=json.dumps(peer_status),
            block_height=peer_status["block_height"],
            total_tx=peer_status["total_tx"])

    def Stop(self, request, context):
        logging.info('GNC will stop... by: ' + request.reason)
        ObjectManager().rs_service.common_service.stop()
        return gbrick__pb2.StopReply(status="0")

    def GetChannelInfos(self, request: gbrick__pb2.GetChannelInfosRequest, context):
        channel_infos: str = \
            ObjectManager().rs_service.admin_manager.get_channel_infos_by_peer_target(request.peer_target)

        return gbrick__pb2.GetChannelInfosReply(
            response_code=define_code.Response.success,
            channel_infos=channel_infos
        )

    def ConnectPeer(self, request: gbrick__pb2.ConnectPeerRequest, context):
        logging.info("Trying to connect peer: "+request.peer_id)

        res, info = ObjectManager().rs_service.validate_group_id(request.group_id)
        if res < 0:  # send null list(b'') while wrong input.
            return gbrick__pb2.ConnectPeerReply(status=define_code.Response.fail, peer_list=b'', more_info=info)

        # TODO check peer's authorization for channel
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if not request.channel else request.channel
        logging.debug(f"ConnectPeer channel_name({channel_name})")
        logging.debug("Connect Peer "
                      + "\nPeer_id : " + request.peer_id
                      + "\nGroup_id : " + request.group_id
                      + "\nPeer_target : " + request.peer_target)

        peer = PeerInfo(request.peer_id, request.group_id, request.peer_target, PeerStatus.unknown, cert=request.cert)

        util.logger.spam(f"service::ConnectPeer try add_peer")
        peer_order = ObjectManager().rs_service.channel_manager.get_peer_manager(channel_name).add_peer(peer)

        peer_list_dump = b''
        status, reason = define_code.get_response(define_code.Response.fail)

        if peer_order > 0:
            try:
                peer_list_dump = ObjectManager().rs_service.channel_manager.get_peer_manager(channel_name).dump()
                status, reason = define_code.get_response(define_code.Response.success)

            except pickle.PicklingError as e:
                logging.warning("fail peer_list dump")
                reason += " " + str(e)

        return gbrick__pb2.ConnectPeerReply(
            status=status,
            peer_list=peer_list_dump,
            channels=None,
            more_info=reason
        )

    def GetPeerList(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if not request.channel else request.channel
        try:
            peer_list_dump = ObjectManager().rs_service.channel_manager.get_peer_manager(channel_name).dump()
        except pickle.PicklingError as e:
            logging.warning("fail peer_list dump")
            peer_list_dump = b''

        return gbrick__pb2.PeerList(
            peer_list=peer_list_dump
        )

    def GetPeerStatus(self, request, context):
        # request parsing
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if not request.channel else request.channel
        logging.debug(f"rs service GetPeerStatus peer_id({request.peer_id}) group_id({request.group_id})")

        # get stub of target peer
        peer_stub_manager = ObjectManager().rs_service.channel_manager.get_peer_manager(
            channel_name).get_peer_stub_manager(
            ObjectManager().rs_service.channel_manager.get_peer_manager(channel_name).get_peer(request.peer_id))
        if peer_stub_manager is not None:
            try:
                response = peer_stub_manager.call_in_times(
                    "GetStatus",
                    gbrick__pb2.StatusRequest(request="get peer status from rs", channel=channel_name))
                if response is not None:
                    return response
            except Exception as e:
                logging.warning(f"fail GetStatus... ({e})")

        return gbrick__pb2.StatusReply(status=define_code.get_response_msg(
            define_code.Response.fail), block_height=0, total_tx=0)

    def AnnounceNewLeader(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel

        new_leader_peer = ObjectManager().rs_service.channel_manager.get_peer_manager(
            channel_name).get_peer(request.new_leader_id, None)

        if new_leader_peer is None:
            logging.warning(f"GNC Has No live Peer Connection(candidate reason is RS's restart)")
            logging.warning(f"GNC Request to Peers make Re-Connection")

            return gbrick__pb2.CommonReply(response_code=define_code.Response.fail_no_peer_info_in_rs,
                                           message=define_code.get_response_msg(
                                                 define_code.Response.fail_no_peer_info_in_rs))
        else:
            logging.debug(f"AnnounceNewLeader({channel_name}) "
                          f"id({request.new_leader_id}) "
                          f"target({new_leader_peer.target}): " + request.message)

            ObjectManager().rs_service.channel_manager.get_peer_manager(
                channel_name).set_leader_peer(peer=new_leader_peer, group_id=None)

            return gbrick__pb2.CommonReply(response_code=define_code.Response.success, message="success")

    def GetRandomTable(self, request, context):
        if Define.ENABLE_KMS:
            try:
                serialized_table = json.dumps(ObjectManager().rs_service.random_table)
                return gbrick__pb2.CommonReply(response_code=define_code.Response.success, message=serialized_table)
            except Exception as e:
                logging.error(f"random table serialize fail \n"
                              f"cause {e}")
                return gbrick__pb2.CommonReply(response_code=define_code.Response.fail,
                                               messsage="random_table serialize fail")
        else:
            return gbrick__pb2.CommonReply(response_code=define_code.Response.fail,
                                           messsage="GNC KMS Policy is not enable")

    def Subscribe(self, request, context):

        channel = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug("GNC Subscription peer_id: " + str(request))
        ObjectManager().rs_service.common_service.add_audience(request)

        peer = ObjectManager().rs_service.channel_manager.get_peer_manager(channel).update_peer_status(
            peer_id=request.peer_id, peer_status=PeerStatus.connected)

        try:
            peer_dump = pickle.dumps(peer)
            request.peer_order = peer.order
            request.peer_object = peer_dump

            ObjectManager().rs_service.channel_manager.get_peer_manager(channel).announce_new_peer(request)


            return gbrick__pb2.CommonReply(
                response_code=define_code.get_response_code(define_code.Response.success),
                message=define_code.get_response_msg(define_code.Response.success))

        except pickle.PicklingError as e:
            logging.warning("Fail Peer Dump: " + str(e))
            return gbrick__pb2.CommonReply(response_code=define_code.get_response_code(define_code.Response.fail),
                                           message=define_code.get_response_msg(define_code.Response.fail))

    def UnSubscribe(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug("GNC UnSubscription peer_id: " + request.peer_target)
        ObjectManager().rs_service.channel_manager.get_peer_manager(channel_name).remove_peer(request.peer_id, request.group_id)
        ObjectManager().rs_service.common_service.remove_audience(request.peer_id, request.peer_target)
        return gbrick__pb2.CommonReply(response_code=0, message="success")

