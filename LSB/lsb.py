import os
import time
import struct
from PIL import Image
import matplotlib.pyplot as plt
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
    # Tambahkan 4 byte di depan untuk menyimpan ukuran data (payload)
    data_bytes = list(struct.pack("i", fsize)) + list(data)
    for b in data_bytes: # iterasi setiap byte, lalu dekomposisi ke bit
        for i in range(7, -1, -1): 
            v.append((b >> i) & 1)
    return v


def assemble(v):
    bytes_out = b""
    length = len(v)
    # iterasi setiap 8 bit untuk membentuk 1 byte
    for idx in range(0, len(v) // 8): 
        byte = 0
        for i in range(0, 8):
            if idx * 8 + i < length:
                byte = (byte << 1) + v[idx * 8 + i] 
        bytes_out += bytes([byte])

    # Ambil 4 byte pertama untuk mendapatkan ukuran data asli (payload)
    payload_size = struct.unpack("i", bytes_out[:4])[0]
    return bytes_out[4: payload_size + 4]


def set_bit(n, i, x):
    mask = 1 << i
    n &= ~mask # Menghapus bit pada posisi i
    if x:
        n |= mask # Menyisipkan bit x ke posisi i
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
    coords_path = os.path.join(out_dir, f"{nama_base_img}_coords.txt")

    return folder_res, nama_base_img, cover_path, payload_path, stego_path, key_path, coords_path


def build_paths_for_extract():
    folder_res = pilih_folder()
    nama_base = input("\n[2] Masukkan nama file (tanpa _stego / _key): ").strip()

    stego_path = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_stego.png")
    key_path = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_key.txt")
    coords_path = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_coords.txt")
    out_txt = os.path.join(HASIL_DIR, folder_res, f"hasil_ekstraksi_{nama_base}.txt")

    return folder_res, nama_base, stego_path, key_path, coords_path, out_txt

def _load_coords_by_channel(coords_path):
    xs_r, ys_r = [], []
    xs_g, ys_g = [], []
    xs_b, ys_b = [], []
    xs_all, ys_all = [], []

    with open(coords_path, "r", encoding="utf-8") as f:
        rows = [line.strip() for line in f.readlines() if line.strip()]

    for row in rows[1:]:
        parts = row.split(",")
        if len(parts) != 3:
            continue

        try:
            y = int(parts[0])
            x = int(parts[1])
        except ValueError:
            continue

        ch = parts[2].strip().upper()
        xs_all.append(x)
        ys_all.append(y)

        if ch == "R":
            xs_r.append(x)
            ys_r.append(y)
        elif ch == "G":
            xs_g.append(x)
            ys_g.append(y)
        elif ch == "B":
            xs_b.append(x)
            ys_b.append(y)

    return xs_all, ys_all, xs_r, ys_r, xs_g, ys_g, xs_b, ys_b


def plot_embed_scatter_from_coords(coords_path, width, height, out_plot_path):
    if not os.path.exists(coords_path):
        print(f"[X] Coords file tidak ditemukan untuk plot: {coords_path}")
        return

    xs_all, ys_all, xs_r, ys_r, xs_g, ys_g, xs_b, ys_b = _load_coords_by_channel(coords_path)

    if not xs_all:
        print("[!] Tidak ada koordinat valid untuk diplot.")
        return

    plt.figure(figsize=(8, 8))
    plt.scatter(xs_all, ys_all, s=0.25, c="black", alpha=0.20, marker="s", edgecolors="none", linewidths=0, label="All")
    if xs_r:
        plt.scatter(xs_r, ys_r, s=0.25, c="red", alpha=0.45, marker="s", edgecolors="none", linewidths=0, label="R")
    if xs_g:
        plt.scatter(xs_g, ys_g, s=0.25, c="limegreen", alpha=0.45, marker="s", edgecolors="none", linewidths=0, label="G")
    if xs_b:
        plt.scatter(xs_b, ys_b, s=0.25, c="deepskyblue", alpha=0.45, marker="s", edgecolors="none", linewidths=0, label="B")

    plt.xlim(0, width - 1)
    plt.ylim(height - 1, 0)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.gca().xaxis.set_ticks_position("top")
    plt.gca().xaxis.set_label_position("top")
    plt.xlabel("x (kolom)")
    plt.ylabel("y (baris)")
    plt.title("Sebaran Koordinat Penyisipan LSB")
    plt.grid(True, linestyle=":", alpha=0.35)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_plot_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"[V] Scatter koordinat tersimpan: {out_plot_path}")


