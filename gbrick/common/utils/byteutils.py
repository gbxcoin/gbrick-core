
def int_to_bytes(p_val):
    result = bytearray()
    while(p_val):
        result.append(p_val & 0xff)
        p_val = p_val >> 8

    return result[::-1]


def bytes_to_int(p_val):
    return int.from_bytes(p_val, byteorder='big')
