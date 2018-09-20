import leveldb
import pickle
from gbrick.property import *


class DBManager:
    def __init__(self, db_name: str):
        self.name = db_name
        self.db = leveldb.LevelDB('{0}/{1}'.format(DB_PATH, db_name), create_if_missing=True)

    # Insert Data
    def insert(self, key: str, data: object) -> bool:
        try:
            if not self.db:
                return False

            self.db.Put(key.encode('utf-8'), pickle.dumps(data))
            return True
        except leveldb.LevelDBError:
            return False

    # Select Data : Dictionary로 리턴한다.
    def select(self, key=None) -> dict:
        try:
            if not self.db:
                return None

            resdict = {}
            if isinstance(key, str):
                if key == "*":
                    for k, data in self.db.RangeIter():
                        resdict[k.decode('utf-8')] = pickle.loads(data)
                else:
                    return pickle.loads(self.db.Get(key.encode('utf-8')))
            elif isinstance(key, list):
                if len(key) > 0:
                    for k in key:
                        resdict[k] = pickle.loads(self.db.Get(k.encode('utf-8')))
            return resdict
        except leveldb.KeyError:
            return None  # Key Error 발생
        except leveldb.LevelDBError:
            return None  # LevelDB Error 발생

    # Update Data
    def update(self, key: str, data: object) -> bool:
        try:
            if not self.db:
                return False

            self.db.Delete(key.encode('utf-8'))
            self.db.Put(key.encode('utf-8'), pickle.dumps(data))
            return True
        except leveldb.LevelDBError:
            return False

    # Delete Data
    def delete(self, key: str) -> bool:
        try:
            if not self.db:
                return False

            self.db.Delete(key.encode('utf-8'))
            return True
        except leveldb.LevelDBError:
            return False

    # DB의 데이터 수 가져오기
    def count_data(self) -> int:
        try:
            if not self.db:
                return -1

            return sum(1 for i in self.db.RangeIter())
        except leveldb.LevelDBError:
            return -1  # error 발생

    # DB의 key List 가져오기
    def get_key_list(self) -> list:
        try:
            if not self.db:
                return []

            key_list = []
            for key, value in self.db.RangeIter():
                key_list.append(key.decode('utf-8'))

            return key_list
        except leveldb.LevelDBError:
            return []  # error 발생

    # DB에 key 존재여부 확인
    def exist_key(self,skey: str) -> bool:
        try:
            for key, value in self.db.RangeIter():
                if skey.encode('utf-8') == key:
                    return True

            return False
        except leveldb.LevelDBError:
            return False  # error 발생

    # DB 지우기
    def remove_db(self) -> bool:
        try:
            leveldb.DestroyDB('{0}/{1}'.format(DB_PATH, self.name))
            return True
        except leveldb.LevelDBError:
            return False  # error 발생

    def batch_process(self, data: dict) -> bool:
        try:
            # create a batch object
            batch = leveldb.WriteBatch()
            for key, val in data.items():
                batch.Put(key.encode('utf-8'), pickle.dumps(val.encode('utf-8')))
            self.db.Write(batch, sync=True)
            return True
        except leveldb.LevelDBError:
            return False


