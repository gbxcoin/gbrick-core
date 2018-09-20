import hashlib, hmac
from gbrick.common.crypto.hash import *


# secp256k1 curve
_a = 0
_b = 7
_p = 2 ** 256 - 2 ** 32 - 977
_n = 115792089237316195423570985008687907852837564279074904382605163141518161494337
_Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
_Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
_G = (_Gx, _Gy)

def inverse(p, q):
    if p == 0:
        return 0
    _l, _h = 1, 0
    low, high = p % q, q
    while low > 1:
        _r = high // low
        _n, n = _h - _l * _r, high - low * _r
        _l, low, _h, high = _n, n, _l, low
    return _l % q

def from_j(p):
    k = inverse(p[2], _p)
    return ((p[0] * k**2) % _p, (p[1] * k**3) % _p)

def to_j(p):
    k = (p[0], p[1], 1)
    return k

def j_double(p):
    if not p[1]:
        return (0, 0, 0)
    y = (p[1] ** 2) % _p
    S = (4 * p[0] * y) % _p
    M = (3 * p[0] ** 2 + _a * p[2] ** 4) % _p
    _x = (M**2 - 2 * S) % _p
    _y = (M * (S - _x) - 8 * y ** 2) % _p
    _z = (2 * p[1] * p[2]) % _p
    return (_x, _y, _z)

def j_add(p, q):
    if not p[1]:
        return q
    if not q[1]:
        return p
    x1 = (p[0] * q[2] ** 2) % _p
    x2 = (q[0] * p[2] ** 2) % _p
    y1 = (p[1] * q[2] ** 3) % _p
    y2 = (q[1] * p[2] ** 3) % _p
    if x1 == x2:
        if y1 != y2:
            return (0, 0, 1)
        return j_double(p)
    dx = x2 - x1
    dy = y2 - y1
    du = (dx * dx) % _p
    dv = (dx * du) % _p
    dudv = (x1 * du) % _p
    _x = (dy ** 2 - dv - 2 * dudv) % _p
    _y = (dy * (dudv - _x) - y1 * dv) % _p
    _z = (dx * p[2] * q[2]) % _p
    return (_x, _y, _z)

def j_mul(p, q):
    if p[1] == 0 or q == 0:
        return (0, 0, 1)
    if q == 1:
        return p
    if q < 0 or q >= _n:
        return j_mul(p, q % _n)
    if (q % 2) == 0:
        return j_double(j_mul(p, q // 2))
    if (q % 2) == 1:
        return j_add(j_double(j_mul(p, q // 2)), p)

def add(p, q):
    return from_j(j_add(to_j(p), to_j(q)))

def mul(p, q):
    return from_j(j_mul(to_j(p), q))

def deterministic(msg_hash, private):
    v = b'\x01' * 32
    k = b'\x00' * 32
    k = hmac.new(k, v + b'\x00' + private + msg_hash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    k = hmac.new(k, v + b'\x01' + private + msg_hash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    return bytes_to_int(hmac.new(k, v, hashlib.sha256).digest())

def sign(msg_hash, private):
    # (bytes, bytes) -> return: v,r,s to num
    d = deterministic(msg_hash, private)
    mh = bytes_to_int(msg_hash)
    r, y = mul(_G, d)
    s = inverse(d, _n) * (mh + r * bytes_to_int(private)) % _n
    v, r, s = 27 + ((y % 2) ^ (0 if s * 2 < _n else 1)), r, s if s * 2 < _n else _n - s
    return v, r, s

def recover(msg_hash, vrs):
    # (bytes, tuple()) -> return: tuple(num, num)
    mh = bytes_to_int(msg_hash)
    v, r, s = vrs
    if not (27 <= v <= 34):
        raise ValueError("v[%d] not in range 27 ~ 34" % v)
    x = r
    xmrx= (x * x * x + _a * x + _b) % _p
    u = pow(xmrx, (_p + 1) // 4, _p)
    y = u if v % 2 ^ u % 2 else (_p - u)

    if (xmrx - y * y) % _p != 0 or not (r % _n) or not (s % _n):
        return False
    G = j_mul((_Gx, _Gy, 1), (_n - mh) % _n)
    xy = j_mul((x, y, 1), s)
    Qa = j_add(G, xy)
    J = j_mul(Qa, inverse(r, _n))
    J = from_j(J)

    return J

