# Impor Excel data awal

## Lingkup

Data awal sekarang menyediakan **Impor Excel** setelah tanggal batas disimpan.
Alur: pilih `.xlsx`, baca pratinjau, perbaiki kesalahan bila ada, centang konfirmasi,
lalu simpan kamar/penghuni baru dan draft. Rekonsiliasi/finalisasi tetap terpisah.
Fitur ini tidak menambahkan CSV atau impor saat mode ACTIVE.

Semua kamar impor bertipe Standar, kapasitas dua orang, harga referensi 700000.
Harga kontrak dihitung server dari jumlah penghuni dan durasi paket:
1 orang: 700000/3500000/7000000; 2 orang: 1000000/5500000/10000000 untuk 1/6/12 bulan.
Kolom formula harga/dibayar dan tabel harga Excel tidak dipercaya. Harga manual
di fitur lain tidak diubah oleh pekerjaan ini.

## Koreksi template

Backend yang sudah ada mewajibkan invoice periode berjalan pada cutover,
termasuk yang lunas. Instruksi template pertama yang menyatakan semua periode
lunas boleh dilewati adalah keliru. Importer tidak mengisi asumsi lunas otomatis.

Gunakan `docs/templates/KAMARTHA-template-data-lama-v2.xlsx` dan contoh
`KAMARTHA-contoh-dummy-5-kamar-v2.xlsx`. Keduanya mempertahankan struktur sheet;
contoh v2 menambahkan dua invoice berjalan yang lunas sehingga lima kontrak
memiliki invoice berjalan. Sisa seluruh contoh tetap 1700000. Berkas lama tidak
ditimpa atau dihapus, agar isian pengguna tidak hilang. Tanggal contoh 2026-11-12
hanya untuk simulasi, bukan tanggal batas yang otomatis disimpan oleh importer.

## API dan keputusan

- `POST /api/v1/initialization/import/preview`: multipart file, require_manager,
  origin dan CSRF yang sama dengan operasi bisnis. Tidak menyimpan berkas atau
  data bisnis. Mengembalikan tabel input, hash snapshot, daftar baru/sudah ada,
  rincian kontrak, saldo, dan kesalahan sheet/baris. Aktivitas sesi auth tetap
  diperbarui sesuai mekanisme aplikasi yang sudah ada.
- `POST /api/v1/initialization/import/confirm`: tabel input, preview_hash,
  confirmed=true. Melakukan validasi dan rekonsiliasi yang sama di dalam lock
  singleton bisnis, lalu menolak snapshot yang berubah. Semua insert berada
  dalam satu transaksi: kegagalan apa pun me-rollback seluruh perubahan.
- Identitas batch berbasis hash konten tabel dan cutover, bukan nama berkas atau
  request key acak. Hasil sukses disimpan memakai mekanisme idempotency existing.
  Replay respons sukses tidak membuat insert kedua. Kode kontrak juga menghasilkan
  client_record_key stabil, sehingga saat receipt dihapus tidak otomatis membuat
  kontrak kedua. Data berbeda dengan kode yang sama ditolak, bukan ditimpa.
- Kamar dicocokkan berdasarkan nomor lower-case. Penghuni dicocokkan berdasarkan
  jenis+nomor identitas case-insensitive; hanya satu kecocokan dengan seluruh
  isian sama yang digunakan. Konflik identitas/nama/metadata dan kecocokan ambigu
  perlu diselesaikan manual. Tidak ada pencocokan berdasarkan nama saja.
- Pratinjau memasukkan draft existing ke pemeriksaan konflik. Draft existing
  yang belum valid dapat memblokir impor; perbaiki draft tersebut lebih dahulu.
- Tidak ada migrasi, dependensi baru, Supabase Auth atau Data API.

## Batas berkas dan keamanan

- Maksimal file 2 MB, 100 anggota ZIP, 12 MB total uncompressed, 200 baris per
  sheet. Tidak mengekstrak ZIP ke disk, tidak mengevaluasi formula, tidak
  mengikuti link eksternal. Macro, duplicate ZIP entries, DTD/entity XML dan
  referensi worksheet di luar folder yang didukung ditolak.
- Reader sengaja terbatas pada header dan input template; teks/shared strings
  dan angka didukung. Tanggal input harus teks YYYY-MM-DD, bukan serial Excel.
  Nomor identitas/WhatsApp harus berformat teks untuk menjaga nol awal.
