'''
name            : gbrick.module.component.db
description     : Level DB Helper
author          : Hyungjoo Yee
date_created    : 20180824
date_modified   : 20180824
version         : 1.0
python_version  : 3.6.5
Comments        :
'''
import leveldb
from gbrick.module.component.gbrickprofile import *


class DbManager:

    def __init__(self, db_name: str = ''):
        self.name = db_name
        self.profile = GbrickProfile().loads(PROFILE_PATH)
        self.total_path = '{0}/db/{1}'.format(self.profile.db_path, self.name)

        if not os.path.isdir(self.profile.db_path):
            os.mkdir(self.profile.db_path)

        db_path = '{0}/db'.format(self.profile.db_path)
        if not os.path.isdir(db_path):
            os.mkdir(db_path)

        self.db = leveldb.LevelDB(self.total_path, create_if_missing=True)

    # Insert Data
    def insert(self, key: bytes, dumped_data: object) -> bool:
        try:
            self.db.Put(key, dumped_data)
            return True
        except leveldb.LevelDBError:
            return False

    # Select Data : Dictionary로 리턴한다.
    def select(self, key=None) -> dict:
        try:
            result = self.db.Get(key)
            return result
        except Exception as e:
            print('[ERROR] DBManager::select: {0}'.format(str(e)))
            return None

    def select_all(self) -> dict:
        try:
            dict_result = {}
            for k, data in self.db.RangeIter():
                dict_result.__setitem__(k, data)
        except Exception as e:
            print('[ERROR] DBManager::select_all: {0}'.format(str(e)))
            return None

    # Update Data
    def update(self, key: str, data: object) -> bool:
        try:
            self.db.Delete(key)
            self.db.Put(key, data)
            return True
        except leveldb.LevelDBError:
            return False

    # Delete Data
    def delete(self, key: str) -> bool:
        try:
            self.db.Delete(key)
            return True
        except leveldb.LevelDBError:
            return False

    # DB의 데이터 수 가져오기
    def count(self) -> int:
        try:
            return sum(1 for i in self.db.RangeIter())
        except leveldb.LevelDBError:
            return -1   # error 발생

    # DB의 key List 가져오기
    def get_key_list(self) -> list:
        try:
            if not self.db:
                return []

            key_list = []
            for key, value in self.db.RangeIter():
                key_list.append(key)

            return key_list
        except leveldb.LevelDBError:
            return []   # error 발생

    # DB에 key 존재여부 확인
    def exist_key(self, skey: bytes) -> bool:
        try:
            for key, value in self.db.RangeIter():
                if skey == key:
                    return True

            return False
        except leveldb.LevelDBError:
            return False   # error 발생

    # DB 지우기
    def remove_db(self) -> bool:
        try:
            leveldb.DestroyDB(self.total_path)
            return True
        except leveldb.LevelDBError:
            return False   # error 발생

    def batch_process(self, data: dict) -> bool:
        try:
            # create a batch object
            batch = leveldb.WriteBatch()
            for key, val in data.items():
                batch.Put(key, val)

            self.db.Write(batch, sync=True)
            return True
        except leveldb.LevelDBError:
            return False


if __name__ == '__main__':
    db = DbManager(db_name='testdb')
    db.insert(b'height', int_to_bytes(14))
    print(db.select('height'.encode('utf-8')))