def plot_embed_overlay_on_cover(cover_path, coords_path, out_plot_path):
    if not os.path.exists(cover_path):
        print(f"[X] Cover file tidak ditemukan untuk overlay: {cover_path}")
        return
    if not os.path.exists(coords_path):
        print(f"[X] Coords file tidak ditemukan untuk overlay: {coords_path}")
        return

    cover = Image.open(cover_path).convert("RGB")
    width, height = cover.size

    xs_all, ys_all, xs_r, ys_r, xs_g, ys_g, xs_b, ys_b = _load_coords_by_channel(coords_path)

    if not xs_all:
        print("[!] Tidak ada koordinat valid untuk overlay.")
        return

    # Marker dinamis agar tetap terlihat di 256 maupun 1024
    marker_size = 1.8 if max(width, height) >= 1024 else 3.2

    plt.figure(figsize=(8, 8))
    plt.imshow(cover)

    # Warna dibuat kontras terhadap background foto alam
    if xs_r:
        plt.scatter(xs_r, ys_r, s=marker_size, c="red", alpha=0.95, marker="s",
                    edgecolors="none", linewidths=0, label=f"R ({len(xs_r)})")
    if xs_g:
        plt.scatter(xs_g, ys_g, s=marker_size, c="green", alpha=0.95, marker="s",
                    edgecolors="none", linewidths=0, label=f"G ({len(xs_g)})")
    if xs_b:
        plt.scatter(xs_b, ys_b, s=marker_size, c="blue", alpha=0.95, marker="s",
                    edgecolors="none", linewidths=0, label=f"B ({len(xs_b)})")

    plt.xlim(0, width - 1)
    plt.ylim(height - 1, 0)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.gca().xaxis.set_ticks_position("top")
    plt.gca().xaxis.set_label_position("top")
    plt.xlabel("x (kolom)")
    plt.ylabel("y (baris)")
    plt.title("Overlay Koordinat Penyisipan pada Cover Image")
    plt.grid(True, linestyle=":", alpha=0.35)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_plot_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"[V] Overlay koordinat pada cover tersimpan: {out_plot_path}")


