import cv2
import numpy as np
import os, math
from skimage.metrics import structural_similarity as ssim

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")    # global
GAMBAR_DIR = os.path.join(DATASET_DIR, "gambar")       # folder gambar
HASIL_DIR = os.path.join(SCRIPT_DIR, "hasil_stego")    # lokal hybrid
RES_FOLDERS = ["128 x 128", "256 x 256", "512 x 512", "1024 x 1024"]


def hitung_kualitas_visual(path_asli, path_stego):
    # 1. Baca kedua gambar
    img_asli = cv2.imread(path_asli)
    img_stego = cv2.imread(path_stego)
    
    # Validasi jika gambar tidak ditemukan atau ukuran berbeda
    if img_asli is None or img_stego is None:
        return "Error: Gambar tidak ditemukan."
    if img_asli.shape != img_stego.shape:
        return "Error: Dimensi gambar asli dan stego berbeda!"

    # 2. Hitung MSE
    # Ubah format matriks piksel ke Float64 agar hasil pengurangan tidak error (minus)
    X = img_asli.astype(np.float64)
    Y = img_stego.astype(np.float64)

    # Hitung [X(i,j) - Y(i,j)]^2
    # Simbol ** 2 di Python melambangkan kuadrat
    kuadrat_selisih = (X - Y) ** 2

    # Hitung Rata-rata dari total kuadrat selisih (1 / m*n * Sigma)
    nilai_mse = np.mean(kuadrat_selisih)
    
    # 3. Hitung PSNR
    if nilai_mse == 0:
        nilai_psnr = float('inf') # Citra identik 100%
    else:
        # Rumus: 10 * log10 ( (255^2) / MSE )
        nilai_maksimal_piksel = 255.0
        nilai_psnr = 10 * math.log10((nilai_maksimal_piksel ** 2) / nilai_mse)
        
    # 4. Hitung SSIM
    nilai_ssim = ssim(img_asli, img_stego, channel_axis=-1, data_range=255)
    
    return nilai_mse, nilai_psnr, nilai_ssim

def main():
    print("=== PENGUJIAN KUALITAS VISUAL (MSE, PSNR, SSIM) ===")
    
    # 1. Pilih Resolusi (Menu Interaktif)
    print("\n[1] PILIH RESOLUSI GAMBAR:")
    res_folders = ["128 x 128", "256 x 256", "512 x 512", "1024 x 1024"]
    for i, folder in enumerate(res_folders):
        print(f"{i+1}. {folder}")
    
    pilihan = int(input("Pilih nomor (1-4): "))
    folder_res = res_folders[pilihan-1]
    
    # 2. Input Nama File (Otomatis tanpa .png)
    nama_base = input("\n[2] Masukkan nama file (tanpa .png, cth: image31244): ").strip()
    
    # 3. Format Path Otomatis
    path_cover = os.path.join(GAMBAR_DIR, folder_res, f"{nama_base}.png")
    path_stego = os.path.join(HASIL_DIR, folder_res, f"{nama_base}_stego.png")
    
    print(f"\n[*] Membandingkan:")
    print(f"    Asli  : {path_cover}")
    print(f"    Stego : {path_stego}")
    
    # Pengecekan keberadaan file yang lebih spesifik
    if not os.path.exists(path_cover):
        print(f"\n[X] Gagal: Gambar asli '{path_cover}' tidak ditemukan!")
        return
    if not os.path.exists(path_stego):
        print(f"\n[X] Gagal: Gambar stego '{path_stego}' tidak ditemukan!")
        return

    # 4. Jalankan Pengujian
    hasil = hitung_kualitas_visual(path_cover, path_stego)
    
    if isinstance(hasil, str):
        print(f"\n[X] {hasil}")
    else:
        nilai_mse, nilai_psnr, nilai_ssim = hasil
        print("\n=== HASIL EVALUASI ===")
        print(f"MSE  : {nilai_mse:.4f} (Semakin kecil semakin baik)")
        print(f"PSNR : {nilai_psnr:.2f} dB (Di atas 35 dB = Sangat Baik)")
        print(f"SSIM : {nilai_ssim:.4f} (Mendekati 1.0 = Sangat Mirip)")

if __name__ == "__main__":
    main()