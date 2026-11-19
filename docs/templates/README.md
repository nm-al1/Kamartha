# Template data lama KAMARTHA

Berkas terbaru: `KAMARTHA-template-data-lama-v2.xlsx`.
Contoh terbaru: `KAMARTHA-contoh-dummy-5-kamar-v2.xlsx`.

Template ini untuk mengumpulkan data sebelum impor melalui Data awal → Impor
Excel. Membuka atau mengisi berkas tidak mengubah database. Periksa pratinjau dan
konfirmasi untuk menyimpan draft; finalisasi tetap terpisah.

## Cara mengisi

1. Simpan salinan berkas dengan nama lain sebelum mengisi data pribadi.
2. Baca sheet **Petunjuk** dan tentukan satu tanggal mulai pencatatan (cutover).
3. Isi **Kamar**, **Penghuni**, **Kontrak**, **Penempatan**, lalu
   **Sisa tagihan awal**. Tersedia 200 baris per sheet isian.
4. Gunakan kode penghuni dan kode kontrak unik untuk menghubungkan sheet.
   Semua kamar bertipe Standar dan maksimal dua orang. Harga ditentukan paket
   yang dipilih pada kontrak, bukan kapasitas maksimal kamar.
5. Pilih jumlah penghuni paket dan durasi melalui dropdown. Harga total paket
   otomatis memakai enam harga yang telah disepakati. Jangan ubah kolom otomatis.
6. Isi tanggal sebagai teks `YYYY-MM-DD`. Tanggal akhir kontrak adalah batas akhir
   eksklusif, sesuai model backend. Nomor identitas dan WhatsApp memakai format
   teks agar nol awal tidak hilang.
7. Untuk tunggakan, isi nilai asli tagihan dan sisa belum dibayar pada cutover.
   Kolom sudah dibayar menghitung selisihnya. **Periode berjalan pada cutover wajib
   dicatat meskipun lunas (sisa 0)**. Periode lama lain yang lunas boleh dilewati.
   Jangan menganggap seluruh harga kontrak selalu merupakan tunggakan.

Contoh hubungan kode, bukan data untuk diimpor: penghuni `P001` ditempatkan pada
kontrak `K001`, dan `K001` merujuk nomor kamar yang sudah terdaftar di sheet Kamar.
Tidak ada identitas orang atau data bisnis contoh di baris isian workbook.

## Harga total per paket

| Penghuni | 1 bulan | 6 bulan | 12 bulan |
| --- | ---: | ---: | ---: |
| 1 | 700000 | 3500000 | 7000000 |
| 2 | 1000000 | 5500000 | 10000000 |

## Batas dan keamanan

- Excel menghitung formula saat berkas dibuka. Cache hasil formula belum diisi.
- Dropdown bukan validasi impor: duplikat, relasi kode, tanggal tidak sah,
  tumpang-tindih kamar, penanggung jawab dan saldo tetap perlu diperiksa importer.
- Versi awal template/contoh keliru menyatakan seluruh periode lunas boleh
  dilewati. Gunakan berkas `-v2.xlsx` atau tambahkan periode berjalan yang lunas
  pada berkas lama sebelum impor. Importer menolak data yang belum lengkap.
- Kolom nomor identitas yang belum diketahui boleh dikosongkan saat pengumpulan,
  tetapi harus diselesaikan sebelum membuat penghuni melalui API yang ada.
- Nama saja tidak cukup untuk pencocokan otomatis. Kasus ambigu harus ditinjau.
- Nilai tagihan dan sudah dibayar tersedia agar dapat dipetakan ke
  `OpeningInvoice.amount` dan `OpeningInvoice.opening_paid`.
- Template tidak mengubah enam paket atau data kamar dalam database aplikasi.
- Berkas berisi identitas setelah diisi: simpan privat, jangan commit atau unggah
  ke repositori. Hanya template kosong yang boleh disimpan di proyek.
- Struktur ZIP/XML, harga, dan jumlah formula diperiksa otomatis. Workbook belum
  diuji secara visual atau dihitung ulang melalui Microsoft Excel asli.

Generator: `ops/create_opening_template.py` (standard library Python). Generator
menolak menimpa berkas yang sudah ada agar data yang diisi tidak terhapus.
