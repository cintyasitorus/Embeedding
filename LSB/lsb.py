import os
import time
import struct
from PIL import Image
from evaluasi_visual import main as evaluasi_main
from crypt import AESCipher, generate_encryption_key

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")    # global
GAMBAR_DIR = os.path.join(DATASET_DIR, "gambar")       # folder gambar
PESAN_DIR = os.path.join(DATASET_DIR, "pesan")         # folder pesan
HASIL_DIR = os.path.join(SCRIPT_DIR, "hasil_stego")    # lokal LSB
RES_FOLDERS = ["128 x 128", "256 x 256", "512 x 512", "1024 x 1024"]

def decompose(data):
    v = []
    fsize = len(data)
    data_bytes = list(struct.pack("i", fsize)) + list(data)
    for b in data_bytes:
        for i in range(7, -1, -1):
            v.append((b >> i) & 1)
    return v


def assemble(v):
    bytes_out = b""
    length = len(v)
    for idx in range(0, len(v) // 8):
        byte = 0
        for i in range(0, 8):
            if idx * 8 + i < length:
                byte = (byte << 1) + v[idx * 8 + i]
        bytes_out += bytes([byte])

    payload_size = struct.unpack("i", bytes_out[:4])[0]
    return bytes_out[4: payload_size + 4]


def set_bit(n, i, x):
    mask = 1 << i
    n &= ~mask
    if x:
        n |= mask
    return n


def pilih_folder():
    print("\n[1] PILIH RESOLUSI GAMBAR:")
    for i, folder in enumerate(RES_FOLDERS):
        print(f"{i+1}. {folder}")
    pilihan = int(input("Pilih nomor (1-4): ").strip())
    return RES_FOLDERS[pilihan - 1]


def build_paths_for_embed():
    folder_res = pilih_folder()
    nama_base_img = input("\n[2] Nama file gambar (tanpa .png): ").strip()
    nama_base_txt = input("[3] Nama file pesan (tanpa .txt): ").strip()

    cover_path = os.path.join(GAMBAR_DIR, folder_res, f"{nama_base_img}.png")
    payload_path = os.path.join(PESAN_DIR, f"{nama_base_txt}.txt")

    out_dir = os.path.join(HASIL_DIR, folder_res)
    os.makedirs(out_dir, exist_ok=True)

    stego_path = os.path.join(out_dir, f"{nama_base_img}_stego.png")
    key_path = os.path.join(out_dir, f"{nama_base_img}_key.txt")

    return folder_res, nama_base_img, cover_path, payload_path, stego_path, key_path


def build_paths_for_extract():
    folder_res = pilih_folder()
    nama_base = input("\n[2] Masukkan nama file (tanpa _stego / _key): ").strip()

    stego_path = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_stego.png")
    key_path = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_key.txt")
    out_txt = os.path.join(HASIL_DIR, folder_res, f"hasil_ekstraksi_{nama_base}.txt")

    return folder_res, nama_base, stego_path, key_path, out_txt


def embed(cover_path, payload_path, stego_path, key_path):
    start_time = time.time()

    if not os.path.exists(cover_path):
        print(f"[X] Cover tidak ditemukan: {cover_path}")
        return None
    if not os.path.exists(payload_path):
        print(f"[X] Payload tidak ditemukan: {payload_path}")
        return None

    img = Image.open(cover_path)
    width, height = img.size
    conv = img.convert("RGB").getdata()
    print(f"[*] Input image size: {width}x{height} pixels.")

    max_size_bits = width * height * 3
    max_size_kb = max_size_bits / 8 / 1024
    print(f"[*] Usable payload size: {max_size_kb:.2f} KB ({max_size_bits} bits)")

    with open(payload_path, "rb") as f:
        data = f.read()

    key_hex = generate_encryption_key()
    cipher = AESCipher(key_hex)
    data_enc = cipher.encrypt(data)

    v = decompose(data_enc)
    total_bits = len(v)

    # pad kelipatan 3 agar muat di channel RGB
    while len(v) % 3:
        v.append(0)

    payload_size_kb = len(v) / 8 / 1024
    if payload_size_kb > max_size_kb - 4:
        print("[-] Cannot embed. File too large")
        return None

    steg_img = Image.new("RGB", (width, height))
    idx = 0
    for h in range(height):
        for w in range(width):
            r, g, b = conv.getpixel((w, h))
            if idx + 2 < len(v):
                r = set_bit(r, 0, v[idx])
                g = set_bit(g, 0, v[idx + 1])
                b = set_bit(b, 0, v[idx + 2])
            steg_img.putpixel((w, h), (r, g, b))
            idx += 3

    steg_img.save(stego_path, "PNG")

    with open(key_path, "w", encoding="utf-8") as f:
        f.write(f"AES_KEY:{key_hex}\n")
        f.write(f"TOTAL_BITS:{total_bits}\n")

    embed_time = time.time() - start_time
    print(f"[V] Embed sukses: {stego_path}")
    print(f"[V] Key file: {key_path}")
    print(f"[V] Waktu embed: {embed_time:.4f} detik")
    return embed_time


def extract(stego_path, key_path, out_file):
    start_time = time.time()

    if not os.path.exists(stego_path):
        print(f"[X] Stego tidak ditemukan: {stego_path}")
        return None
    if not os.path.exists(key_path):
        print(f"[X] Key file tidak ditemukan: {key_path}")
        return None

    with open(key_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    key_hex = lines[0].split(":", 1)[1]
    total_bits = int(lines[1].split(":", 1)[1])

    img = Image.open(stego_path)
    width, height = img.size
    conv = img.convert("RGB").getdata()

    v = []
    for h in range(height):
        for w in range(width):
            r, g, b = conv.getpixel((w, h))
            v.append(r & 1)
            v.append(g & 1)
            v.append(b & 1)
            if len(v) >= total_bits:
                break
        if len(v) >= total_bits:
            break

    # assemble butuh kelipatan 8 bit
    if len(v) % 8 != 0:
        v.extend([0] * (8 - (len(v) % 8)))

    data_out = assemble(v)
    cipher = AESCipher(key_hex)
    data_dec = cipher.decrypt(data_out)

    with open(out_file, "wb") as f:
        f.write(data_dec)

    extract_time = time.time() - start_time
    print(f"[V] Extract sukses: {out_file}")
    print(f"[V] Waktu extract: {extract_time:.4f} detik")
    return extract_time


def main():
    mode = input("\nSelect mode (e=embed, x=extract, t=test_evaluation): ").strip().lower()

    if mode == "e":
        folder_res, nama_base, cover_path, payload_path, stego_path, key_path = build_paths_for_embed()
        embed(cover_path, payload_path, stego_path, key_path)

    elif mode == "x":
        _, _, stego_path, key_path, out_txt = build_paths_for_extract()
        extract(stego_path, key_path, out_txt)

    elif mode == "t":
        print("\n[VISUAL EVALUATION]")
        evaluasi_main()
        return

    else:
        print("Unknown mode.")


if __name__ == "__main__":
    main()