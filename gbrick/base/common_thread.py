
'''
name            : gbrick::common_thread.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180215
date_modified   : 20180610
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import threading

from abc import abstractmethod


class CommonThread:

    def __init__(self):
        self.__is_run = False
        self.__run_thread = None

    def is_run(self):
        return self.__is_run

    def start(self):
        self.__is_run = True
        self.__run_thread = threading.Thread(target=self.run, args=())
        self.__run_thread.start()

    def stop(self):
        self.__is_run = False

    def wait(self):
        self.__run_thread.join()

    @abstractmethod
    def run(self):
        pass
