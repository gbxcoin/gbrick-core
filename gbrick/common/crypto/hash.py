import sha3


def to_gbrick_hash(p_val: str):
    val = p_val
    if type(val) is str:
        val = val.encode()

    return sha3.keccak_256(val).hexdigest().encode('utf-8')


def is_num(x):
    return isinstance(x, int)


def is_bytes(x):
    return isinstance(x, bytes)


def is_text(x):
    return isinstance(x, str)


def sha3_str(x):
    return sha3.keccak_256(x).digest()


def _ord(x):
    if is_num(x):
        return x
    else:
        return ord(x)


def bytes_to_int(x):
    k = 0
    for i in x:
        k = k*256 + _ord(i)
    return k


def int_to_bytes(x):
    return x.to_bytes(256, byteorder='big')

def int_to_bytes32(x):
    return x.to_bytes(32, byteorder='big')