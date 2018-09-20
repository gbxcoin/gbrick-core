from abc import *
from collections import OrderedDict
from gbrick.common.type import *
from gbrick.common.utils.glogger import *
from gbrick.common.crypto.gcrypto import *

class IDataPool(metaclass=ABCMeta):
    @abstractmethod
    def put_data(self, p_data): raise NotImplementedError

    @abstractmethod
    def get_data(self, p_key): raise NotImplementedError

    @abstractmethod
    def clear(self): raise NotImplementedError

    @abstractmethod
    def remove_data(self, p_key): raise NotImplementedError


class DataPool:

    def __init__(self):
        self.dict_pending_tx = {} #unconfirm
        self.dict_finalize_tx = OrderedDict() #confirm
        self.duration = 0


    def put_data(self, p_data: Transaction):
        key = p_data.get_key()

        # transaction out of normaly range
        if (time.time() - p_data.timestamp) > 1800:
            glogger.warning('Pool::{} {} {}'.format('PoolInputTimeOut', p_data.address_sender, p_data.hash_transaction))
            return

        # pool is deny transaction duplication
        if key in self.dict_pending_tx.copy():
            #@TODO
            #t = self.dict_pending_tx.get(key)
            #if (p_data.address_sender == t.address_sender) and (p_data.message == t.message):
                #return
            #else:
            #
            return
        elif key in self.dict_finalize_tx.copy():
            return

        self.dict_pending_tx[key] = p_data


    def put_finalize_data(self,p_hash, p_data: list):
        '''
        :param p_hash: finalize block hash [dictionary key]
        :param p_data: finalize block transaction list  [dictionary values]
        '''
        for k in p_data:
            if self.is_valid(k.address_sender, k.hash_transaction, k.byte_signature):
                continue
            else:
                raise ValueError('Pool::transaction signing error')

        self.dict_finalize_tx[p_hash] = p_data

    def get_data(self, p_key):
        '''
        :param p_key: transaction hash
        :return: transaction data
        '''
        return self.dict_pending_tx[p_key]

    def get_all_data_list(self):
        return [self.dict_pending_tx.get(i) for i in self.dict_pending_tx]


    def remove_data(self, p_data: Transaction):
        if p_data.get_key() in self.dict_pending_tx.copy():
            self.dict_pending_tx.pop(p_data.get_key())


    def remove_data_list(self, p_list_key: list):
        for k in p_list_key:
            key = k.get_key()
            if key in self.dict_pending_tx.copy():
                self.dict_pending_tx.pop(key)


    def pool_manager(self, duration=0):
        # finalize transaction dictionary size limit
        if len(self.dict_finalize_tx.copy()) > 50:
            for k in self.dict_finalize_tx.copy():
                self.dict_finalize_tx.pop(k)
                if len(self.dict_finalize_tx.copy()) < 20:
                    break
        self.duration += duration
        # Stored transaction out of nomarly range
        for k in self.dict_pending_tx.copy():
            t = self.dict_pending_tx.get(k)
            if (time.time() - t.timestamp) > 10800:
                glogger.warning('Pool::{} {} {}'.format('PoolStoreDurationTimeOut', t.address_sender, t.hash_transaction))
                self.dict_pending_tx.pop(k)


    def is_valid(self, address, msg_hash, signature):
        #Transactoin signature valid
        valid = verifying(msg_hash, signature)
        if address == valid:
            return True
        else:
            return False



class StagedDataPool(IDataPool):
    # TODO: Synchronize (using Lock)
    def __init__(self):
        self.dict_data = {}
        self.dict_index = {}

    def get_data(self, p_key):
        _stage = self.dict_index.get(p_key)
        if _stage is None:
            return None

        return self.dict_data.get(_stage).get(p_key)

    def get_stage_dict(self, p_stage):
        return self.dict_data.get(p_stage)

    def get_stage_list(self, p_stage):
        dict_obj = self.dict_data.get(p_stage)
        if dict_obj is None:
            return []

        list_result = []
        for k in dict_obj:
            list_result.append(dict_obj.get(k))

        return list_result

    def clear(self):
        self.dict_data.clear()
        self.dict_index.clear()

    def put_data(self, p_data):
        stage = p_data.get_wave()
        key = p_data.get_key()
        dict_sub: dict = self.dict_data.get(stage)
        if dict_sub is None:
            dict_sub = {}
            self.dict_data[stage] = dict_sub

        dict_sub[key] = p_data
        self.dict_index[key] = stage

    def remove_data(self, p_key):
        stage = self.dict_index.get(p_key)
        self.dict_data.get(stage).__delitem__(p_key)
        self.dict_index.__delitem__(p_key)

    def remove_stage(self, p_stage):
        dict_stage: dict = self.dict_data.get(p_stage)
        if dict_stage is None: return

        for key in dict_stage:
            data = dict_stage.get(key)
            self.dict_index.__delitem__(data.get_key())

        dict_stage.clear()

    def remove_stage_except(self, p_stage):
        dict_stage: dict = self.dict_data.get(p_stage)
        self.dict_data.clear()
        self.dict_data[p_stage] = dict_stage

        self.dict_index.clear()


        if dict_stage is None:
            return

        for key in dict_stage:
            data = dict_stage.get(key)
            self.dict_index[data.get_key()] = data.get_wave()



