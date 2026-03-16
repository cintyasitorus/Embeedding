import cv2
import numpy as np
import random

def get_combined_edge_map(img):
    # Gaussian Blur 
    blur_img = cv2.GaussianBlur(img, (5, 5), 0)
    
    b, g, r = cv2.split(blur_img)
    edge_r = cv2.Canny(r, 50, 150)
    edge_g = cv2.Canny(g, 50, 150)
    edge_b = cv2.Canny(b, 50, 150)
    
    # Operasi OR
    combined = cv2.bitwise_or(edge_r, cv2.bitwise_or(edge_g, edge_b))
    return combined

def embed_hybrid(image_path, bitstream, aes_key):
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    
    # 1. Deteksi Tepi (Canny)
    edge_map = get_combined_edge_map(img)
    edge_coords = []
    smooth_coords = []
    
    # 2. Ekstraksi Koordinat
    for y in range(h):
        for x in range(w):
            if edge_map[y, x] == 255:
                edge_coords.append((y, x))
            else:
                smooth_coords.append((y, x))

    # 3. Persiapan PRNG untuk Pengacakan Koordinat
    seed = int.from_bytes(aes_key, "big")
    random.seed(seed)
    
    # PRNG mengacak urutan koordinat Tepi (E)
    random.shuffle(edge_coords) 
    
    # PRNG mengacak urutan koordinat Non-Tepi (S)
    random.shuffle(smooth_coords)

    # 4. Gabungkan Target: Tepi (E) dulu, lalu Smooth (S)
    targets = [(c, 'E') for c in edge_coords] + [(c, 'S') for c in smooth_coords]
    
    bit_idx = 0
    total_bits = len(bitstream)
    used_log = []
    
    # Kanal OpenCV (BGR)
    channels = [2, 1, 0] 
    huruf_kanal = {2: 'R', 1: 'G', 0: 'B'}

    for i, ((y, x), tipe) in enumerate(targets):
        if bit_idx >= total_bits: break
        
        ch = channels[i % 3] 
        kanal_str = huruf_kanal[ch]
        
        if tipe == 'E':
            # --- PENYISIPAN TEPI (1-BIT per Kanal: R, G, B) ---
            chunk = bitstream[bit_idx:bit_idx+3]
            if len(chunk) < 3:
                chunk = chunk.ljust(3, '0')
                
            # OpenCV membaca dengan format B=0, G=1, R=2
            # Modifikasi 1 bit LSB (& 0xFE) di masing-masing kanal
            img[y, x][2] = (img[y, x][2] & 0xFE) | int(chunk[0]) # Masuk ke Red
            img[y, x][1] = (img[y, x][1] & 0xFE) | int(chunk[1]) # Masuk ke Green
            img[y, x][0] = (img[y, x][0] & 0xFE) | int(chunk[2]) # Masuk ke Blue
            
            used_log.append(f"{y},{x},E,RGB") # Di log ditulis 'RGB' karena pakai ketiganya
            bit_idx += 3
            
        else:
            bit = int(bitstream[bit_idx])
            img[y, x][ch] = (img[y, x][ch] & 0xFE) | bit
            used_log.append(f"{y},{x},S,{kanal_str}")
            bit_idx += 1

    
    # Pengecekan Kapasitas
    if bit_idx < total_bits:
        print(f"\n[X] ERROR FATAL: Kapasitas Gambar Tidak Cukup!")
        print(f"Pesan butuh {total_bits} bit, tapi gambar ini hanya muat {bit_idx} bit.")
        raise ValueError("OVERLOAD: Pesan terlalu besar untuk gambar ini.")

    # Menghitung Statistik
    total_tepi_asli = len(edge_coords)
    tepi_terpakai = sum(1 for x in used_log if ',E,' in x)
    smooth_terpakai = sum(1 for x in used_log if ',S,' in x)
    
    print(f"\n[*] LAPORAN DETEKSI GAMBAR:")
    print(f"    -> Total Tepi Asli Ditemukan (Canny) : {total_tepi_asli} piksel")
    print(f"[*] LAPORAN PENYISIPAN:")
    print(f"    -> Piksel Tepi (E) yang terpakai     : {tepi_terpakai} piksel")
    print(f"    -> Piksel Non-Tepi (S) yang terpakai : {smooth_terpakai} piksel")

    return img, used_log, total_bits