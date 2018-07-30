
'''
name            : gbrick::glogic_base.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180105
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import logging
from gbrick.base import ObjectManager
from abc import ABCMeta, abstractmethod


class GlogicBase(metaclass=ABCMeta):

    PACKAGE_FILE = 'package.json'

    def __init__(self, glogic_info=None):
        self._glogic_info = glogic_info
        self._glogic_service = ObjectManager().glogic_service

    @abstractmethod
    def invoke(self, transaction, block):

        pass

    @abstractmethod
    def query(self, params):

        pass

    @abstractmethod
    def info(self):

        pass

    def get_info_value(self, key):
        if self._glogic_info is not None:
            try:
                return self._glogic_info[key]
            except KeyError:
                logging.warning("There is no key in your score info, your key was: " + str(key))
        return ""
