
'''
name            : gbrick::stub_manager.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180219
date_modified   : 20180625
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import datetime
import logging
import time
import timeit

import grpc
from grpc._channel import _Rendezvous

from gbrick import utils as util
from gbrick import define as Define
from gbrick.protos import gbrick_pb2
from gbrick.utils import define_code


class StubManager:

    def __init__(self, target, stub_type, is_secure=False):
        self.__target = target
        self.__stub_type = stub_type
        self.__is_secure = is_secure
        self.__stub = None
        self.__stub_update_time = datetime.datetime.now()

        self.__make_stub(False)

    def __make_stub(self, is_stub_reuse=True):
        if util.datetime_diff_in_mins(self.__stub_update_time) >= Define.STUB_REUSE_TIMEOUT or \
                not is_stub_reuse or self.__stub is None:
            util.logger.spam(f"StubManager:__make_stub is_stub_reuse({is_stub_reuse}) self.__stub({self.__stub})")
            self.__stub = util.get_stub_to_server(self.__target, self.__stub_type, is_check_status=False)
            self.__stub_update_time = datetime.datetime.now()
        else:
            pass

    @property
    def stub(self, is_stub_reuse=True):
        # TODO

        self.__make_stub(is_stub_reuse)

        return self.__stub

    @stub.setter
    def stub(self, value):
        self.__stub = value

    @property
    def target(self):
        return self.__target

    def call(self, method_name, message, timeout=None, is_stub_reuse=True, is_raise=False):
        if timeout is None:
            timeout = Define.GRPC_TIMEOUT
        self.__make_stub(is_stub_reuse)

        try:
            stub_method = getattr(self.__stub, method_name)
            return stub_method(message, timeout)
        except Exception as e:
            if is_raise:
                raise e
            logging.debug(f"gRPC call fail method_name({method_name}), message({message}): {e}")

        return None

    @staticmethod
    def print_broadcast_fail(result: _Rendezvous):
        if result.code() != grpc.StatusCode.OK:
            logging.warning(f"call_async fail  : {result}\n"
                            f"cause by : {result.details()}")

    def call_async(self, method_name, message, timeout=None, is_stub_reuse=True):
        if timeout is None:
            timeout = Define.GRPC_TIMEOUT
        self.__make_stub(is_stub_reuse)

        try:
            stub_method = getattr(self.__stub, method_name)
            feature_future = stub_method.future(message, timeout)
            feature_future.add_done_callback(self.print_broadcast_fail)
        except Exception as e:
            logging.warning(f"gRPC call_async fail method_name({method_name}), message({message}): {e}")

    def call_in_time(self, method_name, message, time_out_seconds=None, is_stub_reuse=True):

        if time_out_seconds is None:
            time_out_seconds = Define.CONNECTION_RETRY_TIMEOUT
        self.__make_stub(is_stub_reuse)

        stub_method = getattr(self.__stub, method_name)

        start_time = timeit.default_timer()
        duration = timeit.default_timer() - start_time

        while duration < time_out_seconds:
            try:
                return stub_method(message, Define.GRPC_TIMEOUT)
            except Exception as e:
                logging.debug("duration(" + str(duration)
                              + ") interval(" + str(Define.CONNECTION_RETRY_INTERVAL)
                              + ") timeout(" + str(time_out_seconds) + ")")

            time.sleep(Define.CONNECTION_RETRY_INTERVAL)
            self.__make_stub(False)
            duration = timeit.default_timer() - start_time

        return None

    def call_in_times(self, method_name, message,
                      retry_times=Define.CONNECTION_RETRY_TIMES,
                      is_stub_reuse=True,
                      timeout=Define.GRPC_TIMEOUT):

        self.__make_stub(is_stub_reuse)
        stub_method = getattr(self.__stub, method_name)

        while retry_times > 0:
            try:
                return stub_method(message, timeout)
            except Exception as e:
                logging.debug(f"retry request_server_in_times({method_name}): {e}")

            time.sleep(Define.CONNECTION_RETRY_INTERVAL)
            self.__make_stub(False)
            retry_times -= 1

        return None

    def check_status(self):
        try:
            self.__stub.Request(gbrick_pb2.Message(code=define_code.Request.status), Define.GRPC_TIMEOUT)
            return True
        except Exception as e:
            logging.warning(f"stub_manager:check_status is Fail reason({e})")
            return False

    @staticmethod
    def get_stub_manager_to_server(target, stub_class, time_out_seconds=None,
                                   is_allow_null_stub=False):

        if time_out_seconds is None:
            time_out_seconds = Define.CONNECTION_RETRY_TIMEOUT
        stub_manager = StubManager(target, stub_class)
        start_time = timeit.default_timer()
        duration = timeit.default_timer() - start_time

        while duration < time_out_seconds:
            try:
                logging.debug("(stub_manager) get stub to server target: " + str(target))
                stub_manager.stub.Request(gbrick_pb2.Message(code=define_code.Request.status), Define.GRPC_TIMEOUT)
                return stub_manager
            except Exception as e:
                if is_allow_null_stub:
                    return stub_manager
                logging.warning("Connect to Server Error(get_stub_manager_to_server): " + str(e))
                logging.debug("duration(" + str(duration)
                              + ") interval(" + str(Define.CONNECTION_RETRY_INTERVAL)
                              + ") timeout(" + str(time_out_seconds) + ")")

                time.sleep(Define.CONNECTION_RETRY_INTERVAL)
                duration = timeit.default_timer() - start_time

        return None
