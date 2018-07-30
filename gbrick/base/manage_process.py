'''
name            : gbrick::manage_process.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180217
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''


import logging
import multiprocessing
from abc import abstractmethod

from gbrick import utils as util
from gbrick.base import CommonThread

util.set_log_level()


class ManageProcess(CommonThread):

    QUIT_COMMAND = "quit"

    def __init__(self):
        manager = multiprocessing.Manager()
        self.__manager_dic = manager.dict()
        self.__manager_list = manager.list()
        self.__run_process = None

    def is_run(self):
        return self.__run_process.is_alive()

    def run(self):
        self.__run_process = multiprocessing.Process(
            target=self.process_loop,
            args=(self.__manager_dic, self.__manager_list)
        )
        self.__run_process.start()

    def stop(self):
        self.send_to_process(("quit", None))
        super().stop()

    def wait(self):
        self.__run_process.join()
        super().wait()

    def send_to_process(self, job):
        try:
            self.__manager_list.append(job)
            return True
        except ConnectionRefusedError as e:
            if job[0] == ManageProcess.QUIT_COMMAND:
                logging.debug(f"Process is already quit.")
                return True

            logging.warning(f"Process is not available. job({job}) error({e})")
            return False

    def set_to_process(self, key, value):
        self.__manager_dic[key] = value

    def pop_receive(self, request_id):
        if request_id in self.__manager_dic:
            return self.__manager_dic.pop(request_id)

        return None

    def get_receive(self, request_id=None):
        if request_id in self.__manager_dic:
            return self.__manager_dic[request_id]

        if request_id is None:
            return self.__manager_dic

        return None

    @abstractmethod
    def process_loop(self, manager_dic, manager_list):
        pass
