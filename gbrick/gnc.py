from datetime import datetime
import leveldb


class NodeInfo:

    _nodeDb = leveldb.LevelDB('../node_db')

    def __init__(self):

        # Node ID
        self.node_id = ''
        # Node Type : 0 대표, 1 예비대표, 9 일반노드
        self.node_type = '9'
        # 노드 번호
        self.node_no = ''
        # 대표노드가 아닐 경우 대표(정)
        self.boss_id = ''
        # 일반노드일 경우 예비 대표(부) : 평소에는 일반 노드 동작
        self.sub_boss_id = ''
        # 대표 노드일 경우 블럭 생성 횟수
        self.block_count = 0
        # 일반 노드일 경우 트랜잭션 생성 횟수
        self.trans_count = 0
        # 노드의 public key
        self.public_key = ''
        # 인센트브
        self.incentive = ''
        # 네트웍 참여 일시
        self.reg_date = ''

    @property
    def node_id(self):
        return self.node_id

    @node_id.setter
    def node_id(self, node_id):
        self.node_id = node_id

    @property
    def type(self):
        return self.node_type

    @type.setter
    def type(self, type):
        self.node_type = type

    @property
    def node_no(self):
        return self.node_no

    @node_no.setter
    def node_no(self, node_no):
        self.node_no = node_no

    @property
    def boss_id(self):
        return self.boss_id

    @boss_id.setter
    def boss_id(self, boss_id):
        self.boss_id = boss_id

    @property
    def sub_boss_id(self):
        return self.sub_boss_id

    @sub_boss_id.setter
    def sub_boss_id(self, sub_boss_id):
        self.sub_boss_id = sub_boss_id

    @property
    def block_count(self):
        return self.block_count

    @block_count.setter
    def block_count(self, block_count):
        self.block_count = block_count

    @property
    def trans_count(self):
        return self.trans_count

    @trans_count.setter
    def trans_count(self, trans_count):
        self.trans_count = trans_count

    @property
    def public_key(self):
        return self.public_key

    @public_key.setter
    def public_key(self, public_key):
        self.public_key = public_key

    @property
    def incentive(self):
        return self.incentive

    @incentive.setter
    def incentive(self, incentive):
        self.incentive = incentive

    @property
    def reg_date(self):
        return self.reg_date

    @reg_date.setter
    def reg_date(self, reg_date):
        self.reg_date = reg_date

    def getJsonNode(self) -> str:
        return f"""{{
            'node_id': '{self.node_id}', 'type': '{self.node_type}', 'node_no': '{self.node_no}',
            'boss_id': '{self.boss_id}', 'sub_boss_id': '{self.sub_boss_id}', 'block_count': '{self.block_count}',
            'trans_count': '{self.trans_count}', 'public_key': '{self.public_key}', 'incentive': '{self.incentive}',
            'reg_date': '{self.reg_date}'
        }}""".replace(' ', '')

    def insertNodeInfoIntoDB(self) -> bool:
        self.reg_date('{:%Y%m%d%H%M%S}'.format(datetime.now()))
        self._nodeDb.Put(self.node_id.encode('utf-8'), self.getJsonNode().encode('utf-8'))

    def readNodeInfoFromDB(self, nid: str) -> str:
        return self._nodeDb.Get(nid.encode('utf-8'))

    def updateNodeIncentive(self, nid: str) -> bool:
        return self._nodeDb.Get(nid.encode('utf-8'))

