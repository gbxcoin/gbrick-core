
'''
name            : gbrick::object_manager.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180215
date_modified   : 20180609
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from gbrick.components import SingletonMetaClass


class ObjectManager(metaclass=SingletonMetaClass):

    rs_service = None
    peer_service = None
    glogic_service = None
    rest_proxy_service = None
