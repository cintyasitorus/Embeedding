import os
import binascii
import cv2, time
import numpy as np                  
import matplotlib.pyplot as plt
from Crypto.Random import get_random_bytes
from modul_kripto import AESCipher128
from modul_stego import embed_hybrid


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")    # global
GAMBAR_DIR = os.path.join(DATASET_DIR, "gambar")       # folder gambar
PESAN_DIR = os.path.join(DATASET_DIR, "pesan")         # folder pesan
HASIL_DIR = os.path.join(SCRIPT_DIR, "hasil_stego")    # lokal hybrid

IMAGE_CAPACITY = {
    "128 x 128": 16384,
    "256 x 256": 65536,
    "512 x 512": 262144,
    "1024 x 1024": 1048576
}

def pilih_folder():
    """
    Menampilkan daftar folder resolusi yang tersedia dan
    mengembalikan nama folder yang dipilih pengguna
    """

    # Filter folder yang namanya sesuai dengan kunci IMAGE_CAPACITY
    folders = [f for f in os.listdir(GAMBAR_DIR) if f in IMAGE_CAPACITY]
    # Urutkan berdasarkan nilai resolusi (128, 256, 512, 1024)
    folders.sort(key=lambda x: int(x.split(' ')[0]))
    print("\n[1] PILIH RESOLUSI:")
    for i, f in enumerate(folders):
        print(f"{i+1}. {f}")
    pilihan = int(input("Pilih nomor (1-4): "))
    return folders[pilihan-1]

def visualisasi_koordinat(image_path, edge_map, log_koordinat, w, h, output_dir, nama_base_img):
    print("\n[*] Membuat visualisasi scatter plot & overlay koordinat penyisipan...")
    
    # 1. Baca Citra Asli untuk Background Overlay (Konversi BGR ke RGB)
    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 2. Ekstraksi semua koordinat tepi dari edge_map (Canny)
    coords_yx_canny = np.argwhere(edge_map == 255)
    canny_x = coords_yx_canny[:, 1] if coords_yx_canny.size > 0 else []
    canny_y = coords_yx_canny[:, 0] if coords_yx_canny.size > 0 else []

    # 3. Ekstraksi koordinat yang BENAR-BENAR disisipi dari log_koordinat
    edge_used_x, edge_used_y = [], []
    smooth_used_x, smooth_used_y = [], []
    
    for baris in log_koordinat:
        parts = baris.split(',')
        y, x, tipe = int(parts[0]), int(parts[1]), parts[2]
        if tipe == 'E':
            edge_used_x.append(x)
            edge_used_y.append(y)
        else:
            smooth_used_x.append(x)
            smooth_used_y.append(y)

    # 4. Setup Canvas Matplotlib (1 Baris, 2 Kolom)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # === PANEL 1: Scatter Plot Canny Edges (Latar Putih) ===
    if len(canny_x) > 0:
        ax1.scatter(canny_x, canny_y, s=1, c='red', marker='s', label='Piksel Tepi')
    ax1.set_xlim(0, w - 1)
    ax1.set_ylim(h - 1, 0) # y=0 di atas
    ax1.xaxis.set_ticks_position('top')
    ax1.xaxis.set_label_position('top')
    ax1.set_aspect('equal', adjustable='box')
    ax1.set_xlabel("x (kolom)")
    ax1.set_ylabel("y (baris)")
    ax1.set_title(f"1. Peta Tepi Canny\nTotal Tepi Ditemukan: {len(canny_x)} piksel", pad=20)
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.legend(loc="upper right", fontsize=9)

    # === PANEL 2: Overlay Titik Penyisipan pada Gambar Asli ===
    # Tampilkan gambar asli sebagai background
    ax2.imshow(img_rgb)
    
    # Timpa dengan titik-titik koordinat (gunakan alpha agar agak transparan)
    if edge_used_x:
        ax2.scatter(edge_used_x, edge_used_y, s=1, c='red', marker='s', alpha=0.8, label=f'Tepi Terpakai ({len(edge_used_x)})')
    if smooth_used_x:
        ax2.scatter(smooth_used_x, smooth_used_y, s=1, c='blue', marker='s', alpha=0.8, label=f'Non-Tepi Terpakai ({len(smooth_used_x)})')
    
    # Format sumbu mengikuti gaya citra
    ax2.set_xlim(0, w - 1)
    ax2.set_ylim(h - 1, 0)
    ax2.xaxis.set_ticks_position('top')
    ax2.xaxis.set_label_position('top')
    ax2.set_aspect('equal', adjustable='box')
    ax2.set_xlabel("x (kolom)")
    ax2.set_ylabel("y (baris)")
    ax2.set_title(f"2. Overlay Aktual Penyisipan Pesan\nTotal Piksel Disisipi: {len(edge_used_x) + len(smooth_used_x)} piksel", pad=20)
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=9)

    plt.suptitle(f"Distribusi Penyisipan Steganografi Hibrida ({w} x {h})", fontsize=14, fontweight='bold', y=1.05)
    plt.tight_layout()

    # Simpan Gambar Visualisasi
    vis_path = os.path.join(output_dir, f"{nama_base_img}_scatter_plot.png")
    plt.savefig(vis_path, bbox_inches='tight', dpi=300)
    print(f"[V] Visualisasi berhasil disimpan di: {vis_path}")
    
    plt.close(fig)

