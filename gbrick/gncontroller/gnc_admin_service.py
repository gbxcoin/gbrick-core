
'''
name            : gbrick::gnc_admin_manager.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180215
date_modified   : 20180710
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging

from gbrick import utils as util
from gbrick.protos import gbrick_pb2_grpc
from gbrick.utils import define_code

# gbrick_pb2 not import error
import gbrick_pb2


class AdminService(gbrick_pb2_grpc.GNControllerServicer):

    def __init__(self):
        self.__handler_map = {
            define_code.Request.status: self.__handler_status,
            define_code.Request.rs_send_channel_manage_info_to_rs: self.__handler_rs_send_channel_manage_info_to_rs
        }

    def __handler_status(self, request: gbrick_pb2.Message, context):
        util.logger.spam(f"rs_admin_service:__handler_status ({request.message})")
        return gbrick_pb2.Message(code=define_code.Response.success)

    def __handler_rs_send_channel_manage_info_to_rs(self, request, context):
        util.logger.spam(f"rs_admin_service:__handler_rs_send_channel_manage_info_to_rs")
        return gbrick_pb2.Message(code=define_code.Response.success)

    def Request(self, request, context):
        logging.debug("GNC got request: " + str(request))

        if request.code in self.__handler_map.keys():
            return self.__handler_map[request.code](request, context)

        return gbrick_pb2.Message(code=define_code.Response.not_treat_message_code)
