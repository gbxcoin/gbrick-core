
'''
name            : gbrick::api_server.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180220
date_modified   : 20180603
version         : 0.1
python_version  : 3.6.5
Comments        :
'''


import json
import grpc
import logging
import base64

from grpc._channel import _Rendezvous
from flask import Flask, request
from flask_restful import reqparse, Api, Resource
from flask_restful.utils import cors

from gbrick.components import SingletonMetaClass
from gbrick.base import CommonThread
from gbrick.protos import gbrick_pb2, gbrick_pb2_grpc
from gbrick.utils import define_code

import gbrick.define as Define


class ServerComponents(metaclass=SingletonMetaClass):

    def __init__(self):
        self.__app = Flask(__name__)
        self.__api = Api(self.__app)
        self.__api.decorators = [cors.crossdomain(origin='*', headers=['accept', 'Content-Type'])]
        self.__parser = reqparse.RequestParser()
        self.__stub_to_peer_service = None
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
        return self.__stub_to_peer_service

    @property
    def ssl_context(self):
        return self.__ssl_context

    def set_stub_port(self, port, IP_address):
        self.__stub_to_peer_service = gbrick_pb2_grpc.PeerServiceStub(
            grpc.insecure_channel(IP_address + ':' + str(port)))

    def set_argument(self):
        self.__parser.add_argument('hash')
        self.__parser.add_argument('channel')

    def set_resource(self):
        self.__api.add_resource(Query, '/api/v1/query')
        self.__api.add_resource(Transaction, '/api/v1/transactions')
        self.__api.add_resource(Status, '/api/v1/status/peer')
        self.__api.add_resource(Blocks, '/api/v1/blocks')
        self.__api.add_resource(InvokeResult, '/api/v1/transactions/result')

    def query(self, data, channel):
        # TODO
        return self.__stub_to_peer_service.Query(gbrick_pb2.QueryRequest(params=data, channel=channel),
                                                 Define.REST_GLOGIC_QUERY_TIMEOUT)

    def create_transaction(self, data, channel):
        return self.__stub_to_peer_service.CreateTx(gbrick_pb2.CreateTxRequest(data=data, channel=channel)
                                                    , Define.REST_GRPC_TIMEOUT)

    def get_transaction(self, tx_hash, channel):
        return self.__stub_to_peer_service.GetTx(gbrick_pb2.GetTxRequest(tx_hash=tx_hash, channel=channel), self.REST_GRPC_TIMEOUT)

    def get_invoke_result(self, tx_hash, channel):
        return self.__stub_to_peer_service.GetInvokeResult(gbrick_pb2.GetInvokeResultRequest(
            tx_hash=tx_hash, channel=channel), Define.REST_GRPC_TIMEOUT)

    def get_status(self, channel):
        return self.__stub_to_peer_service.GetStatus(gbrick_pb2.StatusRequest(request="", channel= channel), self.REST_GRPC_TIMEOUT)

    def get_block(self, block_hash="", block_height=-1,
                  block_data_filter="prev_block_hash, height, block_hash",
                  tx_data_filter="tx_hash",
                  channel=Define.GBRICK_DEFAULT_CHANNEL):

        response = self.__stub_to_peer_service.GetBlock(
            gbrick_pb2.GetBlockRequest(
                block_hash=block_hash,
                block_height=block_height,
                block_data_filter=block_data_filter,
                tx_data_filter=tx_data_filter,
                channel=channel),
            Define.REST_GRPC_TIMEOUT
            )

        return response

    def get_last_block_hash(self, channel):
        response = self.__stub_to_peer_service.GetLastBlockHash(
            gbrick_pb2.CommonRequest(request="", channel=channel), Define.REST_GRPC_TIMEOUT)
        return str(response.block_hash)

    def get_block_by_hash(self, block_hash="",
                          channel=Define.GBRICK_DEFAULT_CHANNEL,
                          block_data_filter="prev_block_hash, merkle_tree_root_hash, \
                                            time_stamp, height, peer_id",
                          tx_data_filter="tx_hash, timestamp, data_string, peer_id",
                          ):
        return self.get_block(block_hash, -1, block_data_filter, tx_data_filter, channel)


def get_channel_name_from_args(args) -> str:
    return Define.GBRICK_DEFAULT_CHANNEL if args.get('channel') is None else args.get('channel')


def get_channel_name_from_json(request_body: dict) -> str:
    try:
        return request_body['channel']
    except KeyError:
        return Define.GBRICK_DEFAULT_CHANNEL


class Query(Resource):
    def post(self):
        request_body = json.dumps(request.get_json())
        channel = get_channel_name_from_json(request.get_json())
        query_data = json.loads('{}')
        try:
            #TODO
            response = ServerComponents().query(request_body, channel)
            logging.debug(f"query result : {response}")
            query_data['response_code'] = str(response.response_code)
            try:
                query_data['response'] = json.loads(response.response)

            except json.JSONDecodeError as e:
                logging.warning("your response is not json, your response(" + str(response.response) + ")")
                query_data['response'] = response.response

        except _Rendezvous as e:
            logging.error(f'Execute Query Error : {e}')
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                # TODO
                logging.debug("gRPC timeout !!!")
                query_data['response_code'] = str(define_code.Response.timeout_exceed)

        return query_data


