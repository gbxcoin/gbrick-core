'''
name            : gbrick::exceptions.py
description     : Gbrick Blockchain
author          : Seung-man Jang
date_created    : 20180211
date_modified   : 20180211
version         : 0.1
python_version  : 3.6.5
Comments        :
'''
"""A module of exceptions for errors on block chain"""


# BlockChain Exception
class TransactionInValidError(Exception):
    """Transaction validation error
    If the data of the transaction and the value of the transaction hash are different, it causes an error
    """
    pass


class BlockInValidError(Exception):
    """Block validation error
    Occurs when an unvalidated block is added to a block chain, or when the validation has a different hash value
    """
    pass


class BlockError(Exception):
    """Occurs when the configuration of the block is not perfect, or a part of the component is missing.
    """
    pass


class BlockchainError(Exception):
    """Errors that occur when a problem occurs on a block chain
    """
    pass


class ScoreInvokeError(Exception):
    """Error While Invoke Score
    """
