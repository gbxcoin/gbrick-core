
'''
name            : gbrick::common_process.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180218
date_modified   : 20180712
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging
import multiprocessing
from abc import abstractmethod

from gbrick import utils as util

util.set_log_level()


class CommonProcess:

    def __init__(self):
        self.__conn = None
        self.__run_process = None

    def is_run(self):
        return self.__run_process.is_alive()

    def start(self):
        parent_conn, child_conn = multiprocessing.Pipe()

        self.__conn = parent_conn
        self.__run_process = multiprocessing.Process(target=self.run, args=(child_conn, ))
        self.__run_process.start()

    def stop(self):
        self.send_to_process(("quit", None))

    def wait(self):
        self.__run_process.join()

    def send_to_process(self, job):
        self.__conn.send(job)


    def recv_from_process(self):
        try:
            return self.__conn.recv()
        except EOFError:
            logging.error("fail recv from process!")
            return None

    @abstractmethod
    def run(self, child_conn):
        pass
