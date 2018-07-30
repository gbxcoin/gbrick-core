
'''
name            : gbrick::rest_service_gnc.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180215
date_modified   : 20180412
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from gbrick.service import ServerType, Container


class RestServiceRS(Container):
    def __init__(self, port):
        Container.__init__(self, port, ServerType.REST_RS)
        self.start()  # Container Runs RestServer.start()
