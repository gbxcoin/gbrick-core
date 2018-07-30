
'''
name            : gbrick::consensus_llfc.py
description     : Gbrick Blockchain
author          : Byung Kwon Bae
date_created    : 20180319
date_modified   : 20180610
version         : 0.1
python_version  : 3.6.5
Comments        :
'''


from gbrick.blockchain import *
from gbrick.llfc.consensus_base import ConsensusBase


class ConsensusLLFC(ConsensusBase):

    def consensus(self):
        self._makeup_block()
        time.sleep(Define.SLEEP_SECONDS_IN_SERVICE_LOOP)