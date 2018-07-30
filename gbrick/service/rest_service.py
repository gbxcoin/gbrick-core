
'''
name            : gbrick::rest_service.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180215
date_modified   : 20180412
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from gbrick import define as Define
from gbrick.service import ServerType, Container


class RestService(Container):
    def __init__(self, port, peer_ip=None):
        if peer_ip is None:
            peer_ip = Define.IP_LOCAL
        Container.__init__(self, port, ServerType.REST_PEER, peer_ip)
        self.start()  # Container Runs RestServer.start()