'''
class DbManager:

    def __init__(self, db_path: str = ".."):
        try:
            if db_path.endswith('/'):
                db_path = db_path[:-1]

            if not hasattr(self, '_db_main'):
                self._db_main = leveldb.LevelDB(db_path + '/gdb/db_main', create_if_missing=True)
            if not hasattr(self, '_db_block'):
                self._db_block = leveldb.LevelDB(db_path + '/gdb/db_block', create_if_missing=True)
            if not hasattr(self, '_db_node'):
                self._db_node = leveldb.LevelDB(db_path + '/gdb/db_node', create_if_missing=True)
            if not hasattr(self, '_db_llfc'):
                self._db_llfc = leveldb.LevelDB(db_path + '/gdb/db_llfc', create_if_missing=True)
            if not hasattr(self, '_db_wagon'):
                self._db_wagon = leveldb.LevelDB(db_path + '/gdb/db_wagon', create_if_missing=True)
        except leveldb.LevelDBError as err:
            self._db_block = None
            print(str(err))

    # 문자열에 따라 해당 LevelDB 가져오기
    def get_db(self, dbname: str) -> leveldb:
        if dbname == 'db_main':
            return self._db_main
        elif dbname == 'db_block':
            return self._db_block
        elif dbname == 'db_node':
            return self._db_node
        elif dbname == 'db_llfc':
            return self._db_llfc
        elif dbname == 'db_wagon':
            return self._db_wagon
        else:
            return None

    # Insert Data
    def insert_data(self, db: str, key: str, data: object) -> bool:
        try:
            seldb = self.get_db(db)
            if not seldb:
                return False

            seldb.Put(key.encode('utf-8'), pickle.dumps(data))
            return True
        except leveldb.LevelDBError:
            return False

    # Select Data : Dictionary로 리턴한다.
    def select_data(self, db: str, key=None) -> dict:
        try:
            seldb = self.get_db(db)
            if not seldb:
                return None

            resdict = {}
            if isinstance(key, str):
                if key == "*":
                    for k, data in seldb.RangeIter():
                        resdict[k.decode('utf-8')] = pickle.loads(data)
                else:
                    resdict[key] = pickle.loads(seldb.Get(key.encode('utf-8')))
            elif isinstance(key, list):
                if len(key) > 0:
                    for k in key:
                        resdict[k] = pickle.loads(seldb.Get(k.encode('utf-8')))
            return resdict
        except leveldb.KeyError:
            return None  # Key Error 발생
        except leveldb.LevelDBError:
            return None  # LevelDB Error 발생

    # Update Data
    def update_data(self, db: str, key: str, data: object) -> bool:
        try:
            seldb = self.get_db(db)
            if not seldb:
                return False

            seldb.Delete(key.encode('utf-8'))
            seldb.Put(key.encode('utf-8'), pickle.dumps(data))
            return True
        except leveldb.LevelDBError:
            return False

    # Delete Data
    def delete_data(self, db: str, key: str) -> bool:
        try:
            seldb = self.get_db(db)
            if not seldb:
                return False

            seldb.Delete(key.encode('utf-8'))
            return True
        except leveldb.LevelDBError:
            return False

    # DB의 데이터 수 가져오기
    def count_data(self, db: str) -> int:
        try:
            seldb = self.get_db(db)
            if not seldb:
                return -1

            return sum(1 for i in seldb.RangeIter())
        except leveldb.LevelDBError:
            return -1   # error 발생

    # DB의 key List 가져오기
    def get_key_list(self, db) -> list:
        try:
            if isinstance(db, str):
                seldb = self.get_db(db)
            elif isinstance(db, leveldb.LevelDB):
                seldb = db
            else:
                seldb = None

            if not seldb:
                return []

            key_list = []
            for key, value in seldb.RangeIter():
                key_list.append(key.decode('utf-8'))

            return key_list
        except leveldb.LevelDBError:
            return []   # error 발생

    # DB에 key 존재여부 확인
    def exist_key(self, db, skey: str) -> bool:
        try:
            if isinstance(db, str):
                seldb = self.get_db(db)
            elif isinstance(db, leveldb.LevelDB):
                seldb = db
            else:
                return False

            for key, value in seldb.RangeIter():
                if skey.encode('utf-8') == key:
                    return True

            return False
        except leveldb.LevelDBError:
            return False   # error 발생

    # DB 지우기
    def remove_db(self, db: str) -> bool:
        try:
            seldb = self.get_db(db)
            if not seldb:
                False

            leveldb.DestroyDB('../gdb/' + db)
            return True
        except leveldb.LevelDBError:
            return False   # error 발생

    def batch_process(self, db: str, data: dict) -> bool:
        try:
            if isinstance(db, str):
                seldb = self.get_db(db)
            elif isinstance(db, leveldb.LevelDB):
                seldb = db
            else:
                return False

            # create a batch object
            batch = leveldb.WriteBatch()
            for key, val in data.items():
                batch.Put(key.encode('utf-8'), pickle.dumps(val.encode('utf-8')))
            seldb.Write(batch, sync=True)
            return True
        except leveldb.LevelDBError:
            return False
'''