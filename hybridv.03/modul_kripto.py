import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class AESCipher128:
    def __init__(self, key):
        self.key = key  # Kunci 16 byte (AES-128)

    def encrypt_to_bitstream(self, plaintext):
        """
        Menghasilkan Bitstream dari Plaintext
        """
        # 1. Inisialisasi Cipher AES mode CBC (Otomatis buat IV acak)
        cipher = AES.new(self.key, AES.MODE_CBC)
        iv = cipher.iv
        
        # 2. Padding PKCS#7 & Enkripsi
        padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
        ct_bytes = cipher.encrypt(padded_data)
        
        # 3. Gabungkan IV + Ciphertext (IV diletakkan di 16 byte pertama)
        full_data = iv + ct_bytes
        
        # 4. Konversi Bytes ke Bitstream String
        bitstream = ''.join(format(b, '08b') for b in full_data)
        return bitstream

    def decrypt_from_bitstream(self, bitstream, key_hex):
        """
        Mengembalikan Plaintext dari Bitstream
        """
        # 1. Konversi Kunci dari Hex ke Bytes
        key = binascii.unhexlify(key_hex)
        
        # 2. Convert to Byte Process: Konversi bitstream string ke bytearray
        data_bytes = bytearray()
        for i in range(0, len(bitstream), 8):
            byte_str = bitstream[i:i+8]
            if len(byte_str) == 8: # Pastikan blok 8 bit lengkap
                data_bytes.append(int(byte_str, 2))
        
        # 3. Pemisahan IV dan Ciphertext
        # 16 byte pertama adalah IV, sisanya adalah Ciphertext
        iv = bytes(data_bytes[:16])
        ct = bytes(data_bytes[16:])
        
        # 4. Transformasi Dekripsi AES-CBC & Operasi XOR untuk mendapatkan plaintext
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(ct)
        
        # 5. Penghapusan Padding / Unpadding PKCS#7 untuk mendapatkan plaintext asli
        pt = unpad(decrypted_data, AES.block_size)
        
        return pt.decode('utf-8')