def main():
    print("=== AES + EBE + LSB ===")
    
    # 1. Pilih Resolusi & Folder
    folder_res = pilih_folder()
    print(f"\n[2] FOLDER AKTIF: {folder_res}") 

    # 2. Input Gambar Cover .png
    nama_base_img = input("Ketik nama file gambar (tanpa .png, cth: image): ").strip()
    # 3. Membaca Pesan dari File .txt 
    nama_base_txt = input("Masukkan nama file pesan (tanpa .txt, cth: pesan): ").strip()


    image_path = os.path.join(GAMBAR_DIR, folder_res, f"{nama_base_img}.png")
    path_txt = os.path.join(PESAN_DIR, f"{nama_base_txt}.txt")

    # --- Stopwatch Total Mulai ---
    waktu_mulai_encoding = time.time()

    # Cek cover dan payload
    if not os.path.exists(image_path):
        print(f"[Error] File {image_path} tidak ditemukan!")
        return

    if not os.path.exists(path_txt):
        print(f"[Error] File {path_txt} tidak ditemukan!")
        return

    try:
        with open(path_txt, "r", encoding="utf-8") as f:
            pesan = f.read()
    except OSError as e:
        print(f"[Error] Gagal membaca file pesan: {e}")
        return

    # 4. Proses Enkripsi AES-128 CBC
    # Pesan dienkripsi menggunakan kunci acak 16 byte (128-bit)
    # Output berupa bitstream string siap sisip
    print("\n[*] Memulai proses Enkripsi AES...")
    

    # Generate kunci acak 16 byte (128-bit) untuk AES
    key = get_random_bytes(16)
    
    # Inisialisasi objek modul kriptografi dengan kunci yang telah digenerate
    cipher_aes = AESCipher128(key)
    
    # Enkripsi pesan dan konversi hasil ke bitstream string
    bitstream = cipher_aes.encrypt_to_bitstream(pesan)
    
    # Simpan kunci dalam format hex untuk disimpan ke file key
    key_hex = binascii.hexlify(key).decode()

    # 5. Proses Embedding Hybrid (EBE + LSB)
    print("\n[*] Memulai proses Penyisipan (Edge Detection & LSB)...")
    stgo_img, log_koordinat, total_bits, edge_map = embed_hybrid(image_path, bitstream, key)
    
    # Dapatkan dimensi gambar
    h, w = stgo_img.shape[:2]

    # 6. Simpan Hasil
    # Stego image disimpan sebagai .png
    # Key file menyimpan kunci AES, total bit, dan log koordinat
    output_dir = os.path.join(HASIL_DIR, folder_res)
    os.makedirs(output_dir, exist_ok=True)
        
    # Menggunakan nama_base_img agar konsisten
    path_stego = os.path.join(output_dir, f"{nama_base_img}_stego.png")
    path_key = os.path.join(output_dir, f"{nama_base_img}_key.txt")
    
    cv2.imwrite(path_stego, stgo_img)
    
    # Simpan kunci AES, total bit yang disisipkan, dan log koordinat penyisipan
    with open(path_key, 'w') as f:
        f.write(f"AES_KEY:{key_hex}\n")
        f.write(f"TOTAL_BITS:{total_bits}\n")
        f.write("\n".join(log_koordinat))

    # Panggil fungsi visualisasi di sini
    visualisasi_koordinat(image_path,edge_map, log_koordinat, w, h, output_dir, nama_base_img)

    # --- Stopwatch Total Berhenti ---
    total_encoding_time = time.time() - waktu_mulai_encoding
        
    print(f"\n[Sukses] Stego Image & Key File disimpan di: {output_dir}")
    print(f"Total bit terenkripsi yang disisipkan: {total_bits} bit")
    print(f"Waktu total encoding: {total_encoding_time:.4f} detik")

if __name__ == "__main__":
    main()