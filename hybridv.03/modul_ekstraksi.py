import os
import cv2
from modul_kripto import AESCipher128


def read_key_log(path_log):
    with open(path_log, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) < 3:
        raise ValueError("Format file key/log tidak valid. Minimal 3 baris diperlukan.")

    key_hex = lines[0].strip().split(":", 1)[1]
    total_bits = int(lines[1].strip().split(":", 1)[1])
    coords = [line.strip().split(',') for line in lines[2:] if line.strip()]

    return key_hex, total_bits, coords


def extract_bitstream_with_coordinates(img, coords, total_bits):
    bitstream_parts = []
    bit_count = 0

    for coord in coords:
        if bit_count >= total_bits:
            break

        y = int(coord[0])
        x = int(coord[1])
        tipe = coord[2]
        huruf_kanal = coord[3].strip()

        if tipe == 'E':
            bit_r = str(img[y, x][2] & 0x01)
            bit_g = str(img[y, x][1] & 0x01)
            bit_b = str(img[y, x][0] & 0x01)
            bits = bit_r + bit_g + bit_b

            needed = total_bits - bit_count
            chunk = bits[:min(3, needed)]
            bitstream_parts.append(chunk)
            bit_count += len(chunk)
        else:
            ch = {'R': 2, 'G': 1, 'B': 0}[huruf_kanal]
            pixel_val = img[y, x][ch]
            bitstream_parts.append(str(pixel_val & 0x01))
            bit_count += 1

    return ''.join(bitstream_parts)


def extract_bitstream_blind(img, total_bits, channel_order=(2, 1, 0)):
    """
    Menarik LSB secara sekuensial tanpa koordinat.
    Default channel_order=(2,1,0) artinya urutan R,G,B.
    """
    h, w, _ = img.shape
    bitstream_parts = []
    bit_count = 0

    for y in range(h):
        for x in range(w):
            for ch in channel_order:
                if bit_count >= total_bits:
                    return ''.join(bitstream_parts)
                bitstream_parts.append(str(img[y, x][ch] & 0x01))
                bit_count += 1

    return ''.join(bitstream_parts)


def calculate_ber(bitstream_original, bitstream_extracted):
    n = min(len(bitstream_original), len(bitstream_extracted))
    if n == 0:
        return {
            "n": 0,
            "error_bits": 0,
            "ber_ratio": 0.0,
            "ber_percent": 0.0,
        }

    error_bits = sum(1 for i in range(n) if bitstream_original[i] != bitstream_extracted[i])
    ber_ratio = error_bits / n
    ber_percent = ber_ratio * 100.0

    return {
        "n": n,
        "error_bits": error_bits,
        "ber_ratio": ber_ratio,
        "ber_percent": ber_percent,
    }


def bitstream_to_ciphertext_hex(bitstream):
    """
    Konversi bitstream ke representasi hex per-byte.
    Hanya bit penuh 8-bit yang diproses agar valid sebagai byte.
    """
    full_bytes_len = (len(bitstream) // 8) * 8
    valid_bits = bitstream[:full_bytes_len]

    data_bytes = bytearray()
    for i in range(0, len(valid_bits), 8):
        data_bytes.append(int(valid_bits[i:i + 8], 2))

    return bytes(data_bytes).hex(), full_bytes_len


def decrypt_bitstream(bitstream, key_hex):
    cipher_aes = AESCipher128(None)
    return cipher_aes.decrypt_from_bitstream(bitstream, key_hex)


def save_text_file(path_output, content):
    os.makedirs(os.path.dirname(path_output), exist_ok=True)
    with open(path_output, 'w', encoding='utf-8') as f:
        f.write(content)


def read_image(path_stego):
    img = cv2.imread(path_stego)
    if img is None:
        raise ValueError(f"Gagal membaca gambar stego: {path_stego}")
    return img