class VotePool(IDataPool):
    def __init__(self):
        self.dict_data = {}
        self.dict_index = {}
        self.set_deleted_key = set()
        # self.num_quorum = quorum
        # self.callback_notify = callback

    def put_data(self, p_data: Vote):
        stage = p_data.get_wave()
        voted_hash = p_data.hash_candidate_block
        key = p_data.get_key()

        if self.set_deleted_key.__contains__(key):
            self.set_deleted_key.remove(key)
        else:
            dict_stage = self.dict_data.get(stage)
            if dict_stage is None:
                dict_stage = {}
                self.dict_data.__setitem__(stage, dict_stage)

            dict_voted_hash = dict_stage.get(voted_hash)
            if dict_voted_hash is None:
                dict_voted_hash = {}
                dict_stage.__setitem__(voted_hash, dict_voted_hash)

            dict_voted_hash.__setitem__(key, p_data)

            self.dict_index[key] = (stage, voted_hash)

        ''' Remove Callback Process 
        print('VotePool::put_data: now {0}, quorum {1}, voted_hash {2}, stage {3}'
              .format(dict_voted_hash.__len__(), self.num_quorum, voted_hash, stage))
        if dict_voted_hash.__len__() >= self.num_quorum:
            dict_param = {'candidate_block_hash': voted_hash
                , 'height': p_data.num_block_height
                , 'retry_count': p_data.num_retry_count}
            self.callback_notify(dict_param)
        '''

    def get_data(self, p_key):
        if self.dict_index.get(p_key) is None:
            return None

        (stage, voted_hash) = self.dict_index.get(p_key)
        dict_stage = self.dict_data.get(stage)
        if dict_stage is None:
            self.dict_index.__delitem__(p_key)
            return None

        dict_voted_hash = dict_stage.get(voted_hash)
        if dict_voted_hash is None:
            self.dict_index.__delitem__(p_key)
            return None

        return dict_voted_hash.get(p_key)

    def clear(self):
        self.dict_index.clear()
        self.dict_data.clear()

    def remove_data(self, p_key):
        if self.dict_index.get(p_key) is None:
            return

        (stage, voted_hash) = self.dict_index.get(p_key)
        self.dict_index.__delitem__(p_key)
        dict_stage = self.dict_data.get(stage)
        if dict_stage is None:
            return

        dict_voted_hash = dict_stage.get(voted_hash)
        if dict_voted_hash is None:
            return

        dict_voted_hash.__delitem__(p_key)

    def remove_stage(self, p_stage):
        dict_stage = self.dict_data.get(p_stage)
        if dict_stage is None : return

        for voted_hash in dict_stage:
            dict_voted_hash = dict_stage.get(voted_hash)
            for key in dict_voted_hash:
                self.dict_index.__delitem__(key)

        dict_stage.clear()

    def remove_stage_except(self, p_stage):
        dict_stage: dict = self.dict_data.get(p_stage)
        self.dict_data.clear()
        self.dict_data[p_stage] = dict_stage

        self.dict_index.clear()

        if dict_stage is None:
            return

        for voted_hash in dict_stage:
            dict_voted_hash = dict_stage.get(voted_hash)
            for key in dict_voted_hash:
                vote = dict_voted_hash.get(key)
                self.dict_index.__setitem__(key, (vote.get_wave(), vote.hash_candidate_block))

    def get_vote_result(self, p_stage):
        dict_stage = self.dict_data.get(p_stage)

        if dict_stage is None:
            return None

        dict_result = {}
        for k in dict_stage:
            dict_result[k] = dict_stage[k].__len__()

        return dict_result

    def get_vote_list(self, p_stage, p_candidate_hash):
        dict_stage = self.dict_data.get(p_stage)

        if dict_stage is None:
            return None

        dict_voted_hash = dict_stage.get(p_candidate_hash)

        if dict_voted_hash is None:
            return None

        list_result = []
        for k in dict_voted_hash:
            list_result.append(dict_voted_hash.get(k))

        return list_result