- Client memeriksa ukuran yang tersedia dan membaca stream secara terbatas.
  Server tetap menerapkan batas ukuran dan validasi independen.
- Workbook mengandung data pribadi setelah diisi. Jangan unggah workbook berisi
  data nyata ke repositori atau chat. Server tidak menyimpan workbook mentah;
  data menjadi master/draft hanya setelah konfirmasi. Tidak ada input dummy ke
  Supabase utama pada pengujian ini.
- Importer menolak rentang satu kontrak di atas 100 tahun untuk membatasi kerja
  kalender sebelum rekonsiliasi. Ini batas impor, bukan perubahan kontrak existing.

## Bukti verifikasi

- Full backend suite pada cluster PostgreSQL loopback sekali pakai:
  **199 tests passed, 38 subtests passed**. Tidak memakai SQLite atau Supabase utama.
- Targeted importer: **26 tests passed**, coverage statements+branches **86%**
  pada modul import_excel. Mencakup preview tanpa business write, insert/replay,
  missing paid current period, nominal salah, duplikat, bentrok kamar/orang,
  snapshot kedaluwarsa, rollback paksa, mismatch existing, auth/CSRF, ACTIVE gate,
  dan projection contoh v2 lima kamar/delapan penghuni.
- Flutter: **174 tests passed**, analyzer clean. Tiga tes baru mencakup blokir
  kesalahan per baris, konfirmasi eksplisit, retry payload/key, serta teks 200%
  pada 320x568 dan landscape 800x360.
- Release build sukses. `ops/browser_opening_import_smoke.py`: file terlalu besar
  ditolak tanpa request, file chooser nyata mengunggah contoh v2, pratinjau tampil,
  tombol konfirmasi terkunci sampai checkbox dipilih, lalu kembali ke Data awal.
  Lolos 320x568, 390x844, 800x360 tanpa page errors. Semua API dicegat sintetis.
- Existing five-viewport browser smoke akhirnya lolos. Dua percobaan awal gagal
  pada penemuan textbox login; diagnostik terpisah berhasil. Ini flake bootstrap
  yang sudah diketahui, bukan bukti akar masalah sudah diperbaiki. Runner kini
  mencetak viewport aktif agar kegagalan berikutnya dapat dilokalisasi.
- `scratch/opening-import-2026-11-12/preview-320.png` diperiksa secara visual:
  header, petunjuk, picker, nama berkas membungkus, dan ringkasan muat tanpa
  horizontal overflow. Ini bukan audit VoiceOver/TalkBack perangkat nyata.

Backend lokal direstart untuk mendaftarkan endpoint baru; metadata OpenAPI
diverifikasi. Tidak dilakukan impor atau pembersihan data pada Supabase utama.
Catatan lama pengguna tidak dihapus atau diubah.

## Batas pembuktian dan gate

PASS terbatas: parsing dan aturan bisnis pada PostgreSQL nyata terisolasi;
browser file chooser/review dengan API sintetis; layout 200% pada widget tests.
Belum ada satu tes browser yang terhubung ke backend PostgreSQL terisolasi untuk
seluruh alur impor, atau uji Android nyata. Excel desktop belum diuji langsung.
Global contrast tetap tidak memenuhi AA sesuai keputusan mempertahankan warna.
Jangan menyebut seluruh gate aksesibilitas/produksi telah lolos.

## Evaluasi mandiri

| Aspek | Skor | Bukti dan perbaikan berikutnya |
| --- | --- | --- |
| Akurasi | 4/5 | Tes PostgreSQL dan parser lulus; workbook belum dibuka di Excel desktop. |
| Kelengkapan | 4/5 | Upload, review, konflik, transaksi dan replay tercakup; browser/backend belum diuji bersama. |
| Kejelasan | 4/5 | Error menunjuk sheet/baris; serial tanggal Excel sengaja tidak didukung dan perlu petunjuk. |
| Dapat digunakan | 4/5 | Tombol ada setelah cutover dan backend lokal direstart; data awal invalid perlu diperbaiki dulu. |
| Ringkas | 4/5 | Memakai transaksi/rekonsiliasi/idempotency existing tanpa dependensi; reader XLSX terbatas masih perlu perawatan. |

Rata-rata 4.0/5. Prioritas: tes browser+backend terisolasi, uji Excel desktop,
lalu Android/TalkBack. Penilaian ini bukan sertifikasi; pengguna masih bisa
menemukan perbedaan perilaku picker pada perangkatnya.
