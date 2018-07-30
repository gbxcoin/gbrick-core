'''
name           : Gbrick>blockchain.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180215
date_modified   : 20180530
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from gbrick import define as Define
import leveldb

class   dbBlock:
    def __init__(self):
        self.db = leveldb.LevelDB(str(Define['BLOCK_DB_PATH']))

    def countDB(self):
        return sum(1 for i in self.db.RangeIter(reverse = True))

    def get(self, key):
        if key not in self.kv:
            self.kv[key] = self.parent.get(key)
        return self.parent.get(key)

    def put(self, key, value):
        self.parent.put(key, value)

    def commit(self):
        pass

    def delete(self, key):
        self.parent.delete(key)

    def _has_key(self, key):
        return self.parent._has_key(key)

    def __contains__(self, key):
        return self.parent.__contains__(key)

    def __eq__(self, other):
        return self.parent == other

    def __hash__(self):
        return self.parent.__hash__()


class   dbWorking:
    def __init__(self):
        #print (Define['WORK_DB_PATH'])
        self.db = leveldb.LevelDB(str(Define['WORK_DB_PATH']))

    def countDB(self):
        return sum(1 for i in self.db.RangeIter(reverse = True))

    def get(self, key):
        if key not in self.kv:
            self.kv[key] = self.parent.get(key)
        return self.parent.get(key)

    def put(self, key, value):
        self.parent.put(key, value)

    def commit(self):
        pass

    # def delete(self, key):
    #     self.parent.delete(key)

    def _has_key(self, key):
        return self.parent._has_key(key)

    def __contains__(self, key):
        return self.parent.__contains__(key)

    def __eq__(self, other):
        return self.parent == other

    def __hash__(self):
        return self.parent.__hash__()

    # def doTest1(self):
    #     self.db.Put("test1".encode('utf-8'),"1wefewfewf".encode('utf-8'))
    #     self.db.Put("test2".encode('utf-8'),"2ewfewfewf".encode('utf-8'))
    #
    #     print (self.db.Get(b'test1'))
    #
    #     print ("----- counter db ------------")
    #     print (self.countDB())


# if __name__ == "__main__":
#     c = dbManager()
#     c.doTest1()
