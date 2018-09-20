
WAIT_PROPOSE_BLOCK = 0.4

class LLFCStage:
    READY = 0
    PROPOSE = 1
    COLLECT_CANDIDATE = 2
    COLLECT_VOTE = 3
    WAIT_FOR_FINALIZE = 4
    SYNC = 5
    RETRY = 6

class LLFCTerm:
    COLLECT_CANDIDATE = 5
    COLLECT_VOTE = 5
    WAIT_FOR_FINALIZE = 5

class MessageType:
    NONE = 'NONE'
    TRANSACTION = 'TRANSACTION'
    CANDIDATE_BLOCK = 'CANDIDATE_BLOCK'
    VOTE = 'VOTE'
    FINALIZE_BLOCK = 'FINALIZE_BLOCK'
    BROADCAST_NORMAL = 'BROADCAST_NORMAL'
    BROADCAST_REP = 'BROADCAST_REP'
    ADD_PEER = 'ADD_PEER'
    SELECT_DATA = 'SELECT_DATA'


class NodeType:
    NORMAL = 0
    REP = 1


class ModuleType:
    NONE = 'NONE'
    P2P = 'P2P'
    CONSENSUS = 'CONSENSUS'
    BLOCKCHAIN = 'BLOCKCHAIN'
    WAGON = 'WAGON'
    STATE = 'STATE'


class ModulePort:
    NONE = '6600'
    P2P = '6601'
    CONSENSUS = '6602'
    BLOCKCHAIN = '6603'
    WAGON = '6604'
    STATE = '6605'


class TransactionType:
    NONE = None
    TRANSFER = 'transfer'
    BASE_GAME = 'base_game'
    CREATE_GLOGIC = 'create_glogic'
    CALL_GLOGIC = 'call_glogic'


class AccountType:
    EOA = 'eoa'
    BASEGAME = 'basegame'
    GLOGIC = 'glogic'


class TransactionFee:
    TRANSFER = 1000
    BASE_GAME = 100


class GLogicCommand:
    CREATE = 'create'
    CALL = 'call'


class BaseGameMethod:
    BETTING = 'betting'
    SETRESULT = 'set_result'
    GETREWARD = 'get_reward'



MODULEPORT = {ModuleType.NONE: ModulePort.NONE
            , ModuleType.P2P: ModulePort.P2P
            , ModuleType.CONSENSUS: ModulePort.CONSENSUS
            , ModuleType.BLOCKCHAIN: ModulePort.BLOCKCHAIN
            , ModuleType.WAGON: ModulePort.WAGON
            , ModuleType.STATE: ModulePort.STATE
            }
