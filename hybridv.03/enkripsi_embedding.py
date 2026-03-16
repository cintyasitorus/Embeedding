import os
import binascii
import cv2, time
from Crypto.Random import get_random_bytes
from modul_kripto import AESCipher128
from modul_stego import embed_hybrid

DATASET_DIR = "dataset"
IMAGE_CAPACITY = {
    "128 x 128": 16384,
    "256 x 256": 65536,
    "512 x 512": 262144,
    "1024 x 1024": 1048576
}

def pilih_folder():
    folders = [f for f in os.listdir(DATASET_DIR) if f in IMAGE_CAPACITY]
    folders.sort(key=lambda x: int(x.split(' ')[0]))
    print("\n[1] PILIH RESOLUSI:")
    for i, f in enumerate(folders):
        print(f"{i+1}. {f}")
    pilihan = int(input("Pilih nomor (1-4): "))
    return folders[pilihan-1]

def main():
    print("=== SISTEM PENGAMANAN DATA CITRA (AES-CBC + HYBRID STEGO) ===")
    
    # 1. Pilih Resolusi & Folder
    folder_res = pilih_folder()
    print(f"\n[2] FOLDER AKTIF: {folder_res}") 
    
    # 2. Input Gambar Cover .png
    nama_base_img = input("Ketik nama file gambar (tanpa .png, cth: image): ").strip()
    image_path = os.path.join(DATASET_DIR, folder_res, f"{nama_base_img}.png")

    if not os.path.exists(image_path):
        print(f"[Error] File {image_path} tidak ditemukan!")
        return

    # 3. Membaca Pesan dari File .txt 
    nama_base_txt = input("Masukkan nama file pesan (tanpa .txt, cth: pesan): ").strip()
    path_txt = f"{nama_base_txt}.txt"
    
    try:
        with open(path_txt, 'r', encoding='utf-8') as f:
            pesan = f.read()
    except FileNotFoundError:
        print(f"[Error] File {path_txt} tidak ditemukan!")
        return

    # 4. Proses Enkripsi AES-128 CBC
    print("\n[*] Memulai proses Enkripsi AES...")
    # --- Stopwatch Total Mulai ---
    waktu_mulai_encoding = time.time()

    key = get_random_bytes(16)
    cipher_aes = AESCipher128(key)
    bitstream = cipher_aes.encrypt_to_bitstream(pesan)
    key_hex = binascii.hexlify(key).decode()

    # 5. Proses Embedding Hybrid
    print("\n[*] Memulai proses Penyisipan (Edge Detection & LSB)...")
    stgo_img, log_koordinat, total_bits = embed_hybrid(image_path, bitstream, key)
    
    # --- Stopwatch Total Berhenti ---
    waktu_selesai_encoding = time.time() 
    total_encoding_time = waktu_selesai_encoding - waktu_mulai_encoding
    
    # 6. Simpan Hasil
    output_dir = os.path.join("hasil_stego", folder_res)
    if not os.path.exists(output_dir): 
        os.makedirs(output_dir)
        
    # Menggunakan nama_base_img agar konsisten
    path_stego = os.path.join(output_dir, f"{nama_base_img}_stego.png")
    path_key = os.path.join(output_dir, f"{nama_base_img}_key.txt")
    
    cv2.imwrite(path_stego, stgo_img)
    
    with open(path_key, 'w') as f:
        f.write(f"AES_KEY:{key_hex}\n")
        f.write(f"TOTAL_BITS:{total_bits}\n")
        f.write("\n".join(log_koordinat))
        
    print(f"\n[Sukses] Stego Image & Key File disimpan di: {output_dir}")
    print(f"Total bit terenkripsi yang disisipkan: {total_bits} bit")
    print(f"Waktu total encoding: {total_encoding_time:.2f} detik")

if __name__ == "__main__":
    main()