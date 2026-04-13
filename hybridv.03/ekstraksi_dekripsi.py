import cv2
import os
import time
from modul_kripto import AESCipher128
from modul_ekstraksi_hybrid import (
    read_key_log,
    read_image,
    extract_bitstream_with_coordinates,
    bitstream_to_ciphertext_hex,
    save_text_file,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

HASIL_DIR = os.path.join(SCRIPT_DIR, "hasil_stego")    # lokal hybrid
RES_FOLDERS = ["128 x 128", "256 x 256", "512 x 512", "1024 x 1024"]


def ringkasan_5_komponen(nama_base, folder_res, total_bits, bitstream):
    ciphertext_hex, _ = bitstream_to_ciphertext_hex(bitstream)
    return (
        f"Nama basis file: {nama_base}\n"
        f"Resolusi: {folder_res}\n"
        f"Total_bits: {total_bits}\n"
        f"Ciphertext: {ciphertext_hex}\n"
        f"Bitstream (0 & 1): {bitstream}\n"
    )

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
    try:
        key_hex, total_bits, coords = read_key_log(path_log)
    except Exception as e:
        print(f"\n[X] GAGAL membaca key/log: {e}")
        return

    # 4. Ekstraksi Bit dari Piksel Gambar
    print(f"[*] Mengekstraksi {total_bits} bit dari gambar...")
    

    try:
        img = read_image(path_stego)
    except Exception as e:
        print(f"\n[X] GAGAL membaca gambar stego: {e}")
        return

    bitstream = extract_bitstream_with_coordinates(img, coords, total_bits)

    # --- PENGECEKAN JUMLAH BIT ---
    print(f"[*] Status Ekstraksi Piksel: Terkumpul {len(bitstream)} bit (Target: {total_bits} bit)")
    if len(bitstream) != total_bits:
        print("[!] PERINGATAN: Jumlah bit yang diekstrak tidak sesuai target!")

    # 5. Dekripsi AES
    print("[*] Melakukan dekripsi pesan (AES-128 CBC)...")
    try:
        #Inisialisasi objek dan proses dekripsi
        cipher_aes = AESCipher128(None)
        pesan_asli = cipher_aes.decrypt_from_bitstream(bitstream, key_hex)
        
        # Simpan hasilnya ke file teks baru di dalam folder hasil_stego
        # Penyimpanan hasil dekripsi ke file teks (.txt)
        nama_output = os.path.join(HASIL_DIR, folder_res, f"hasil_ekstraksi_{nama_base}.txt")
        path_output_ringkasan = os.path.join(HASIL_DIR, folder_res, f"bitstream_result_{nama_base}.txt")
        
        with open(nama_output, 'w', encoding='utf-8') as f:
            f.write(pesan_asli)

        konten_ringkasan = ringkasan_5_komponen(nama_base, folder_res, total_bits, bitstream)
        save_text_file(path_output_ringkasan, konten_ringkasan)

        # --- Stopwatch Total Berhenti ---
        total_decoding_time = time.time() - waktu_mulai_decoding
            
        print(f"\n[V] SUKSES! Ekstraksi dan Dekripsi berhasil.")
        print(f"Waktu total decoding: {total_decoding_time:.4f} detik")
        print(f"Pesan Anda sudah dikembalikan dan disimpan di: {nama_output}")
        print(f"Ringkasan ciphertext + bitstream disimpan di: {path_output_ringkasan}")
        
    except Exception as e:
        print(f"\n[X] GAGAL DEKRIPSI: {e}")
        print("Penyebab umum: Gambar Stego rusak/terkompresi, atau kunci tidak cocok.")
        
if __name__ == "__main__":
    main()