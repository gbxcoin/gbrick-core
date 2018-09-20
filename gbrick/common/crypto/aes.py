import base64
import hashlib
from Crypto.Cipher import AES


class AESCipher:
    BS = 16
    pad = (lambda s: s + (AESCipher.BS - len(s) % AESCipher.BS) * chr(AESCipher.BS - len(s) % AESCipher.BS).encode())
    un_pad = (lambda s: s[:-ord(s[len(s)-1:])])

    def __init__(self, key):
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, msg):
        raw = AESCipher.pad(msg)
        cipher = AES.new(self.key, AES.MODE_CBC, self._iv())
        encrypted = cipher.encrypt(raw)
        return base64.b64encode(encrypted)

    def decrypt(self, encrypted):
        encrypted = base64.b64decode(encrypted)
        cipher = AES.new(self.key, AES.MODE_CBC, self._iv())
        decrypted = cipher.decrypt(encrypted)
        return AESCipher.un_pad(decrypted)

    def _iv(self):
        return b' ' * 16


if __name__ == '__main__':
    c = AESCipher(b'1234')
    enc = c.encrypt(b'qwertyuiopasdfghjklzxcvbnm')
    print('encrypted: {0}'.format(enc))
    dec = c.decrypt(enc)
    print(dec.decode())
