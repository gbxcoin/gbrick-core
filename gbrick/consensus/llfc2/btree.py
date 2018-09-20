import time
from abc import *
from gbrick.common.utils.behaviortree import *
from gbrick.define import *


class ILLFCBehaviorTree(metaclass=ABCMeta):

    @abstractmethod
    def check_diff_height(self): raise NotImplementedError

    @abstractmethod
    def check_exist_transaction(self): raise NotImplementedError

    @abstractmethod
    def create_candidate_block(self): raise NotImplementedError

    @abstractmethod
    def get_propose_block_from_pool(self): raise NotImplementedError

    @abstractmethod
    def select_maximum_tx(self): raise NotImplementedError

    @abstractmethod
    def select_oldest_tx(self): raise NotImplementedError

    @abstractmethod
    def select_timecompatibility(self): raise NotImplementedError

    @abstractmethod
    def select_conflict_tolerance(self): raise NotImplementedError

    @abstractmethod
    def create_vote(self): raise NotImplementedError

    @abstractmethod
    def check_select_vote(self): raise NotImplementedError

    @abstractmethod
    def check_block_creator(self): raise NotImplementedError

    @abstractmethod
    def create_finalize_block(self): raise NotImplementedError

    @abstractmethod
    def get_stage(self): raise NotImplementedError

    @abstractmethod
    def update_stage(self, p_stage): raise NotImplementedError

    @abstractmethod
    def wait(self, time_limit): raise NotImplementedError

    @abstractmethod
    def retry_round(self): raise NotImplementedError

    @abstractmethod
    def time_start(self): raise NotImplementedError

    @abstractmethod
    def increase_height(self): raise NotImplementedError

    @abstractmethod
    def clear_pool(self): raise NotImplementedError

class LLFCBehaviorTree:
    def __init__(self, p_engine: ILLFCBehaviorTree):
        self.engine: ILLFCBehaviorTree = p_engine

    # Level 0 : Root
    def create_root(self):
        root = Selector()
        # first child : Check Finalize and Sync Block
        root.add_child(self.check_finalize_tree())

        # second child : Process Stage
        indexer = Indexer(self.engine.get_stage)
        indexer.add_child(LLFCStage.PROPOSE, self.propose_block_tree())
        indexer.add_child(LLFCStage.COLLECT_CANDIDATE, self.select_tree())
        indexer.add_child(LLFCStage.COLLECT_VOTE, self.collect_vote_tree())
        indexer.add_child(LLFCStage.WAIT_FOR_FINALIZE, Action(self.engine.wait, LLFCTerm.WAIT_FOR_FINALIZE))

        root.add_child(indexer)
        return root

    # Level 1 : Root : first child
    def check_finalize_tree(self):
        root = Selector()

        child2 = Sequencer()
        child2.add_child(Action(self.engine.check_diff_height))
        child2.add_child(self.new_round_tree())
        root.add_child(child2)

        return root

    # Level 1 : Root - Seq - Idx: first child
    def propose_block_tree(self):
        root=Sequencer()
        root.add_child(Action(self.engine.check_exist_transaction))
        root.add_child(Action(self.engine.time_start))
        root.add_child(Action(self.engine.create_candidate_block))
        root.add_child(Action(self.engine.update_stage, LLFCStage.COLLECT_CANDIDATE))

        return root

    # Level 1 : Root - Seq - Idx: second child
    def select_tree(self):
        root = Sequencer()
        root.add_child(Action(self.engine.wait, LLFCTerm.COLLECT_CANDIDATE))
        root.add_child(Action(self.engine.time_start))
        root.add_child(Action(self.engine.get_propose_block_from_pool))

        child = Selector()
        child.add_child(Action(self.engine.select_maximum_tx))
        child.add_child(Action(self.engine.select_oldest_tx))
        child.add_child(Action(self.engine.select_timecompatibility))
        child.add_child(Action(self.engine.select_conflict_tolerance))

        root.add_child(child)
        root.add_child(Action(self.engine.create_vote))
        root.add_child(Action(self.engine.update_stage,LLFCStage.COLLECT_VOTE))

        return root

    # Level 1 : Root - Seq - Idx: third child
    def collect_vote_tree(self):
        root = Selector()

        child1 = Sequencer()
        child1.add_child(Action(self.engine.check_select_vote))

        child1_sub_root = Selector()
        child1_sub_child_1 = Sequencer()
        child1_sub_child_2 = Sequencer()

        child1_sub_child_1.add_child(Action(self.engine.check_block_creator))
        child1_sub_child_1.add_child(Action(self.engine.create_finalize_block))
        child1_sub_child_1.add_child(Action(self.engine.update_stage, LLFCStage.WAIT_FOR_FINALIZE))
        child1_sub_child_1.add_child(Action(self.engine.time_start))

        child1_sub_child_2.add_child(Action(self.engine.update_stage, LLFCStage.WAIT_FOR_FINALIZE))
        child1_sub_child_2.add_child(Action(self.engine.time_start))

        child1_sub_root.add_child(child1_sub_child_1)
        child1_sub_root.add_child(child1_sub_child_2)

        child1.add_child(child1_sub_root)

        child2 = Sequencer()
        child2.add_child(Action(self.engine.wait, LLFCTerm.COLLECT_VOTE))
        child2.add_child(Action(self.engine.retry_round))
        child2.add_child(Action(self.engine.update_stage, LLFCStage.PROPOSE))



        root.add_child(child1)
        root.add_child(child2)

        return root


    def new_round_tree(self):
        root = Sequencer()
        root.add_child(Action(self.engine.increase_height))
        root.add_child(Action(self.engine.clear_pool))
        root.add_child(Action(self.engine.update_stage, LLFCStage.PROPOSE))
        return root