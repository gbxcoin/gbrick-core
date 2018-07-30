'''
name            : gbrick>helper.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180222
date_modified   : 20180222
version         : 0.1
python_version  : 3.6.5
Comments        :
'''
""" A help class of the gbrick which provides interface for accessing into engine."""

from gbrick.base import ObjectManager


class ChainHelper:
    """It provides an interface that can refer to or use the gbrick engine's internal information.
    """

    def __init__(self):
        self.gbrick_objects = ObjectManager()

    def get_peer_id(self):
        """Obtains the id (Peer unique identification value) of the currently operating Peer.

        :return: peer id
        """
        return self.gbrick_objects.peer_service.peer_id
