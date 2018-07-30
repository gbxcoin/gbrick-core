'''
name            : Gbrick::singleton.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180205
date_modified   : 20180623
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

class SingletonMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMetaClass, cls).__call__(*args, **kwargs)

        return cls._instances[cls]

    def clear(cls):

        if cls in cls._instances:
            cls._instances.pop(cls)