def embed(cover_path, payload_path, stego_path, key_path, coords_path):
    start_time = time.time()

    if not os.path.exists(cover_path):
        print(f"[X] Cover tidak ditemukan: {cover_path}")
        return None
    if not os.path.exists(payload_path):
        print(f"[X] Payload tidak ditemukan: {payload_path}")
        return None

    # Membuka citra dan menyiapkan data piksel
    img = Image.open(cover_path)
    width, height = img.size

    # Mengonversi ke RGB untuk memastikan 3 kanal warna (R, G, B)
    conv = img.convert("RGB").getdata()
    print(f"[*] Input image size: {width}x{height} pixels.")


    # Menghitung kapasitas maksimum (3 bit per piksel)
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

    # Cek apakah payload melebihi kapasitas maksimum
    payload_size_kb = len(v) / 8 / 1024
    if payload_size_kb > max_size_kb - 4:
        print("[-] Cannot embed. File too large")
        return None

    # Menyisipkan bit ke LSB dari setiap kanal warna
    steg_img = Image.new("RGB", (width, height))
    idx = 0

    # Log koordinat hanya untuk bit ciphertext asli (tanpa padding tambahan)
    coords_log = []
    logged_bits = 0

    for h in range(height):
        for w in range(width):
            r, g, b = conv.getpixel((w, h))
            if idx + 2 < len(v):
                r = set_bit(r, 0, v[idx])
                if logged_bits < total_bits:
                    coords_log.append(f"{h},{w},R")
                    logged_bits += 1

                g = set_bit(g, 0, v[idx + 1])
                if logged_bits < total_bits:
                    coords_log.append(f"{h},{w},G")
                    logged_bits += 1

                b = set_bit(b, 0, v[idx + 2])
                if logged_bits < total_bits:
                    coords_log.append(f"{h},{w},B")
                    logged_bits += 1

            steg_img.putpixel((w, h), (r, g, b))
            idx += 3

    steg_img.save(stego_path, "PNG")

    with open(key_path, "w", encoding="utf-8") as f:
        f.write(f"AES_KEY:{key_hex}\n")
        f.write(f"TOTAL_BITS:{total_bits}\n")

    # Simpan file koordinat penyisipan
    with open(coords_path, "w", encoding="utf-8") as f:
        f.write("y,x,channel\n")
        f.write("\n".join(coords_log))

    overlay_path = os.path.splitext(coords_path)[0] + "_overlay.png"
    plot_embed_overlay_on_cover(cover_path, coords_path, overlay_path)

    embed_time = time.time() - start_time
    print(f"[V] Embed sukses: {stego_path}")
    print(f"[V] Key file: {key_path}")
    print(f"[V] Waktu embed: {embed_time:.4f} detik")
    return embed_time


def extract(stego_path, key_path, coords_path, out_file):
    start_time = time.time()

    if not os.path.exists(stego_path):
        print(f"[X] Stego tidak ditemukan: {stego_path}")
        return None
    if not os.path.exists(key_path):
        print(f"[X] Key file tidak ditemukan: {key_path}")
        return None
    if not os.path.exists(coords_path):
        print(f"[X] Coords file tidak ditemukan: {coords_path}")
        return None

    # Membaca key dari file
    with open(key_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    key_hex = lines[0].split(":", 1)[1]
    total_bits = int(lines[1].split(":", 1)[1])

    # Membaca koordinat penyisipan
    with open(coords_path, "r", encoding="utf-8") as f:
        coord_lines = [line.strip() for line in f.readlines() if line.strip()]

    # Lewati header "y,x,channel"
    coords = coord_lines[1:] if coord_lines else []

    # Membuka citra stego dan menyiapkan data piksel
    img = Image.open(stego_path)
    width, height = img.size
    conv = img.convert("RGB").getdata()

    v = []
    for row in coords:
        if len(v) >= total_bits:
            break

        parts = row.split(",") 
        if len(parts) != 3:
            continue

        y = int(parts[0])
        x = int(parts[1])
        ch = parts[2].strip().upper()

        r, g, b = conv.getpixel((x, y))
        if ch == "R":
            v.append(r & 1)
        elif ch == "G":
            v.append(g & 1)
        elif ch == "B":
            v.append(b & 1)

    if len(v) < total_bits:
        print(f"[!] Peringatan: bit terkumpul {len(v)} < target {total_bits}")

    # assemble butuh kelipatan 8 bit
    if len(v) % 8 != 0:
        v.extend([0] * (8 - (len(v) % 8)))

    # Data hasil ekstraksi dalam bentuk bytes
    data_out = assemble(v)
    # Inisialisasi cipher dengan kunci yang sama untuk dekripsi
    cipher = AESCipher(key_hex)

    # Pemrosesan dekripsi data hasil ekstraksi
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
        folder_res, nama_base, cover_path, payload_path, stego_path, key_path, coords_path = build_paths_for_embed()
        embed(cover_path, payload_path, stego_path, key_path, coords_path)

    elif mode == "x":
        _, _, stego_path, key_path, coords_path, out_txt = build_paths_for_extract()
        extract(stego_path, key_path, coords_path, out_txt)

    elif mode == "t":
        print("\n[VISUAL EVALUATION]")
        evaluasi_main()
        return

    else:
        print("Unknown mode.")


if __name__ == "__main__":
    main()