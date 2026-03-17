# Sistem Pengamanan Data Citra Baseline (AES-CBC + LSB Steganography)

Proyek ini adalah implementasi baseline sistem keamanan data citra yang menggabungkan kriptografi AES-128 Mode CBC dengan teknik steganografi LSB klasik (Least Significant Bit). Sistem mengenkripsi pesan teks lalu menyisipkannya ke dalam citra digital PNG menggunakan bit paling rendah pada kanal warna, serta menyediakan evaluasi kualitas visual untuk dibandingkan dengan metode Hybrid.

## Struktur Folder

Berikut adalah penjelasan fungsi dari setiap file dan folder dalam eksperimen baseline LSB.

### Program Utama
Script yang dijalankan langsung oleh pengguna untuk proses embedding, ekstraksi, dan evaluasi.

- `lsb.py`  
  Program utama baseline LSB.  
  *Fungsi:*  
  - Mode `e`: Membaca cover image dan file pesan, melakukan enkripsi AES, lalu menyisipkan data terenkripsi ke citra dengan metode LSB.  
  - Mode `x`: Membaca stego image dan key file, mengekstrak bit pesan, lalu melakukan dekripsi.  
  - Mode `t`: Menjalankan evaluasi kualitas visual dari `evaluasi_visual.py`.  
  *Output:*  
  - File stego image dengan akhiran `_stego.png`.  
  - File key dengan akhiran `_key.txt`.  
  - File hasil ekstraksi dengan akhiran `hasil_ekstraksi_namafile.txt`.

- `evaluasi_visual.py`  
  Program untuk pengujian kualitas citra.  
  *Fungsi:* Membandingkan gambar asli dari folder `dataset` dengan gambar stego dari folder `hasil_stego`.  
  *Metrik:* Menghitung MSE, PSNR, dan SSIM.

### Modul Pendukung
File pendukung yang diimpor oleh program utama.

- `crypt.py`  
  Berisi implementasi kelas `AESCipher` untuk:  
  - Enkripsi pesan dengan AES-128 CBC.  
  - Dekripsi ciphertext kembali menjadi data asli.  
  - Pembuatan key enkripsi acak.

### Direktori Data
- `dataset`  
  Folder untuk menyimpan gambar asli (cover image) yang akan digunakan.  
  Sub-folder berdasarkan resolusi:  
  - `128 x 128`  
  - `256 x 256`  
  - `512 x 512`  
  - `1024 x 1024`

- `hasil_stego`  
  Folder output baseline LSB, terstruktur sesuai resolusi gambar.  
  - Menyimpan stego image: `nama_stego.png`  
  - Menyimpan key file: `nama_key.txt`  
  - Menyimpan hasil ekstraksi: `hasil_ekstraksi_nama.txt`

### File Lainnya
- `pesanlsb.txt`  
  Contoh file pesan rahasia untuk kebutuhan pengujian baseline LSB.

---

## Cara Penggunaan

### 1. Persiapan Environment
Pastikan library Python yang dibutuhkan sudah terpasang:

```bash
pip install pillow pycryptodome opencv-python scikit-image numpy
```

### 2. Menyembunyikan Pesan (Encrypt and Embed)
1. Siapkan gambar PNG di folder `dataset` sesuai resolusinya.
2. Siapkan file pesan TXT di folder `LSB` (contoh: `pesanlsb.txt`).
3. Jalankan:

```bash
python lsb.py
```

4. Pilih mode `e`.
5. Ikuti instruksi:
- Pilih resolusi.
- Masukkan nama file gambar tanpa ekstensi.
- Masukkan nama file pesan tanpa ekstensi.

### 3. Mengambil Pesan (Extract and Decrypt)
1. Pastikan stego image dan key file sudah ada di folder `hasil_stego` sesuai resolusi.
2. Jalankan:

```bash
python lsb.py
```

3. Pilih mode `x`.
4. Ikuti instruksi:
- Pilih resolusi.
- Masukkan nama dasar file tanpa akhiran `_stego` atau `_key`.

### 4. Menguji Kualitas Visual
1. Jalankan:

```bash
python lsb.py
```

2. Pilih mode `t`.
3. Program akan menjalankan `evaluasi_visual.py` untuk membandingkan:
- Cover image dari `dataset`
- Stego image dari `hasil_stego`

4. Hasil evaluasi menampilkan:
- MSE
- PSNR
- SSIM

---

## Catatan Penting

- Gunakan format PNG untuk cover image agar kualitas tetap konsisten.
- Struktur path pada baseline ini bersifat lokal terhadap folder `LSB`.
- Untuk perbandingan eksperimen yang adil dengan hybrid, gunakan gambar cover dan pesan yang sama pada kedua metode.
- Jika ingin mencegah file cache Python, jalankan dengan:

```bash
python -B lsb.py
```

---

## Ringkasan Alur Baseline LSB

1. Pesan dibaca dari file teks.
2. Pesan dienkripsi menggunakan AES-128 CBC.
3. Data terenkripsi diubah menjadi bitstream.
4. Bitstream disisipkan ke LSB kanal RGB pada citra.
5. Stego image dan key disimpan.
6. Saat ekstraksi, bit diambil kembali dari stego image.
7. Bitstream didekripsi untuk mendapatkan pesan asli.
8. Kualitas visual dievaluasi menggunakan MSE, PSNR, dan SSIM.
