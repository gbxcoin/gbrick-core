from gbrick.common.type.genesisblock import *
from gbrick.wagon.wagon import *


@singleton
class BlockChain(IMessageQueueDelegator):
    def __init__(self):
        self.profile = GbrickProfile().loads(PROFILE_PATH)

        if not os.path.isdir(self.profile.db_path):
            os.mkdir(self.profile.db_path)

        db_path = '{0}/db'.format(self.profile.db_path)
        if not os.path.isdir(db_path):
            os.mkdir(db_path)

        self.total_path = '{0}/db/{1}'.format(self.profile.db_path, 'blockchain')
        self.db = leveldb.LevelDB(self.total_path, create_if_missing=True)

        self.queue = MessageQueue(delegator=self)

        self._num_height = -1
        self._block_first = None
        self._block_last = None

        try:
            self._num_height = bytes_to_int(self.db.Get(b'height'))
        except Exception:
            print('[LOG] BlockChain::__init__: key height not exist')
            f = open('{0}/gbrick_genesis.block'.format(PROFILE_PATH), 'r')
            str_genesis_block_json = f.read()
            f.close()
            b = GenesisBlock(p_json_str=str_genesis_block_json)
            b.header.hash_block = b.to_hash()
            raw_block = self.to_raw(b)

            batch = leveldb.WriteBatch()
            batch.Put(b'height', int_to_bytes(0))
            batch.Put(b.header.hash_block, raw_block)
            batch.Put(b'first', raw_block)
            batch.Put(b'last', raw_block)
            self.db.Write(batch)

            StateDB().update_genesis_block(b)

            self._num_height = 0

    def start(self):
        self.queue.start()

    def push(self, message: Message):
        self.queue.push(message)

    def to_raw(self, block):
        return pickle.dumps(block.to_dict())

    def from_raw(self, raw) -> Block:
        return Block(p_dict_obj=pickle.loads(raw))

    def finalize(self, p_block:BlockBase):
        height = bytes_to_int(self.db.Get(b'height'))
        if height+1 != p_block.header.num_height:
            # TODO: Synchronize Blockchain
            raise ValueError(
                'Blockchain height is {0}. but finalized Block height is {1}'.format(height, p_block.header.num_height))

        block_last: BlockBase = self.from_raw(self.db.Get(b'last'))
        hash_last_block = block_last.header.hash_block

        str_hash_last_block = hash_last_block.decode('utf-8')
        str_hash_prev = p_block.header.hash_prev_block.decode('utf-8')
        if not str_hash_last_block.__eq__(str_hash_prev):
            raise ValueError(
                'Invalid prev_hash {0} (Last Block Hash is {1})'.format(str_hash_prev, str_hash_last_block))

        str_hashing = p_block.to_hash().decode('utf-8')
        str_hash_block = p_block.header.hash_block.decode('utf-8')
        if not str_hash_block.__eq__(str_hashing):
            raise ValueError(
                'Invalid block hash {0}. (Hashing Result is {1}'.format(str_hash_block, str_hashing))

        raw_block = self.to_raw(p_block)
        batch = leveldb.WriteBatch()
        batch.Put(p_block.header.hash_block, raw_block)
        batch.Put(b'last', raw_block)
        batch.Put(b'height', int_to_bytes(p_block.header.num_height))
        self.db.Write(batch, sync=True)
        self._num_height = p_block.header.num_height
        self._block_last = p_block

        msg = Message()
        msg.to = ModuleType.WAGON
        msg.type = MessageType.FINALIZE_BLOCK
        msg.data = p_block.to_json_str()
        Wagon().push(msg)
        return self._num_height

    def get_height(self):
        if self._num_height < 0:
            self._num_height = bytes_to_int(self.db.Get(b'height'))

        return self._num_height

    def get_last_block(self):
        if self._block_last is None:
            self._block_last: BlockBase = self.from_raw(self.db.Get(b'last'))

        return self._block_last

    def get_first_block(self):
        if self._block_first is None:
            self._block_first: BlockBase = self.from_raw(self.db.Get(b'first'))

        return self._block_first

    # IMessageQueueDelegator Implementation =================================================
    def mq_process_queue(self, queue_thread, message: Message):
        print('[LOG] BlockChain::mq_process_queue')
        if message.to != ModuleType.BLOCKCHAIN:
            return

        if message.type == MessageType.SELECT_DATA:
            pass

        elif message.type == MessageType.FINALIZE_BLOCK:
            self.finalize(Block(message.data))
        else:
            print('[ERROR] BlockChain::receiver_receive: Unknown Message Type {0}'.format(message.type))

    def mq_process_synced(self, queue_thread):
        pass

    def mq_pre_run(self, queue_thread):
        print('[LOG] BlockChain::mq_pre_run')

    def mq_end_run(self, queue_thread):
        print('[LOG] BlockChain::mq_end_run')
    # ==================================================================================


if __name__ == '__main__':
    '''
    b = BlockChain()
    b.start()

    bl = Block()
    bl.header.hash_prev_block = b.get_last_block().header.hash_block
    bl.header.num_height = b.get_height()+1

    bl.header.hash_block = bl.to_hash()

    msg = Message()
    msg.to = ModuleType.BLOCKCHAIN
    msg.type = MessageType.FINALIZE_BLOCK
    msg.data = bl.to_json_str()

    b.push(msg)
    '''

    iterr = BlockChain().db.RangeIter()
    for k, v in iterr:
        print(k)
        if k.decode('utf-8').__eq__('height'):
            print(bytes_to_int(v))
        else:
            print(BlockChain().from_raw(BlockChain().db.Get(k)).to_dict())

