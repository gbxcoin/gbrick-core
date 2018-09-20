'''
name            : gbrick.wagon.glogic.glogic
description     : Gbrick Smart Contract Interface, Base Game Contract Implementation
author          : Hyungjoo Yee
date_created    : 20180906
date_modified   : 20180906
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
from gbrick.common.type.transaction import *
from gbrick.statedb.account import *


class GLogic(metaclass=ABCMeta):
    def __init__(self, account: Account):
        self.account = account

    @abstractmethod
    def run(self, tx: Transaction): raise NotImplementedError()


class BaseGameGLogic(GLogic):

    def __init__(self, account: Account):
        super().__init__(account)

    def run(self, tx: Transaction):
        method = tx.message.get('method')
        if method == BaseGameMethod.BETTING:
            self.betting(tx)
        elif method == BaseGameMethod.SETRESULT:
            self.set_result(tx)
        elif method == BaseGameMethod.GETREWARD:
            self.get_reward(tx)

    def betting(self, tx: Transaction):
        pass

    def set_result(self, tx: Transaction):
        pass

    def get_reward(self, tx: Transaction):
        pass


class CustomGLogic(GLogic):
    def __init__(self, account: Account):
        super().__init__()

    def run(self, tx: Transaction):
        pass

