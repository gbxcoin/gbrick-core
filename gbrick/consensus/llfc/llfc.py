from gbrick.module.p2p import *
from gbrick.common.type import *
from gbrick.common.utils.glogger import *
from gbrick.consensus.base.datapool import *
from gbrick.consensus.llfc.btree import *
from gbrick.module.component.gbrickprofile import *
from gbrick.module.component.messagequeue import *
from gbrick.module.component.modulehub import *
from gbrick.blockchain.blockchain import *


class LLFCEngine(IMessageQueueDelegator, ILLFCBehaviorTree, IModule):
    def __init__(self):
        self.profile = GbrickProfile().loads(PROFILE_PATH)
        self.glogger = Glog()
        self.queue = MessageQueue(delegator=self)
        self.hub = None
        self.btree_root = LLFCBehaviorTree(p_engine=self).create_root()
        self.pool_transaction = DataPool()
        self.pool_candidate_block = StagedDataPool()
        self.pool_vote = VotePool()
        self.blockchain = BlockChain()

        self.num_quorum = 4
        self.stage = LLFCStage.PROPOSE
        self.num_height = self.blockchain.get_height()+1
        self.num_prev_height = 0
        self.num_retry_count = 0
        self.list_selected_block = []
        self.timestamp = 0
        self.duration = 0

        self.trace_log = []

    def start(self):
        self.queue.start()

    # IModule Implementation
    def set_hub(self, hub):
        self.hub = hub

    def push(self, message: Message):
        self.queue.push(message)

    # IMessageQueueDelegator Implementation
    def mq_process_queue(self, queue_thread, message):
        if message.to != ModuleType.CONSENSUS:
            return

        if message.type == MessageType.CANDIDATE_BLOCK:
            b = Block()
            b.from_dict(json.loads(message.data))
            self.pool_candidate_block.put_data(b)
            '''if self._is_valid(b.header.address_creator, 
                             b.header.hash_candidate_block, 
                             b.header.byte_signature):
                self.pool_candidate_block.put_data(b)'''

        elif message.type == MessageType.TRANSACTION:
            t = Transaction()
            t.from_dict(json.loads(message.data))
            self.pool_transaction.put_data(t)
            '''if self._is_valid(t.address_sender, 
                             t.hash_transaction,
                             t.byte_signature):
                self.pool_transaction.put_data(t)'''

        elif message.type == MessageType.VOTE:
            v = Vote()
            v.from_dict(json.loads(message.data))
            self.pool_vote.put_data(v)
            '''if self._is_valid(v.address_creator, 
                             v.hash_vote, 
                             v.byte_signature):
                self.pool_vote.put_data(v)'''

        elif message.type == MessageType.FINALIZE_BLOCK:
            message.to = ModuleType.BLOCKCHAIN
            self.blockchain.push(message)
        else:
            raise ValueError('LLFCEngine::Messagetype not matched')

    def mq_process_synced(self, queue_thread):
        trace_log = []
        self.btree_root.invoke(trace_log)
        if not self.trace_log.__eq__(trace_log):
            print('[LOG] LLFCEngine::mq_process_synced: tree trace {0}'.format(trace_log))
        self.trace_log = trace_log

    def mq_pre_run(self, queue_thread):
        print('[LOG] LLFCEngine::mq_pre_run')

    def mq_end_run(self, queue_thread): pass

    # ILLFCBehaviorTree
    def check_diff_height(self):
        if self.num_height < self.blockchain.get_height()+1:
            return True
        return False

    def check_exist_transaction(self):
        if self.pool_transaction.dict_data:
            return True
        return False

    def create_candidate_block(self):
        c_block = self._generate_candidate()
        # TODO path, pw
        self.pool_candidate_block.put_data(c_block)
        glogger.debug('LLFCEngine::Create Candidate Block {}'.format(c_block.to_json_str()))
        #print('LLFCEngine::Create Cadidate Block {}'.format(c_block.to_json_str()))

        msg_block = Message()
        msg_block.to = ModuleType.CONSENSUS
        msg_block.type = MessageType.CANDIDATE_BLOCK
        msg_block.data = c_block.to_json_str()
        self.sendall(msg_block)
        return True

