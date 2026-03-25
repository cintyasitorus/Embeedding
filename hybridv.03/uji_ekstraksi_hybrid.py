import os
import time
from modul_ekstraksi_hybrid import (
    read_key_log,
    read_image,
    extract_bitstream_with_coordinates,
    extract_bitstream_blind,
    calculate_ber,
    decrypt_bitstream,
    bitstream_to_ciphertext_hex,
    save_text_file,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

HASIL_DIR = os.path.join(SCRIPT_DIR, "hasil_stego")    # lokal hybrid
RES_FOLDERS = ["128 x 128", "256 x 256", "512 x 512", "1024 x 1024"]


def analisis_keterbacaan_teks(teks):
    if not teks:
        return 0.0

    printable_count = sum(1 for ch in teks if ch.isprintable() or ch in "\n\r\t")
    return printable_count / len(teks)


def baris_info(label, value, width=32):
    return f"{label:<{width}}: {value}\n"


def ringkasan_ciphertext(bitstream):
    ciphertext_hex, full_bytes_len = bitstream_to_ciphertext_hex(bitstream)
    return (
        baris_info("Panjang bitstream", len(bitstream))
        + baris_info("Bit valid untuk byte", full_bytes_len)
        + baris_info("Panjang ciphertext hex", len(ciphertext_hex))
        + "\n"
        + "[CIPHERTEXT_HEX_UTUH]\n"
        + f"{ciphertext_hex}\n"
        + "\n"
        + "[BITSTREAM_UTUH]\n"
        + f"{bitstream}\n"
    )


def pilih_mode_operasi():
    print("\n[MODE OPERASI]:")
    print("1. Normal Extraction : Legitimate User")
    print("2. Blind Extraction : Attacker")
    pilihan = int(input("Pilih mode (1-2): "))
    if pilihan not in [1, 2]:
        raise ValueError("Pilihan mode tidak valid.")
    return pilihan

def main():
    print("=== EKSTRAKSI / DEKRIPSI / EVALUASI BER ===")
    try:
        mode = pilih_mode_operasi()
    except ValueError as e:
        print(f"\n[X] GAGAL: {e}")
        return
    
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
    
    # --- Stopwatch Total Mulai ---
    waktu_mulai_decoding = time.time()

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

    if mode == 1:
        print("[*] Melakukan dekripsi pesan (AES-128 CBC)...")
        try:
            pesan_asli = decrypt_bitstream(bitstream, key_hex)

            # BER pembanding internal legitimate vs legitimate (harus 0%)
            hasil_ber_legit = calculate_ber(bitstream, bitstream)

            # --- Stopwatch Total Berhenti ---
            waktu_selesai_decoding = time.time()
            total_decoding_time = waktu_selesai_decoding - waktu_mulai_decoding

            nama_output = os.path.join(HASIL_DIR, folder_res, f"hasil_ekstraksi_{nama_base}.txt")
            path_laporan_legit = os.path.join(HASIL_DIR, folder_res, f"laporan_ber_normal_{nama_base}.txt")

            save_text_file(nama_output, pesan_asli)

            laporan_legit = (
                "=== LAPORAN BER NORMAL EXTRACTION ===\n"
                + baris_info("Nama basis file", nama_base)
                + baris_info("Resolusi", folder_res)
                + baris_info("Total bit target (TOTAL_BITS)", total_bits)
                + baris_info("n bit yang dibandingkan", hasil_ber_legit['n'])
                + baris_info("Jumlah bit salah", hasil_ber_legit['error_bits'])
                + baris_info("BER (rasio)", f"{hasil_ber_legit['ber_ratio']:.6f}")
                + baris_info("BER (%)", f"{hasil_ber_legit['ber_percent']:.4f}%")
                + "\n"
                + "=== RINGKASAN CIPHERTEXT LEGITIMATE ===\n"
                + ringkasan_ciphertext(bitstream)
                + "\n"
                + "Catatan\n"
                + "BER normal dihitung terhadap bitstream legitimate itu sendiri sebagai baseline, sehingga targetnya 0%.\n"
            )
            save_text_file(path_laporan_legit, laporan_legit)

            print(f"\n[V] SUKSES! Ekstraksi dan Dekripsi berhasil.")
            print(f"Waktu total decoding: {total_decoding_time:.4f} detik")
            print(f"Pesan Anda sudah dikembalikan dan disimpan di: {nama_output}")
            print(f"Laporan BER legit disimpan di: {path_laporan_legit}")
            print(f"BER legit (target 0%): {hasil_ber_legit['ber_percent']:.4f}%")
        except Exception as e:
            print(f"\n[X] GAGAL DEKRIPSI: {e}")
            print("Penyebab umum: Gambar Stego rusak/terkompresi, atau kunci tidak cocok.")

    else:
        print("[*] Menjalankan blind extraction (tanpa koordinat)...")
        blind_bits = extract_bitstream_blind(img, total_bits, channel_order=(2, 1, 0))

        hasil_ber = calculate_ber(bitstream, blind_bits)

        path_laporan = os.path.join(HASIL_DIR, folder_res, f"laporan_ber_blind_{nama_base}.txt")

        # Uji pembuktian: coba dekripsi blind ciphertext dengan AES key asli.
        # Hasil normalnya gagal (mis. unpadding error) atau lolos tapi output noise.
        dekripsi_blind_status = "GAGAL"
        dekripsi_blind_catatan = ""
        path_blind_dekripsi = os.path.join(HASIL_DIR, folder_res, f"hasil_dekripsi_blind_{nama_base}.txt")
        try:
            blind_plaintext = decrypt_bitstream(blind_bits, key_hex)
            skor_keterbacaan = analisis_keterbacaan_teks(blind_plaintext)

            if skor_keterbacaan >= 0.95:
                kategori = "kemungkinan terbaca (tetap perlu verifikasi manual)"
            else:
                kategori = "kemungkinan tidak bermakna/noise"

            dekripsi_blind_status = "BERHASIL_SECARA_TEKNIS"
            dekripsi_blind_catatan = (
                f"Dekripsi blind lolos tanpa exception. Skor keterbacaan={skor_keterbacaan:.4f} ({kategori})."
            )

            save_text_file(path_blind_dekripsi, blind_plaintext)
        except Exception as e:
            dekripsi_blind_status = "GAGAL_UNPADDING_ATAU_FORMAT"
            dekripsi_blind_catatan = f"Dekripsi blind gagal: {e}"

        laporan = (
            "=== LAPORAN BER BLIND EXTRACTION ===\n"
            + baris_info("Nama basis file", nama_base)
            + baris_info("Resolusi", folder_res)
            + baris_info("Total bit target (TOTAL_BITS)", total_bits)
            + baris_info("n bit yang dibandingkan", hasil_ber['n'])
            + baris_info("Jumlah bit salah", hasil_ber['error_bits'])
            + baris_info("BER (rasio)", f"{hasil_ber['ber_ratio']:.6f}")
            + baris_info("BER (%)", f"{hasil_ber['ber_percent']:.4f}%")
            + "\n"
            + "=== RINGKASAN CIPHERTEXT LEGITIMATE ===\n"
            + ringkasan_ciphertext(bitstream)
            + "\n"
            + "=== RINGKASAN CIPHERTEXT BLIND ===\n"
            + ringkasan_ciphertext(blind_bits)
            + "\n"
            + "=== UJI DEKRIPSI BLIND DENGAN AES_KEY ASLI ===\n"
            + baris_info("Status dekripsi blind", dekripsi_blind_status)
            + baris_info("Catatan", dekripsi_blind_catatan)
            + "\n"
            + "Catatan\n"
            + "BER blind dihitung dengan XOR per-bit antara ciphertext legitimate extraction dan ciphertext blind extraction.\n"
        )
        save_text_file(path_laporan, laporan)

        waktu_selesai = time.time()
        total_waktu = waktu_selesai - waktu_mulai_decoding

        print("\n[V] SUKSES! Evaluasi blind extraction + BER selesai.")
        print(f"Waktu total evaluasi: {total_waktu:.4f} detik")
        print(f"BER (rasio): {hasil_ber['ber_ratio']:.6f}")
        print(f"BER (%): {hasil_ber['ber_percent']:.4f}%")
        print(f"Status dekripsi blind: {dekripsi_blind_status}")
        if dekripsi_blind_status == "BERHASIL_SECARA_TEKNIS":
            print(f"Hasil dekripsi blind disimpan di: {path_blind_dekripsi}")
        print(f"Laporan BER disimpan di: {path_laporan}")
        
if __name__ == "__main__":
    main()