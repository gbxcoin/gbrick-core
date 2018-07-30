
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180205
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging
import time
import queue

from gbrick.base import CommonThread
from gbrick import define as Define


class SendToProcess(CommonThread):
    def __init__(self):
        CommonThread.__init__(self)
        self.__job = queue.Queue()
        self.__process = None

    def set_process(self, process):
        self.__process = process

    def send_to_process(self, params):
        # logging.debug("send job queue add")
        self.__job.put(params)

    def run(self):
        while self.is_run():
            time.sleep(Define.SLEEP_SECONDS_IN_SERVICE_LOOP)

            param = None
            while not self.__job.empty():
                # logging.debug("Send to Process by thread.... remain jobs: " + str(self.__job.qsize()))

                param = self.__job.get()
                try:
                    self.__process.send_to_process(param)
                    param = None
                except Exception as e:
                    logging.warning(f"process not init yet... ({e})")
                    break

            if param is not None:
                self.__job.put(param)
