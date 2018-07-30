
'''
name            : gbrick::glogic_code.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180105
date_modified   : 20180620
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from enum import IntEnum


class GlogicResponse(IntEnum):
    SUCCESS = 0
    EXCEPTION = 9000
    NOT_INVOKED = 2
    GLOGIC_CONTAINER_EXCEPTION = 9100
