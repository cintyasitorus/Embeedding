# Evaluasi Ekstraksi pada Dua Eksperimen

Dokumen ini merangkum skema evaluasi ekstraksi pada dua eksperimen:

1. Hybrid: AES + LSB + EBE
2. LSB: AES + LSB

Fokus evaluasi pada kedua eksperimen adalah membandingkan:

- Normal Extraction (Legitimate User)
- Blind Extraction (Attacker)

serta mengukur Bit Error Rate (BER) dan dampaknya pada proses dekripsi.

---

## 1. Tujuan Evaluasi Ekstraksi

Evaluasi ekstraksi dilakukan untuk membuktikan dua hal:

1. Pada jalur legitimate, bitstream ciphertext dapat dipulihkan sesuai urutan yang benar dan dekripsi berhasil.
2. Pada jalur blind, bitstream yang diekstrak tanpa susunan koordinat menjadi tidak selaras, BER tinggi, dan dekripsi cenderung gagal atau menghasilkan keluaran tidak bermakna.

---

## 2. Definisi BER yang Dipakai

BER dihitung sebagai:

BER = jumlah bit salah / jumlah bit yang dibandingkan

Dalam implementasi laporan, BER juga ditampilkan dalam persen:

BER(%) = BER x 100%

Catatan:

- Pada mode Normal, BER dihitung terhadap bitstream legitimate itu sendiri, sehingga baseline seharusnya 0%.
- Pada mode Blind, BER dihitung antara bitstream legitimate dan bitstream blind.

---

## 3. Eksperimen Hybrid (AES + LSB + EBE)

### 3.1 Alur Normal Extraction

1. Baca stego image dan file key/log.
2. Ambil bit ciphertext berdasarkan koordinat embedding.
3. Susun bitstream ciphertext.
4. Dekripsi dengan AES key yang valid.
5. Simpan plaintext hasil ekstraksi.
6. Simpan laporan BER normal (baseline).

### 3.2 Alur Blind Extraction

1. Baca stego image dan file key/log.
2. Ekstrak bit secara sekuensial tanpa memakai koordinat.
3. Bentuk bitstream blind.
4. Hitung BER terhadap bitstream legitimate.
5. Coba dekripsi bitstream blind dengan AES key asli.
6. Simpan laporan BER blind dan status dekripsi blind.

### 3.3 File keluaran (Hybrid)

Mode Normal:

- hasil_ekstraksi_namaBase.txt
- laporan_ber_normal_namaBase.txt

Mode Blind:

- laporan_ber_blind_namaBase.txt
- hasil_dekripsi_blind_namaBase.txt (hanya jika dekripsi blind berhasil secara teknis)

### 3.4 Catatan isi laporan

Laporan normal dan blind berisi:

- nilai BER
- ringkasan ciphertext legitimate
- ringkasan ciphertext blind (khusus mode blind)
- ciphertext hex utuh
- bitstream utuh
- status uji dekripsi blind

---

## 4. Eksperimen LSB (AES + LSB)

### 4.1 Alur Normal Extraction

1. Baca key file dan coords file.
2. Ekstrak bit ciphertext berdasarkan koordinat channel R/G/B.
3. Rekonstruksi payload bytes.
4. Dekripsi dengan AES key valid.
5. Simpan plaintext hasil ekstraksi.
6. Hitung dan simpan laporan BER normal.

### 4.2 Alur Blind Extraction

1. Baca key file dan coords file.
2. Ekstrak bit secara sekuensial pada seluruh piksel (tanpa koordinat).
3. Bentuk bitstream blind.
4. Hitung BER terhadap hasil legitimate.
5. Coba dekripsi blind dengan AES key asli.
6. Simpan laporan BER blind dan status dekripsi blind.

### 4.3 File keluaran (LSB)

Mode Normal:

- hasil_ekstraksi_namaBase.txt
- laporan_ber_normal_namaBase.txt

Mode Blind:

- laporan_ber_blind_namaBase.txt
- hasil_dekripsi_blind_namaBase.txt (hanya jika dekripsi blind berhasil secara teknis)

---

## 5. Interpretasi Hasil yang Diharapkan

### 5.1 Normal Extraction

- BER mendekati 0% (ideal: 0%).
- Dekripsi berhasil.
- Plaintext hasil ekstraksi sama dengan pesan asli.

### 5.2 Blind Extraction

- BER tinggi (sering mendekati 50%).
- Dekripsi sering gagal pada unpadding atau format payload.
- Jika dekripsi lolos secara teknis, isi output biasanya tidak bermakna.

---

## 6. Kesimpulan Umum

Dua eksperimen menunjukkan pola yang konsisten:

1. Koordinat ekstraksi berperan penting untuk menjaga urutan bit ciphertext.
2. Ekstraksi blind menghasilkan ketidaksesuaian bit tinggi yang tercermin pada BER.
3. BER menjadi metrik kuantitatif utama untuk menunjukkan kegagalan attacker dalam memulihkan informasi bermakna.
4. Uji dekripsi blind dengan key asli memperkuat bukti bahwa kehilangan urutan bit membuat data tidak dapat dipulihkan dengan benar.

---

## 7. Rekomendasi Pelaporan Akhir

Untuk tabel hasil skripsi atau laporan, disarankan menyajikan kolom berikut:

- Eksperimen (Hybrid atau LSB)
- Resolusi
- Nama sampel
- TOTAL_BITS
- BER normal (%)
- BER blind (%)
- Status dekripsi blind
- Catatan kualitas output blind

Dengan format ini, pembandingan antar eksperimen menjadi jelas secara kuantitatif dan kualitatif.
