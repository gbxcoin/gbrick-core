'''
name            : gbrick.wagon.wagon
description     : WAGON
author          : Hyungjoo Yee
date_created    : 20180905
date_modified   : 20180905
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
from gbrick.module.component.messagequeue import *
from gbrick.wagon.txprocess import *
from gbrick.module.component.modulehub import *


@singleton
class Wagon(IMessageQueueDelegator):
    def __init__(self):
        self.queue = MessageQueue(delegator=self)
        self.tx_process_pool = TransactionProcessPool()

    def start(self):
        self.queue.start()

    def push(self, message: Message):
        self.queue.push(message)

    # ========================= IMessageQueueDelegator Implements =========================
    def mq_process_queue(self, queue_thread, message):
        if message.to != ModuleType.WAGON:
            return

        print('[LOG] Wagon::mq_process_queue: {0}'.format(message.to_dict()))
        if message.type == MessageType.FINALIZE_BLOCK:
            block = Block(message.data)
            self.tx_process_pool.start(block)

    def mq_process_synced(self, queue_thread):
        pass

    def mq_pre_run(self, queue_thread):
        print('[LOG] Wagon::mq_pre_run')

    def mq_end_run(self, queue_thread):
        print('[LOG] Wagon::mq_end_run')
    # =====================================================================================


# Test Code========================
import time
from gbrick.common.type.block import *
if __name__ == '__main__':
    height, hash_last, dict_state = StateDB().get_state([b'1234', b'2345'])
    print(dict_state.get(b'1234').to_dict())
    print(dict_state.get(b'2345').to_dict())

    w = Wagon()
    w.start()

    time.sleep(3)

    msg = Message()
    msg.to = ModuleType.WAGON
    msg.type = MessageType.FINALIZE_BLOCK

    block = Block()

    tx = Transaction()
    tx.enum_transaction_type = TransactionType.TRANSFER
    tx.address_recipient = b'2345'
    tx.address_sender = b'1234'
    tx.amount_value = 5000
    tx.amount_fee = 1000

    block.list_transactions = [tx]
    block.header.hash_block = block.to_hash()

    msg.data = block.to_json_str()

    Wagon().push(msg)

    height, hash_last, dict_state = StateDB().get_state([b'1234', b'2345'])
    print(dict_state.get(b'1234').to_dict())
    print(dict_state.get(b'2345').to_dict())