# wait도 무작정 정해진 시간동안 기다릴게 아니다.
# 대표들의 후보블록이 모두 들어온다면 기다린 시간 계산과 함께 다음 스테이지로 바로 연결

    def get_propose_block_from_pool(self):
        self.list_selected_block = self.pool_candidate_block.get_stage_list(self.get_wave())
        return True

    def select_maximum_tx(self):
        if len(self.list_selected_block) > 0:
            cblock_list = self.list_selected_block
            glogger.debug(cblock_list)
            # self.list_selected_block.clear()
            # .clear() -> 연결된? 데이터도 다 삭제해버림... 위에서 clear 사용 시 cblock_list 변수도 비어버림
            self.list_selected_block = []
            maximum = [len(b.list_transactions) for b in cblock_list]
            maximum.sort()
            _max = maximum.pop()

            for b in cblock_list:
                if _max <= len(b.list_transactions):
                    self.list_selected_block.append(b)

            if len(self.list_selected_block) is 1:
                print('LLFCEngine::Selected Block : {}'.format(self.list_selected_block[0].header.hash_candidate_block))
                return True

        return False

    def select_oldest_tx(self):
        if len(self.list_selected_block) > 0:
            cblock_list = self.list_selected_block
            glogger.debug(cblock_list)
            self.list_selected_block = []
            list_select_time = []

            for b in cblock_list:
                list_time = [t.timestamp for t in b.list_transactions]
                list_time.sort(reverse=True)
                list_select_time.append((list_time.pop(), b))
            # Nonetype 예외처리
            time_compare = [float(i[0]) for i in list_select_time]
            time_compare.sort(reverse=True)
            _max = time_compare.pop()

            for i in list_select_time:
                if _max >= i[0]:
                    self.list_selected_block.append(i[1])

            if len(self.list_selected_block) is 1:
                print('LLFCEngine:: Selected Block : {}'.format(self.list_selected_block[0].header.hash_candidate_block))
                return True

        return False

    def select_timecompatibility(self):
        return False
        if len(self.list_selected_block) > 0:

            cblock_list = self.list_selected_block
            glogger.debug(cblock_list)
            self.list_selected_block = []

            #적합한 시간...?
            suitable = [b.header.timestamp for b in cblock_list]
            suitable.sort()


            if len(self.list_selected_block) is 1:
                print('LLFCEngine:: Selected Block  : {}'.format(self.list_selected_block[0].header.hash_candidate_block))
                return True

        return False

    def select_conflict_tolerance(self):
        max_hash_val = b''
        selected_block = None
        glogger.debug(self.list_selected_block)
        for i in self.list_selected_block:
            if max_hash_val < i.header.hash_candidate_block:
                max_hash_val = i.header.hash_candidate_block
                selected_block = i

        self.list_selected_block = []
        self.list_selected_block.append(selected_block)
        print('LLFCEngine::Selected Block : {0}'.format(self.list_selected_block[0].header.hash_candidate_block))
        return True


    def create_vote(self):
        v = Vote()
        v.address_creator = self.profile.address_coinbase
        v.num_block_height = self.num_height
        v.num_retry_count = self.num_retry_count
        v.hash_candidate_block = self.list_selected_block[0].header.hash_candidate_block
        v.hash_vote = v.to_hash()
        #TODO path, pw
        v.byte_signature = signing(v.hash_vote, self.profile.private_key)
        print('LLFCEngine::Vote')

        self.pool_vote.put_data(v)

        msg_block = Message()
        msg_block.to = ModuleType.CONSENSUS
        msg_block.type = MessageType.VOTE
        msg_block.data = v.to_json_str()
        self.sendall(msg_block)
        return True

    def check_select_vote(self):
        v = self.pool_vote.get_vote_result(self.get_wave())
        #get_data(vote_hash), get_vote_list(wave, c_hash)
        for k in v:
            result = v.get(k)
            #result = 6
            if result >= self.num_quorum:
                if k == self.list_selected_block[0].header.hash_candidate_block:
                    return True
                else:
                    b = self.pool_candidate_block.get_data(k)
                    self.list_selected_block=[]
                    self.list_selected_block.append(b)
                    return True
        return False


    def check_block_creator(self):
        print(self.list_selected_block[0].header.address_creator,self.profile.address_coinbase )
        if self.list_selected_block[0].header.address_creator == self.profile.address_coinbase:
            return True
        return False

    def create_finalize_block(self):

        b = self._generate_finalize()
        #irreversible block
        glogger.debug('LLFCEngine::Create Finalize Block')

        msg_block = Message()
        msg_block.to = ModuleType.CONSENSUS
        msg_block.type = MessageType.FINALIZE_BLOCK
        msg_block.data = b.to_json_str()
        self.sendall(msg_block)

        msg_block.to = ModuleType.BLOCKCHAIN
        self.blockchain.push(msg_block)
        return True

    def get_wave(self):
        return '{0}-{1}'.format(self.num_height, self.num_retry_count)

    def increase_height(self):
        #트리수정이나 로직 수정 필요, 이전 블록 해쉬 정보 블록체인 DB에서 가져오기?
        #self.num_blockchain_height = BlockChain.get_height()
        self.num_height += 1
        return True


    def clear_pool(self):
        #block . get_key() -> 변경 후 커밋안햇음
        #create finalize 시 hash_block =b''  ->  hash_block = b'hash' , block.get_key() return is hash_block
        self.pool_candidate_block.remove_stage_except(self.get_wave())
        self.pool_vote.remove_stage_except(self.get_wave())
        self.pool_transaction.remove_data_list([t.hash_transaction for t in self.list_selected_block[0].list_transactions])
        self.list_selected_block = []
        return True


    def get_stage(self):
        return self.stage

    def wait(self, time_limit):
        arrival = time.time()
        if arrival - self.timestamp > time_limit:
            self.duration = arrival
            return True
        return False

    def retry_round(self):
        self.num_retry_count += 1
        print('LLFCEngine::Round retry {}'.format(self.num_retry_count))
        return True

    def update_stage(self,p_stage):
        self.stage = p_stage
        return True

    def time_start(self):
        self.timestamp = time.time()
        return True

    def sendall(self, data):
        msg = Message()
        msg.to = ModuleType.P2P
        msg.type = MessageType.BROADCAST_REP
        msg.data = data.to_json_str()
        self.hub.push(msg)

    def _is_valid(self, address, msghash, signature):
        valid = verifying(msghash, signature)
        if address == valid:
            return True
        else:
            return False

    def _generate_signature(self, hash):
        # address_coinbase +'.keystore'
        return signing(hash, self.profile.private_key)

    def _generate_candidate(self):
        c_block = Block()
        c_block.header.timestamp = time.time()
        c_block.header.hash_prev_block = self.blockchain.get_last_block().header.hash_block
        c_block.header.num_height = self.num_height
        c_block.header.address_creator = self.profile.address_coinbase
        c_block.header.num_retry_count = self.num_retry_count
        c_block.add_transactions(self.pool_transaction.get_all_data_list())
        c_block.header.hash_transaction_root = c_block.generate_tx_root_hash()
        c_block.header.hash_candidate_block = c_block.to_candidate_hash()
        c_block.header.byte_signature = self._generate_signature(c_block.header.hash_candidate_block)
        return c_block

    def _generate_finalize(self):
        v = self.pool_vote.get_vote_result(self.get_wave())
        b: Block = self.list_selected_block[0]
        for k in v:
            if k == b.header.hash_candidate_block:
                v_list = self.pool_vote.get_vote_list(self.get_wave(), b.header.hash_candidate_block)
                b.add_votes(v_list)
                break
        b.header.hash_vote_root = b.generate_vote_root_hash()
        b.header.hash_block = b.to_hash()
        b.header.byte_signature = self._generate_signature(b.header.hash_block)
        return b

if __name__ == '__main__':
    l = LLFCEngine()
    l.start()