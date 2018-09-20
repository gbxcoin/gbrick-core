'''
name            : gbrick.wagon.txprocess
description     : Transaction Process Pool, Tpu (Transaction Processing Unit)
author          : Hyungjoo Yee
date_created    : 20180905
date_modified   : 20180906
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
from gbrick.statedb.statedb import *
from gbrick.common.type.base.blockbase import *
from gbrick.wagon.glogic.glogic import *


class TransactionProcessPool:

    # Validate Block before commit transactions to state
    def verify_block(self, block: BlockBase):
        if block.header.hash_block != block.to_hash():
            raise ValueError('[EXCEPTION] TransactionProcessPool::verify_block: Invalid block {0}'.format(block.to_json_str()))

        return True

    def start(self, block: BlockBase):
        self.verify_block(block)

        set_account = set()

        for tx in block.list_transactions:
            set_account.add(tx.address_sender)
            set_account.add(tx.address_recipient)

        height, hash_last_block, dict_state = StateDB().get_state(set_account)

        # TODO: process tx
        for tx in block.list_transactions:
            Tpu(tx).commit(dict_state)

        StateDB().update_state(block.header.num_height, block.header.hash_block, dict_state)

class Tpu:
    def __init__(self, tx: Transaction):
        self.tx = tx;

    def commit(self, dict_state: dict):
        account_sender: Account = dict_state.get(self.tx.address_sender)
        account_recipient: Account = dict_state.get(self.tx.address_recipient)

        account_sender.balance -= self.tx.amount_fee
        if account_sender.balance <= 0:
            return False

        if account_sender.balance < self.tx.amount_value:
            return False

        if account_recipient.type == AccountType.EOA:
            account_sender.balance -= self.tx.amount_value
            print(account_sender.balance)
            account_recipient.balance += self.tx.amount_value
            print(account_recipient.balance)
        elif account_recipient.type == AccountType.BASEGAME:
            BaseGameGLogic(account_recipient).run(self.tx)
        else:
            CustomGLogic(account_recipient).run(self.tx)
