# Sistem Pengamanan Data Citra (AES-CBC + Hybrid Steganography)

Proyek ini adalah implementasi sistem keamanan data yang menggabungkan kriptografi **AES-128 Mode CBC** dengan teknik **Hybrid Steganography** (berbasis deteksi tepi/edge detection). Sistem ini mengenkripsi pesan teks dan menyembunyikannya ke dalam citra digital (PNG) dengan memprioritaskan area tepi gambar untuk menjaga kualitas visual, serta dilengkapi dengan **evaluasi waktu komputasi** untuk mengukur performa sistem.

## Struktur Folder

Berikut adalah penjelasan fungsi dari setiap file dan folder dalam proyek ini untuk mempermudah navigasi:

### Program Utama
Script yang dijalankan langsung oleh pengguna untuk melakukan proses enkripsi, dekripsi, atau evaluasi.

- **`enkripsi_embedding.py`**  
  Program untuk menyembunyikan pesan.  
  *Fungsi:* Membaca gambar cover dan file pesan -> melakukan enkripsi AES -> menyisipkan bit terenkripsi ke dalam gambar (prioritas area tepi). Mencatat **waktu komputasi** yang diperlukan untuk proses enkripsi dan penyisipan.
  *Output:* Menyimpan gambar stego (`_stego.png`) dan kunci dekripsi (`_key.txt`) di folder `hasil_stego/`.

- **`ekstraksi_dekripsi.py`**  
  Program untuk mengambil kembali pesan.  
  *Fungsi:* Membaca gambar stego dan file kunci -> mengekstraksi bit dari piksel -> melakukan dekripsi AES -> menampilkan pesan asli. Mencatat **waktu komputasi** yang diperlukan untuk proses ekstraksi dan dekripsi.

- **`evaluasi_visual.py`**  
  Program untuk pengujian kualitas citra.  
  *Fungsi:* Membandingkan gambar asli (dari `dataset/`) dengan gambar hasil stego (dari `hasil_stego/`).  
  *Metrik:* Menghitung **MSE** (Mean Squared Error), **PSNR** (Peak Signal-to-Noise Ratio), dan **SSIM** (Structural Similarity Index).

### Modul Pendukung
File ini berisi fungsi dan kelas yang diimpor oleh program utama, tidak perlu dijalankan secara langsung.

- **`modul_kripto.py`**  
  Berisi implementasi kelas `AESCipher128` untuk:
  - Enkripsi pesan (Padding PKCS#7, AES-CBC) menjadi bitstream.
  - Dekripsi bitstream kembali menjadi teks asli.

- **`modul_stego.py`**  
  Berisi logika inti steganografi `embed_hybrid`, termasuk:
  - Deteksi tepi menggunakan algoritma Canny.
  - Pengacakan koordinat penyisipan menggunakan PRNG (Pseudo Random Number Generator) berbasis seed kunci.
  - Klasifikasi area tepi (Edge) dan area halus (Smooth).

### Direktori Data
- **`dataset/`**  
  Folder untuk menyimpan gambar asli (cover image) yang akan digunakan. Gambar harus berformat **.png**. Sub-folder dikategorikan berdasarkan resolusi:
  - `1024 x 1024/`
  - `128 x 128/`
  - `256 x 256/`
  - `512 x 512/`

- **`hasil_stego/`**  
  Folder output sistem. Hasil enkripsi akan otomatis tersimpan di sini sesuai resolusi gambar aslinya.
  - Berisi file gambar steganografi (`..._stego.png`).
  - Berisi file kunci & log koordinat (`..._key.txt`).

### File Lainnya
- **`secretmessage*.txt`** (Contoh: `secretmessage128.txt`)  
  Contoh file pesan rahasia dengan berbagai panjang karakter untuk keperluan pengujian.
Jumlah Karakter pada secret message Untuk Tiap Resolusi
1. 128 x 128 = 1.843
2. 256 x 256 = 7.372
3. 512 x 512 = 29.491
4. 1024 x 1024 = 117.964

---

## Cara Penggunaan

### 1. Persiapan Environment
Pastikan library Python yang dibutuhkan sudah terinstall:
```bash
pip install opencv-python pycryptodome scikit-image numpy
```

### 2. Menyembunyikan Pesan (Enkripsi & Embedding)
1. Siapkan gambar `.png` di dalam folder `dataset/` sesuai resolusinya.
2. Siapkan file pesan `.txt` di root folder (atau gunakan contoh yang ada).
3. Jalankan perintah:
   ```bash
   python enkripsi_embedding.py
   ```
4. Ikuti instruksi di layar:
   - Pilih resolusi gambar.
   - Masukkan nama file gambar (tanpa ekstensi).
   - Masukkan nama file pesan (tanpa ekstensi).

### 3. Menampilkan Pesan (Ekstraksi & Dekripsi)
1. Pastikan file hasil stego dan file key ada di folder `hasil_stego/`.
2. Jalankan perintah:
   ```bash
   python ekstraksi_dekripsi.py
   ```
3. Ikuti instruksi di layar:
   - Pilih resolusi gambar.
   - Masukkan nama file (nama awal file sebelum ditambahkan akhiran `_stego`).

### 4. Menguji Kualitas Citra
1. Jalankan perintah:
   ```bash
   python evaluasi_visual.py
   ```
2. Pilih resolusi dan masukkan nama file gambar untuk melihat perbandingan nilai MSE, PSNR, dan SSIM antara gambar asli dan stego.