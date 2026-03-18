import os
import binascii
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key_hex):
        self.bs = AES.block_size  # 16 bytes
        key_bytes = binascii.unhexlify(key_hex)
        if len(key_bytes) != 16:
            raise ValueError("AES key harus 16 byte (32 hex karakter).")
        self.key = key_bytes  # pakai key 16-byte langsung, tanpa hashing

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(self.bs)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
        iv = enc[:self.bs]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[self.bs:]))

    def _pad(self, data):
        padding_len = self.bs - len(data) % self.bs
        padding = bytes([padding_len]) * padding_len
        return data + padding

    @staticmethod
    def _unpad(data):
        padding_len = data[-1]
        if padding_len < 1 or padding_len > 16:
            raise ValueError("Padding tidak valid.")
        return data[:-padding_len]


def generate_encryption_key():
    # 16 byte random -> simpan sebagai hex string (32 karakter)
    return os.urandom(16).hex()