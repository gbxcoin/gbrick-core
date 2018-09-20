from gbrick.common.crypto.hash import *


def merkleroot(p_list: list):
    if p_list.__len__() == 0:
        raise BaseException('list length cannot be 0')

    if p_list.__len__() == 1:
        return p_list[0]

    if p_list.__len__() % 2 != 0:
        p_list.append(p_list[p_list.__len__()-1])

    new_list = []
    length = p_list.__len__() / 2
    for i in range(0, int(length)):
        o = (to_gbrick_hash(p_list[i*2] + p_list[i*2+1]))
        new_list.append(o)

    return merkleroot(new_list)

