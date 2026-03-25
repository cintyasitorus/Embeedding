import cv2
import os
import time
from modul_kripto import AESCipher128

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

HASIL_DIR = os.path.join(SCRIPT_DIR, "hasil_stego")    # lokal hybrid
RES_FOLDERS = ["128 x 128", "256 x 256", "512 x 512", "1024 x 1024"]

def main():
    print("=== EKSTRAKSI & DEKRIPSI PESAN ===")

    # 1. Pilih Resolusi 
    print("\n[1] PILIH RESOLUSI GAMBAR:")
    for i, folder in enumerate(RES_FOLDERS):
        print(f"{i+1}. {folder}")

    pilihan = int(input("Pilih nomor (1-4): "))
    folder_res = RES_FOLDERS[pilihan - 1]
    
    # 2. Input Nama File (Otomatis mencari stego.png dan key.txt)
    nama_base = input("\n[2] Masukkan nama file (tanpa .png/.txt, cth: image): ").strip()
    
    path_stego = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_stego.png")
    path_log = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_key.txt")

    # --- Stopwatch Total Mulai ---
    waktu_mulai_decoding = time.time()

    if not os.path.exists(path_stego) or not os.path.exists(path_log):
        print(f"\n[X] GAGAL: File tidak ditemukan!")
        print(f"Pastikan {path_stego} dan {path_log} ada di folder.")
        return

    # 3. Proses Pembacaan Log Kunci
    print(f"\n[*] Membaca kunci dari: {path_log}...")
    # Membuka file log (.txt) dalam mode baca ('r') secara aman
    with open(path_log, "r", encoding="utf-8") as f:
        lines = f.readlines() # Membaca seluruh isi file teks dan menyimpannya ke dalam list 'lines'
    
    # Mengambil string kunci AES dari baris pertama (indeks 0) setelah tanda ':'
    key_hex = lines[0].strip().split(":")[1]
    
    # Mengambil angka total bit dari baris kedua (indeks 1) lalu diubah ke tipe integer
    total_bits = int(lines[1].strip().split(":")[1])
    
    # Memecah seluruh baris sisanya (indeks 2 ke bawah) berdasarkan tanda koma menjadi list koordinat
    coords = [line.strip().split(',') for line in lines[2:]]

    # 4. Ekstraksi Bit dari Piksel Gambar
    print(f"[*] Mengekstraksi {total_bits} bit dari gambar...")
    

    img = cv2.imread(path_stego)
    bitstream = ""
    bit_count = 0
    
    for coord in coords:
        if bit_count >= total_bits: break
        y = int(coord[0])
        x = int(coord[1])
        tipe = coord[2]
        huruf_kanal = coord[3].strip() 
        
        if tipe == 'E':
            # --- EKSTRAKSI TEPI (Ambil 1 bit dari R, G, B) ---
            # Ingat: OpenCV menggunakan format B=0, G=1, R=2
            bit_r = str(img[y, x][2] & 0x01)
            bit_g = str(img[y, x][1] & 0x01)
            bit_b = str(img[y, x][0] & 0x01)
            
            # Gabungkan ketiga bit menjadi satu urutan asli
            bits = bit_r + bit_g + bit_b
            
            needed = total_bits - bit_count
            bitstream += bits[:min(3, needed)]
            bit_count += min(3, needed)
            
        else:
            # --- EKSTRAKSI NON-TEPI (Tetap 1 bit di kanal yang terpilih) ---
            ch = {'R': 2, 'G': 1, 'B': 0}[huruf_kanal]
            pixel_val = img[y, x][ch]
            
            bitstream += str(pixel_val & 0x01)
            bit_count += 1

    # --- PENGECEKAN JUMLAH BIT ---
    print(f"[*] Status Ekstraksi Piksel: Terkumpul {len(bitstream)} bit (Target: {total_bits} bit)")
    if len(bitstream) != total_bits:
        print("[!] PERINGATAN: Jumlah bit yang diekstrak tidak sesuai target!")

    # 5. Dekripsi AES
    print("[*] Melakukan dekripsi pesan (AES-128 CBC)...")
    try:
        cipher_aes = AESCipher128(None)
        pesan_asli = cipher_aes.decrypt_from_bitstream(bitstream, key_hex)
        
        # Simpan hasilnya ke file teks baru di dalam folder hasil_stego
        nama_output = os.path.join(HASIL_DIR, folder_res, f"hasil_ekstraksi_{nama_base}.txt")
        
        with open(nama_output, 'w', encoding='utf-8') as f:
            f.write(pesan_asli)

        # --- Stopwatch Total Berhenti ---
        total_decoding_time = time.time() - waktu_mulai_decoding
            
        print(f"\n[V] SUKSES! Ekstraksi dan Dekripsi berhasil.")
        print(f"Waktu total decoding: {total_decoding_time:.4f} detik")
        print(f"Pesan Anda sudah dikembalikan dan disimpan di: {nama_output}")
        
    except Exception as e:
        print(f"\n[X] GAGAL DEKRIPSI: {e}")
        print("Penyebab umum: Gambar Stego rusak/terkompresi, atau kunci tidak cocok.")
        
if __name__ == "__main__":
    main()