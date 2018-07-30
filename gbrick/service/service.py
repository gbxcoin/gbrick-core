'''
name            : gbrick::service.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180215
date_modified   : 20180702
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging
import grpc
from enum import Enum
from concurrent import futures
from gbrick.api_server import RestServer, RestServerRS
from gbrick import define as Define
from gbrick.base import CommonProcess

from gbrick.protos import gbrick_pb2_grpc


class ServerType(Enum):
    REST_RS = 1
    REST_PEER = 2
    GRPC = 3


class Container(CommonProcess):

    def __init__(self, port, type=ServerType.GRPC, peer_ip=None):
        CommonProcess.__init__(self)
        self._port = port
        self._type = type
        self._peer_ip = peer_ip

    def run(self, conn):
        logging.debug("Container run...")

        if self._type == ServerType.GRPC:
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=Define.MAX_WORKERS))
            gbrick_pb2_grpc.add_ContainerServicer_to_server(self, server)
            server.add_insecure_port('[::]:' + str(self._port))
        elif self._type == ServerType.REST_PEER:
            server = RestServer(self._port, self._peer_ip)
        else:
            server = RestServerRS(self._port)

        server.start()

        command = None
        while command != "quit":
            try:
                command, param = conn.recv()
                logging.debug("Container got: " + str(param))
            except Exception as e:
                logging.warning("Container conn.recv() error: " + str(e))

        if self._type == ServerType.GRPC:
            server.stop(0)
        else:
            server.stop()

        logging.info("Server Container Ended.")