class Transaction(Resource):
    def get(self):
        args = ServerComponents().parser.parse_args()
        response = ServerComponents().get_transaction(args['hash'], get_channel_name_from_args(args))
        tx_data = json.loads('{}')
        tx_data['response_code'] = response.response_code
        tx_data['data'] = ""
        if len(response.data) is not 0:
            try:
                tx_data['data'] = json.loads(response.data)
            except json.JSONDecodeError as e:
                logging.warning("your data is not json, your data(" + str(response.data) + ")")
                tx_data['data'] = response.data

        tx_data['meta'] = ""
        if len(response.meta) is not 0:
            tx_data['meta'] = json.loads(response.meta)

        tx_data['more_info'] = response.more_info
        b64_sign = base64.b64encode(response.signature)
        tx_data['signature'] = b64_sign.decode()
        b64_public_key = base64.b64encode(response.public_key)
        tx_data['public_key'] = b64_public_key.decode()

        return tx_data

    def post(self):
        # logging.debug("RestServer Post Transaction")
        request_body = json.dumps(request.get_json())
        logging.debug("Transaction Request Body : " + request_body)
        channel = get_channel_name_from_json(request.get_json())
        response = ServerComponents().create_transaction(request_body, channel)

        tx_data = json.loads('{}')
        tx_data['response_code'] = str(response.response_code)
        tx_data['tx_hash'] = response.tx_hash
        tx_data['more_info'] = response.more_info
        logging.debug('create tx result : ' + str(tx_data))

        return tx_data


class InvokeResult(Resource):
    def get(self):
        logging.debug('transaction result')
        args = ServerComponents().parser.parse_args()
        logging.debug('tx_hash : ' + args['hash'])
        channel_name = get_channel_name_from_args(args)
        response = ServerComponents().get_invoke_result(args['hash'], channel_name)
        verify_result = dict()
        verify_result['response_code'] = str(response.response_code)
        if len(response.result) is not 0:
            try:
                result = json.loads(response.result)
                result['jsonrpc'] = '2.0'
                verify_result['response'] = result
            except json.JSONDecodeError as e:
                logging.warning("your data is not json, your data(" + str(response.data) + ")")
                verify_result['response_code'] = define_code.Response.fail
        else :
            verify_result['response_code'] = str(define_code.Response.fail)
        return verify_result


class Status(Resource):
    def get(self):
        args = ServerComponents().parser.parse_args()
        response = ServerComponents().get_status(
            get_channel_name_from_args(args)
        )
        status_json_data = json.loads(response.status)
        status_json_data['block_height'] = response.block_height
        status_json_data['total_tx'] = response.total_tx
        status_json_data['leader_complaint'] = response.is_leader_complaining
        return status_json_data


class Blocks(Resource):
    def get(self):
        args = ServerComponents().parser.parse_args()
        channel = get_channel_name_from_args(args)
        if not args['hash'] is None:
            block_hash = args['hash']
            response = ServerComponents().get_block_by_hash(block_hash=block_hash,
                                                            channel=channel)
            logging.debug(f"response : {response}")
            block_data = json.loads('{}')
            block_data['block_hash'] = response.block_hash
            block_data['block_data_json'] = json.loads(response.block_data_json)

            if len(response.tx_data_json) < 1:
                block_data['tx_data_json'] = ''
            else:
                tx_data = json.loads('[]')
                tx_json_data = response.tx_data_json

                for i in range(0, len(tx_json_data)):
                    tx_data.append(json.loads(tx_json_data[i]))

                block_data['tx_data_json'] = json.loads(json.dumps(tx_data))

        else:
            block_hash = ServerComponents().get_last_block_hash(channel=channel)
            response = ServerComponents().get_block_by_hash(block_hash=block_hash,
                                                            channel=channel)
            logging.debug(f"response : {response}")
            block_data = json.loads('{}')
            block_data['response_code'] = response.response_code
            block_data['block_hash'] = response.block_hash
            block_data['block_data_json'] = json.loads(response.block_data_json)

        return block_data


class RestServer(CommonThread):
    def __init__(self, peer_port, peer_ip_address=None):
        if peer_ip_address is None:
            peer_ip_address = Define.IP_LOCAL
        CommonThread.__init__(self)
        self.__peer_port = peer_port
        self.__peer_ip_address = peer_ip_address
        ServerComponents().set_argument()
        ServerComponents().set_resource()

    def run(self):
        ServerComponents().set_stub_port(self.__peer_port, self.__peer_ip_address)
        api_port = self.__peer_port + Define.PORT_DIFF_REST_SERVICE_CONTAINER
        host='0.0.0.0'
        logging.debug("RestServer run... %s", str(api_port))
        ServerComponents().app.run(port=api_port, host='0.0.0.0',
                                   debug=False, ssl_context=ServerComponents().ssl_context)
