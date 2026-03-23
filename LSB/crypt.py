import os
import binascii
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key_hex):
        self.bs = AES.block_size  # 16 bytes
        # Konversi hex string ke bytes untuk kunci AES
        key_bytes = binascii.unhexlify(key_hex)
        if len(key_bytes) != 16:
            raise ValueError("AES key harus 16 byte (32 hex karakter).")
        # Simpan kunci AES dalam bentuk bytes 
        self.key = key_bytes  # pakai key 16-byte

    def encrypt(self, raw):
        raw = self._pad(raw) # melakukan padding pada plaintext
        iv = Random.new().read(self.bs) # generate IV acak untuk setiap enkripsi
        cipher = AES.new(self.key, AES.MODE_CBC, iv) # buat cipher dengan mode CBC
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
        # Pisahkan IV dari data terenkripsi
        iv = enc[:self.bs]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # Mengirimkan hasil dekripsi ke fungsi unpad
        return self._unpad(cipher.decrypt(enc[self.bs:]))

    def _pad(self, data):
        # Menghitung jumlah byte yang diperlukan
        padding_len = self.bs - len(data) % self.bs
        # Menambahkan byte padding sesuai skema PKCS#7
        padding = bytes([padding_len]) * padding_len
        return data + padding

    @staticmethod
    def _unpad(data):
        # Mengambil nilai byte terakhir untuk menentukan jumlah padding
        padding_len = data[-1]
        if padding_len < 1 or padding_len > 16:
            raise ValueError("Padding tidak valid.")
        return data[:-padding_len]


def generate_encryption_key():
    # 16 byte random -> simpan sebagai hex string (32 karakter)
    return os.urandom(16).hex()