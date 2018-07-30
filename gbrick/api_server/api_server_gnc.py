
'''
name            : gbrick::api_server_gnc.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180205
date_modified   : 20180620

version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import base64
import json
import logging
import pickle

from flask import Flask, request
from flask_restful import reqparse, Api, Resource
from flask_restful.utils import cors

import gbrick.define as Define
from gbrick.base import CommonThread, StubManager, PeerManager, PeerStatus
from gbrick.components import SingletonMetaClass
from gbrick.protos import gbrick_pb2, gbrick_pb2_grpc
from gbrick.utils import define_code


class ServerComponents(metaclass=SingletonMetaClass):
    def __init__(self):
        self.__app = Flask(__name__)
        self.__api = Api(self.__app)
        self.__api.decorators = [cors.crossdomain(origin='*', headers=['accept', 'Content-Type'])]
        self.__parser = reqparse.RequestParser()
        self.__stub_to_rs_service = None
        self.__ssl_context = None

    @property
    def app(self):
        return self.__app

    @property
    def api(self):
        return self.__api

    @property
    def parser(self):
        return self.__parser

    @property
    def stub(self):
        return self.__stub_to_rs_service

    @property
    def ssl_context(self):
        return self.__ssl_context

    def set_stub_port(self, port):
        self.__stub_to_rs_service = StubManager.get_stub_manager_to_server(
            Define.IP_LOCAL + ':' + str(port), gbrick_pb2_grpc.GNControllerStub
        )

    def set_argument(self):
        self.__parser.add_argument('peer_id')
        self.__parser.add_argument('group_id')
        self.__parser.add_argument('name')
        self.__parser.add_argument('channel')

    def set_resource(self):
        self.__api.add_resource(Peer, '/api/v1/peer/<string:request_type>')
        self.__api.add_resource(Configuration, '/api/v1/conf')

    def get_peer_list(self, channel):
        return self.__stub_to_rs_service.call(
            "GetPeerList",
            gbrick_pb2.CommonRequest(request="", group_id=Define.ALL_GROUP_ID, channel=channel))

    def get_leader_peer(self, channel):
        return self.__stub_to_rs_service.call(
            "Request",
            gbrick_pb2.Message(code=define_code.Request.peer_get_leader, channel=channel))

    def get_peer_status(self, peer_id, group_id, channel):
        return self.__stub_to_rs_service.call_in_times(
            "GetPeerStatus",
            gbrick_pb2.PeerID(peer_id=peer_id, group_id=group_id, channel=channel))

    def get_configuration(self, conf_info):
        return self.__stub_to_rs_service.call(
            "Request",
            gbrick_pb2.Message(code=define_code.Request.rs_get_configuration, meta=conf_info))

    def set_configuration(self, conf_info):
        return self.__stub_to_rs_service.call(
            "Request",
            gbrick_pb2.Message(code=define_code.Request.rs_set_configuration, meta=conf_info))

    def response_simple_success(self):
        result = json.loads('{}')
        result['response_code'] = define_code.Response.success
        result['message'] = define_code.get_response_msg(define_code.Response.success)

        return result

    def abort_if_url_doesnt_exist(self, request_type, type_list):
        result = json.loads('{}')
        result['response_code'] = define_code.Response.fail

        if request_type not in type_list.values():
            result['message'] = "The resource doesn't exist"

        return result


def get_channel_name_from_args(args) -> str:
    return Define.GBRICK_DEFAULT_CHANNEL if args.get('channel') is None else args.get('channel')


class Peer(Resource):
    __REQUEST_TYPE = {
        'PEER_LIST': 'list',
        'LEADER_PEER': 'leader',
        'PEER_STATUS': 'status',
        'PEER_STATUS_LIST': 'status-list'
    }

    def get(self, request_type):
        args = ServerComponents().parser.parse_args()
        channel = get_channel_name_from_args(args)
        logging.debug(f'channel name : {channel}')
        if request_type == self.__REQUEST_TYPE['PEER_LIST']:
            response = ServerComponents().get_peer_list(channel)

            peer_manager = PeerManager()
            peer_list_data = pickle.loads(response.peer_list)
            peer_manager.load(peer_list_data, False)

            all_peer_list = []
            connected_peer_list = []

            leader_peer_id = ""
            leader_peer = peer_manager.get_leader_peer(Define.ALL_GROUP_ID, is_peer=False)  # for set peer_type info to peer
            if leader_peer is not None:
                leader_peer_id = leader_peer.peer_id
            
            for peer_id in peer_manager.peer_list[Define.ALL_GROUP_ID]:
                peer_each = peer_manager.peer_list[Define.ALL_GROUP_ID][peer_id]
                peer_data = self.__change_format_to_json(peer_each)

                if peer_each.peer_id == leader_peer_id:
                    peer_data['peer_type'] = gbrick_pb2.BLOCK_GENERATOR
                else:
                    peer_data['peer_type'] = gbrick_pb2.PEER

                all_peer_list.append(peer_data)

                if peer_each.status == PeerStatus.connected:
                    connected_peer_list.append(peer_data)

            json_data = json.loads('{}')
            json_data['registered_peer_count'] = peer_manager.get_peer_count()
            json_data['connected_peer_count'] = peer_manager.get_connected_peer_count()
            json_data['registered_peer_list'] = all_peer_list
            json_data['connected_peer_list'] = connected_peer_list

            result = json.loads('{}')
            result['response_code'] = define_code.Response.success
            result['data'] = json_data
            
        elif request_type == self.__REQUEST_TYPE['PEER_STATUS_LIST']:
            response = ServerComponents().get_peer_list(channel)

            peer_manager = PeerManager()
            peer_list_data = pickle.loads(response.peer_list)
            peer_manager.load(peer_list_data, False)

            all_peer_list = []

            for peer_id in peer_manager. peer_list[Define.ALL_GROUP_ID]:
                response = ServerComponents().get_peer_status(peer_id, Define.ALL_GROUP_ID, channel)
                if response is not None and response.status != "":
                    peer_each = peer_manager.peer_list[Define.ALL_GROUP_ID][peer_id]
                    status_json = json.loads(response.status)
                    status_json["order"] = peer_each.order
                    all_peer_list.append(status_json)

            json_data = json.loads('{}')
            json_data['registered_peer_count'] = peer_manager.get_peer_count()
            json_data['connected_peer_count'] = peer_manager.get_connected_peer_count()
            json_data['peer_status_list'] = all_peer_list

            result = json.loads('{}')
            result['response_code'] = define_code.Response.success
            result['data'] = json_data

        elif request_type == self.__REQUEST_TYPE['LEADER_PEER']:
            response = ServerComponents().get_leader_peer(channel)

            result = json.loads('{}')
            result['response_code'] = response.code

            if response.code == define_code.Response.success:
                result['data'] = self.__change_format_to_json(pickle.loads(response.object))
            else:
                result['message'] = define_code.get_response_msg(response.code)

        elif request_type == self.__REQUEST_TYPE['PEER_STATUS']:
            peer_id = args['peer_id']
            group_id = args['group_id']

            if peer_id is None or group_id is None:
                return self.__abort_if_arg_isnt_enough('peer_id, group_id')

            # logging.debug(f"try get_peer_status peer_id({peer_id}), group_id({group_id})")
            response = ServerComponents().get_peer_status(args['peer_id'], args['group_id'], channel)
            if response.status == define_code.get_response_msg(define_code.Response.fail):
                result = json.loads('{}')
                result['response_code'] = define_code.Response.fail
                result['message'] = response.status
            else:
                result = json.loads(response.status)

        else:
            return ServerComponents().abort_if_url_doesnt_exist(request_type, self.__REQUEST_TYPE)

        return result

    def __change_format_to_json(self, peer):
        json_data = json.loads('{}')
        json_data['order'] = peer.order
        json_data['peer_id'] = peer.peer_id
        json_data['group_id'] = peer.group_id
        json_data['target'] = peer.target
        json_data['cert'] = base64.b64encode(peer.cert).decode("utf-8")
        json_data['status_update_time'] = str(peer.status_update_time)
        json_data['status'] = peer.status

        return json_data

    def __abort_if_arg_isnt_enough(self, param_name):
        result = json.loads('{}')
        result['response_code'] = define_code.Response.fail_validate_params
        result['message'] = \
            define_code.get_response_msg(result['response_code']) \
            + ". You must throw all of parameters : " + param_name
        return result


class Configuration(Resource):
    def get(self):
        args = ServerComponents().parser.parse_args()

        if args['name'] is not None:
            json_data = json.loads('{}')
            json_data['name'] = args['name']
            request_data = json.dumps(json_data)

        else:
            request_data = ''

        response = ServerComponents().get_configuration(request_data)

        result = json.loads('{}')
        result['response_code'] = response.code

        if response.meta is not "":
            result['data'] = json.loads(response.meta)
        else:
            result['message'] = response.message

        return result

    def post(self):
        result = json.loads('{}')
        request_data = request.get_json()

        try:
            if request_data is None:
                result['response_code'] = define_code.Response.fail
                result['message'] = 'You must throw parameter of JSON when you call (/api/v1/conf) by post method.'

            else:
                response = ServerComponents().set_configuration(json.dumps(request_data))

                result = json.loads('{}')
                result['response_code'] = response.code
                result['message'] = define_code.get_response_msg(define_code.Response.success)

        except ValueError as e:
            result['response_code'] = define_code.Response.fail
            result['message'] = str(e)

        return result


class RestServerRS(CommonThread):
    def __init__(self, rs_port):
        CommonThread.__init__(self)
        self.__rs_port = rs_port
        ServerComponents().set_argument()
        ServerComponents().set_resource()

    def run(self):
        ServerComponents().set_stub_port(self.__rs_port)
        api_port = self.__rs_port + Define.PORT_DIFF_REST_SERVICE_CONTAINER
        logging.debug("RestServer GNC run... %s", str(api_port))
        ServerComponents().app.run(port=api_port, host='0.0.0.0',
                                   debug=False, ssl_context=ServerComponents().ssl_context)
