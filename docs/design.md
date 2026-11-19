# Desain Antarmuka Kamartha

| Metadata | Nilai |
| --- | --- |
| Versi | 1.0 |
| Tanggal | 31 Oktober 2026, WITA |
| Acuan | PRD.md 1.0, architecture.md 1.0, database.md 1.0 dan uml.md 1.0 |
| Target | Flutter Web responsif, penggunaan utama browser HP |
| Arah visual | Adaptasi karakter Accomodio pilihan pengguna: oranye, putih, navy, kelompok informasi dan navigasi bawah |
| Status | Spesifikasi UI untuk implementasi; bukan file Figma editable atau bukti UAT |

Simpan file ini sebagai `docs/design.md`. Agent AI membaca aturan produk pada PRD, mekanisme server pada architecture dan relasi pada database/uml sebelum mengimplementasikan layar. Jika mockup bertentangan dengan aturan tertulis, jangan menyalin kesalahannya; gunakan keputusan konsisten di dokumen dan laporkan konflik yang belum terpecahkan.

## 1. Arah desain dan batas

Tampilan yang dipilih menggunakan satu keluarga aksen oranye, latar terang, teks navy dan kelompok informasi yang jelas. Beranda berfokus ke tindak lanjut tagihan/akhir sewa. Jangan mengubahnya menjadi aplikasi booking wisata, landing page promosi atau dashboard berisi grafik dekoratif.

Referensi visual yang diterima dalam diskusi: board beranda/detail/tinjau pembayaran, board kamar/tagihan/pengeluaran, halaman Menu serta login/registrasi awal. Semua gambar adalah mockup raster; nama, nominal, versi dan angka statistik di dalamnya adalah contoh. Gambar belum menjadi Figma atau prototipe yang dapat diklik. Logo rumah sementara bukan identitas final yang wajib disalin persis.

Koreksi sebelum implementasi:

- Ringkasan kamar menghitung Dihuni, Kosong dan Perlu konfirmasi secara terpisah; tidak menganggap kamar Perlu konfirmasi sebagai Kosong. Total harus konsisten dengan data, termasuk jika ada kontrak terjadwal.
- Tagihan contoh yang tampil tidak selalu seluruh piutang. Ringkasan harus memberi label ruang lingkup, jumlah hasil dan pagination; jangan menampilkan total yang terlihat tidak dapat dijelaskan.
- Konfirmasi “uang diterima” pada layar tinjau tidak dicentang otomatis.
- Teks oranye terang pada putih dalam mockup diganti warna foreground lebih gelap bila diperlukan agar terbaca; warna brand tidak wajib dipakai mentah untuk seluruh teks.
- Login tidak menyediakan signup publik, remember-me, email/social login atau PIN. Kode penyiapan tetap dipakai untuk registrasi akun pertama sesuai keputusan pengguna.

## 2. Token visual calon implementasi

| Token | Nilai rancangan | Pemakaian |
| --- | --- | --- |
| brand | #F45A24 | Identitas dan aksen yang tidak bergantung teks kecil |
| primary_action | #B9380B | Tombol berteks putih; warna lebih gelap daripada aksen dekoratif |
| link | #A8320A | Tautan teks di latar putih |
| ink | #142039 | Judul, nominal dan isi utama |
| secondary_text | #526079 | Penjelasan dan metadata |
| background | #F5F7FA | Latar halaman |
| surface | #FFFFFF | Formulir dan kelompok daftar |
| border | #DCE3EB | Pemisah dan batas input |
| success | #167347 | Label Lunas/Dihuni beserta teks |
| warning | #8A5700 | Mendekati tempo/Perlu konfirmasi |
| danger | #B42318 | Menunggak, error dan pembatalan |
| Font | Inter, regular 400 dan semibold 600 | Sertakan aset font berlisensi sesuai distribusi; fallback sans-serif |
| Ukuran | Isi/input 16, metadata 14, judul 24, nomor kamar utama 30 logical px | Jangan mengecilkan teks untuk memaksakan semua isi masuk satu layar |
| Spasi | 4, 8, 12, 16, 24, 32 logical px | Padding layar HP 16–20, sela bagian 24 |
| Bentuk | Input radius 12, kelompok daftar 16, tombol utama 24 | Konsisten; chip filter boleh pill |
| Sentuhan | Target minimal rancangan 48 × 48 logical px | Ikon, pilihan metode, baris daftar dan tombol |

Header oranye boleh memakai variasi tonal tipis dalam keluarga oranye yang sama; tidak wajib ada gradasi di setiap tombol. Gunakan tombol solid untuk implementasi awal. Bayangan hanya tipis pada panel pencarian beranda/navigasi jika perlu; jangan beri glow atau shadow berat pada setiap elemen. Ikon outline satu keluarga, dengan label teks. Warna status selalu didampingi kata, bukan hanya titik/warna.

Nilai token adalah spesifikasi awal, bukan klaim aksesibilitas telah diuji. Implementasi memeriksa kontras, ukuran teks browser, fokus keyboard dan penggunaan pada HP mitra sebelum UAT.

## 3. Navigasi dan responsif

### 3.1 Empat tujuan utama

| Tujuan | Isi |
| --- | --- |
| Beranda | Pencarian singkat, ringkasan hunian dan tindak lanjut tagihan/akhir sewa |
| Kamar | Daftar, pencarian/filter dan detail kamar |
| Tagihan | Daftar tagihan, detail, cicilan dan penerimaan uang |
| Menu | Penghuni, Masa sewa, Pengeluaran, Laporan kas, Ganti password dan Keluar |

Bottom navigation hadir pada layar daftar utama. Detail dan wizard yang memakai sticky action bar boleh menyembunyikan bottom nav agar tidak bertabrakan; back mengembalikan filter/posisi daftar sebelumnya. Halaman login/setup/data awal tidak memakai bottom nav operasional. Navigasi UI bukan pengganti pemeriksaan sesi/mode di API.

Pada lebar <600 logical px gunakan satu kolom dan bottom nav. Pada 600–1023 gunakan lebar isi maksimal sekitar 760 dan navigation rail. Pada >=1024 gunakan rail/sidebar dan area isi maksimal sekitar 1200; detail bisa dua kolom dengan bagian utama dan ringkasan. Ini pilihan layout Flutter, bukan aplikasi React terpisah. Form panjang tetap terbaca satu kolom maksimal sekitar 640; jangan meregangkan input sepanjang monitor.

Pastikan safe area dan padding bawah sebesar tinggi nav/action bar sehingga baris terakhir tidak tertutup. Keyboard tidak menutupi input/tombol; halaman dapat digulir. Filter chip bisa digulir horizontal dengan petunjuk ada pilihan berikutnya. Uji minimal lebar 360/390/430 dan desktop 1280, termasuk zoom/teks diperbesar; ukuran ini rencana pengujian, bukan hasil aktual.

### 3.2 Route dan akses

| ID layar | Route calon Flutter | Akses |
| --- | --- | --- |
| AUTH-01 | /login | Instalasi sudah punya akun, belum login |
| AUTH-02 | /setup | Hanya akun pertama belum ada; wajib kode setup |
| AUTH-03 | /change-password | Sesi sah dan password lama |
| INIT-01 | /initialization | Sesi sah, mode Persiapan |
| HOME-01 | /home | Sesi sah, mode Aktif |
| ROOM-01/02 | /rooms dan /rooms/:id | Daftar/detail kamar |
| RES-01/02 | /residents dan /residents/:id | Daftar/detail orang |
| LEASE-01/02 | /leases dan /leases/:id | Kontrak dan tindakan Penghunian |
| INV-01/02 | /invoices dan /invoices/:id | Tagihan per periode |
| PAY-01/02/03 | /payments/new, /payments/review, /payments/:id | Form, tinjau lokal, detail hasil tersimpan |
| EXP-01/02 | /expenses dan /expenses/:id | Daftar/detail/form biaya |
| REPORT-01 | /reports/cash | Rekap kas |
| MENU-01 | /menu | Menu tambahan |
| WA-01 | Panel/halaman pratinjau dari konteks | Kontak/context valid; tidak memerlukan route publik |

Route adalah rancangan frontend, bukan endpoint FastAPI. Halaman tinjau pembayaran memakai state wizard; membuka route tinjau tanpa data mengembalikan ke formulir, bukan menebak nilai. Deep link ke objek yang tidak tersedia menghasilkan halaman tidak ditemukan yang aman.

## 4. Login, registrasi dan penyiapan

### AUTH-01 Login

Header brand oranye, form putih. Field username/password dengan label permanen, toggle tampil/sembunyikan password, tombol Masuk. Pesan kredensial salah bersifat generik. Proses menonaktifkan pengiriman ulang selama menunggu; rate limit menampilkan waktu tunggu dari API. Jangan mempertahankan password pada log, localStorage atau draft.

Tautan Lupa password membuka petunjuk pemulihan melalui tim/pemeliharaan setelah verifikasi pemilik, bukan janji email/OTP otomatis. Jangan mengarang nomor kontak tim jika belum diberikan. Instalasi dengan akun tidak menampilkan tautan daftar. Sesudah login, server menentukan masuk ke Persiapan atau Beranda; jangan selalu menganggap mode Aktif.

### AUTH-02 Registrasi awal

Isi: kode penyiapan, username, password dan konfirmasi. Helper username 4–32 huruf/angka/titik/garis bawah; password minimal 8 dan maksimal 128 karakter sesuai revisi pengguna, mendukung frasa sandi. Kode diperoleh privat dari tim, tidak ditanam di Flutter. Tombol Buat akun, review error per isian. Setelah sukses tampilkan “Akun pengelola berhasil dibuat. Silakan masuk.” lalu arahkan login; jangan membuat asumsi API sekaligus mengautentikasi jika kontraknya belum menetapkan demikian.

Server menutup setup setelah akun pertama ada, termasuk ketika dua permintaan bersamaan. Jika akun sudah dibuat, tampilkan akses login tanpa mengekspos detail kode atau identitas akun. Pembatalan/kembali meninggalkan setup tidak boleh membuat akun sebagian.

### INIT-01 Data awal

Alur halaman: (1) tanggal mulai pencatatan, (2) formulir berkas, (3) rekap, (4) tinjau/finalisasi. Form berkas berisi pilihan kamar/penghuni yang bisa dipakai kembali, nama satu/dua orang, paket, harga, tanggal kontrak, keadaan Penghunian dan baris tagihan per periode.

Setiap tagihan menampilkan periode, jatuh tempo, nominal asli, “Dibayar sebelum pencatatan” dan sisa otomatis. Ini bukan daftar transaksi kas lama. Sertakan periode berjalan walau lunas serta semua tunggakan lama yang relevan. Data belum lengkap dapat disimpan sebagai Draft; tampilkan daftar kekurangan, jangan isi identitas/tanggal rekaan.

Rekap memperlihatkan kamar/orang, berkas belum lengkap, jumlah tagihan dan total piutang. Finalisasi hanya tersedia setelah validasi ulang berhasil, konfirmasi kecocokan buku mitra, lalu ringkasan dampak: saldo awal/cutover terkunci dan transaksi operasional dibuka. Tindakan akhir memakai idempotency key. Setelah sukses tidak ada tombol reset atau ubah saldo awal di Menu; data asal tetap dapat ditelusuri melalui riwayat yang relevan.

## 5. Beranda dan daftar utama

### HOME-01 Beranda

Header ringkas: nama Kamartha, salam sederhana dan tanggal server. Panel pencarian kamar/penghuni; ringkasan hunian memberi label jumlah kamar Dihuni, Kosong, Perlu konfirmasi serta jumlah orang yang masih tinggal. Contoh konsisten untuk 10 kamar: 7 Dihuni, 2 Kosong, 1 Perlu konfirmasi; penghuni dihitung dari orang sebenarnya, bukan kamar dikali paket.

Bagian utama “Perlu ditindaklanjuti” mempunyai tab Tagihan dan Akhir sewa. Baris tagihan memuat nomor kamar, nama/kontak, sisa, periode dan jatuh tempo. Urutkan menunggak dari jatuh tempo tertua, lalu yang mendekati tempo; periode dan ID menjadi tie-breaker stabil. Baris akhir sewa memuat batas akhir dan status tindak lanjut fisik. Kamar dengan kontrak habis tetapi masih dihuni tetap tampil perlu konfirmasi.

Bagian Pencatatan cepat hanya Pembayaran dan Pengeluaran. Tidak ada grafik promosi, foto resort atau empat tile statistik berwarna. Sebelum GET ringkasan, jalankan billing/synchronize; jika gagal tampilkan “Data tagihan belum diperbarui” dan Coba lagi, jangan mengklaim data sudah mutakhir.

### ROOM-01 Daftar kamar

Pencarian nomor/nama, filter Semua/Dihuni/Kosong/Perlu konfirmasi. Row: nomor kamar, nama terkini, jenis paket singkat, status dan chevron. Kamar tanpa penghuni menampilkan “Belum ada penghuni”. Tombol Buat sewa tetap memvalidasi rentang yang diminta; status Kosong sekarang tidak menjamin bebas dari kontrak terjadwal.

Tambah/edit kamar: nomor, tipe, dukungan 1/2 orang dan harga referensi. Harga positif; penjelasan “Harga kesepakatan ditentukan saat membuat sewa”. Tidak ada hapus permanen kamar bersejarah. Mengubah kapasitas yang merusak kontrak aktif ditolak dengan alasan server.

### INV-01 Daftar tagihan

Pencarian, filter status dan rentang periode. Ringkasan “Sisa tagihan aktif” mencakup piutang belum tempo serta menunggak, diberi label jelas apakah seluruh hasil filter atau seluruh kos. Daftar berpaginasi memberi jumlah hasil; ringkasan tidak hanya menjumlah row halaman pertama.

Kelompok Menunggak/Mendekati jatuh tempo atau daftar berfilter mengikuti pilihan pengguna. Row: kamar, nama, periode, tempo, sisa dan status. Tagihan Batal dapat ditelusuri lewat filter riwayat, bukan masuk piutang. Catat pembayaran membuka pemilih masa sewa/tagihan, bukan gateway bayar online.

## 6. Detail kamar, penghuni dan kontrak

### ROOM-02 Detail kamar

Urutan: nomor/status → Penghuni → Masa sewa → Tagihan per periode → aksi utama. Kelola penghuni adalah pintu ke detail kontrak/tindakan per orang, bukan mengganti nama lama langsung. Ringkasan kontrak membedakan tanggal mulai, batas akhir, paket, harga per periode dan fasilitas termasuk air/listrik/Wi-Fi.

Tagihan periode menampilkan total, dibayar, sisa, tempo dan status. Label batas akhir harus jelas: “Batas akhir kontrak: 1 Desember 2026”; periode sebelumnya memakai [1 Nov,1 Des), bukan janji termasuk seluruh tanggal 1 Des. Tindakan Catat pembayaran dan Siapkan pesan WhatsApp; WA dinonaktifkan dengan alasan jika kontak tidak valid.

### RES-01/02 Penghuni

Daftar pencarian nama/identitas dan filter masih tinggal/riwayat. Detail: identitas, WA, kamar/hubungan terkini, sejarah masuk/keluar dan kontrak terkait. Orang yang telah dilanjutkan tidak dihitung dua kali. Kontak mantan penghuni tetap dapat ditinjau untuk piutang tanpa mengaktifkan hunian palsu. Foto KTP tidak wajib; nomor identitas tidak dimasukkan pesan/tautan WA.

### LEASE-01/02 Masa sewa

Wizard kontrak baru: pilih kamar dan rentang → pilih jenis 1/2 orang serta periode 1/6/12 → pilih satu/dua nama dan kontak penanggung jawab → harga total kamar per periode → tinjau dan simpan. Dua nama harus berbeda; harga dua orang/6/12 bulan tidak dihitung otomatis dari tarif satu orang/bulanan. Tampilkan satu tagihan kamar, bukan tagihan per orang.

| Tindakan | Isian dan tinjauan | Hasil yang diperlihatkan |
| --- | --- | --- |
| Perpanjang | Jumlah periode penuh, harga/paket yang tetap, tanggal akhir baru | Tidak menghidupkan kembali orang yang telah keluar |
| Keluar per orang | Pilih nama, tanggal sebenarnya; penerus kontak jika diperlukan | Riwayat orang berubah, harga/tagihan tetap jika masih ada yang tinggal |
| Ganti penanggung jawab | Pilih penghuni yang masih tinggal dan alasan | Kontak baru dan riwayat; tidak otomatis memindahkan utang |
| Tambah penghuni pengganti | Orang baru, tanggal masuk dan orang yang telah keluar | Maksimal dua bersamaan, tanpa menimpa identitas lama |
| Semua keluar | Tanggal per orang, tagihan saat ini/mendatang dan alasan | Penutupan fisik tidak menghapus utang; pemotongan periode berbayar ditolak |
| Kontrak lanjutan | Paket/harga/tanggal baru yang sah, orang yang dilanjutkan | Hubungan lama ditutup sebagai Dilanjutkan, bukan tanggal keluar fisik rekaan |

Semua tindakan diawali review dampak dan dikonfirmasi sebelum simpan. Jika seluruh penghuni keluar/kontrak berakhir, alur pengganti tidak dapat menghidupkannya kembali. Kesalahan benturan menampilkan kamar/orang/periode relevan tanpa menghapus isian formulir.

## 7. Tagihan dan pembayaran

### INV-02 Detail tagihan

Header kamar, periode dan status; rincian nominal, pembayaran sebelum sistem bila OPENING, penerimaan baru dan sisa. Tampilkan cicilan dengan tanggal uang diterima, metode, nominal bagian untuk tagihan ini dan link induk penerimaan. Riwayat Batal tetap terlihat berlabel; jangan dicampur ke total dibayar Valid.

### PAY-01 Form pembayaran

Bisa dibuka dari tagihan tertentu atau pemilih masa sewa. Isian: tanggal uang diterima, total uang, metode Cash/Transfer/QRIS, daftar alokasi dan bukti/referensi opsional. Pada satu tagihan, alokasi otomatis mengikuti nominal uang yang diisi, tetap terlihat pada ringkasan. Jangan otomatis mengisi/menganggap seluruh sisa sudah diterima; pengguna mengetik jumlah sebenarnya.

“Tambah tagihan lain” hanya memilih invoice Aktif yang memiliki sisa pada masa sewa sama dan tersedia menurut aturan kalender. Setelah beberapa dipilih, setiap row punya nominal alokasi yang dapat diedit serta tombol hapus dari formulir, bukan hapus invoice. Tampilkan Total diterima, Total dialokasikan dan Selisih; lanjut hanya jika selisih nol dan semua bagian valid.

Nominal maksimal sisa, tanpa nol/negatif/pecahan atau lebih bayar. Tanggal tidak masa depan/tidak sebelum cutover; tanggal input otomatis tidak dapat diedit. Upload opsional JPG/PNG/PDF <=2 MB memperlihatkan nama aman, ukuran, progres dan status. Upload gagal memberi Retry atau Lanjut tanpa bukti dengan pilihan eksplisit; tidak membuat uang tersimpan diam-diam.

### PAY-02 Tinjau sebelum simpan

Bagian Kamar dan penghuni, Rincian penerimaan, Alokasi per periode, sisa sebelum/sesudah dan total uang. Tautan Ubah kembali ke form dengan nilai terjaga. Checkbox “Saya sudah memastikan uang diterima” default tidak dicentang. Simpan pembayaran aktif setelah konfirmasi, validasi lokal dan upload yang dipilih selesai. Review hanya perhitungan sementara; server memeriksa ulang saldo terbaru saat commit.

### PAY-03 Hasil dan riwayat pembayaran

Setelah commit sukses: “Pembayaran berhasil dicatat”, tanggal penerimaan, waktu catat server, metode, total dan alokasi; sisa terbaru dari server. Tombol Siapkan pesan WhatsApp bersifat opsional dan tidak menentukan berhasilnya pencatatan. Jangan memberi status Lunas sebelum server menyatakan sisa nol.

Pembatalan membutuhkan alasan, ringkasan seluruh alokasi yang dibatalkan serta konfirmasi; tidak ada edit tanggal/metode/nominal induk atau hapus permanen. Setelah batal, tampilkan status Batal beserta alasan dan perbarui laporan/sisa. Koreksi dibuat sebagai penerimaan baru setelah pembatalan; tidak otomatis menyalin dan menyimpan transaksi kedua tanpa pengguna meninjaunya.

### Retry yang aman

Satu tindakan simpan mempertahankan idempotency key saat respons gagal/terputus. Teks “Hasil penyimpanan belum diketahui. Coba periksa kembali” lebih tepat daripada “Pembayaran gagal” jika commit mungkin sudah terjadi. Retry memakai key yang sama, mengambil ID hasil, lalu membaca saldo terbaru. Data berasal dari layar lama yang tidak lagi valid memerlukan review ulang, bukan pemaksaan nominal lama.

## 8. Pengeluaran, laporan, menu dan pesan

### EXP-01/02 Pengeluaran

Daftar dikelompokkan tanggal dengan filter rentang dan total hasil; row kategori, keterangan dan nominal. Form: tanggal, kategori Listrik/Air/Internet-WiFi/Perbaikan/Gaji/Lainnya, nominal, keterangan dan bukti opsional. Listrik/air/Wi-Fi tidak membuat tagihan tambahan penghuni.

Detail memperlihatkan nilai terkini, bukti, riwayat dan aksi Koreksi/Batalkan. Koreksi wajib alasan, review nilai sebelum/sesudah dan expected version. Konflik layar lama menampilkan pilihan muat ulang dan tinjau perubahan, bukan overwrite. Pembatalan untuk salah catat/duplikat dikecualikan dari laporan, bukan uang kembali. Riwayat lampiran lama tetap dapat dibuka setelah koreksi, dengan autentikasi.

### REPORT-01 Laporan kas

Pemilih tanggal awal/akhir termasuk kedua batas, tombol Tampilkan, lalu Pemasukan, Pengeluaran dan Selisih kas. Jangan menyebut selisih kas sebagai laba akrual. Rincian penerimaan menampilkan induk sekali, expandable untuk melihat alokasi; tanggal uang diterima menjadi acuan. Rincian biaya hanya pengeluaran Valid. Saldo sebelum sistem tidak masuk kas baru.

Periode sebelum cutover atau rentang terbalik ditolak. Rentang kosong menampilkan nol dengan penjelasan “Belum ada transaksi pada rentang ini”. Total dan rincian berasal snapshot server yang sama. Tidak menambahkan tombol ekspor Excel/PDF yang belum masuk scope. Label kecil menjelaskan input terlambat/koreksi dapat memperbarui laporan tanggal sebelumnya.

### MENU-01 Menu

Profil ringkas pengelola, kelompok Operasional (Penghuni, Masa sewa, Pengeluaran), Laporan (Laporan kas), Akun (Ganti password, Keluar). Tidak menduplikasi Kamar/Tagihan yang sudah di nav utama. Ganti password meminta password lama, baru dan konfirmasi; sesudah sukses seluruh sesi dicabut lalu login ulang. Keluar meminta konfirmasi jika ada formulir belum disimpan, mencabut sesi dan kembali login.

Tidak ada pengaturan gateway, template pesan, backup publik, akun penghuni atau reset data awal. Nama/versi mockup tidak membuktikan versi software sudah dirilis; label versi aplikasi aktual diambil dari build.

### WA-01 Pratinjau pesan

Tampilkan penerima, nomor ternormalisasi, konteks kamar/kontrak/tagihan, dan pesan. Konfirmasi pembayaran pertama setiap invoice menyertakan paket/masa sewa; cicilan berikutnya menyertakan nominal dan sisa. Penerimaan beberapa invoice merinci alokasi masing-masing tanpa menggandakan total. Konfirmasi pembayaran Batal tidak dapat dibuka seolah Valid.

Tombol “Buka WhatsApp”; pengguna masih meninjau/edit dan menekan Kirim di WhatsApp. Tidak memberi toast “Pesan terkirim”, tidak membuat log terkirim/dibaca atau saldo berubah. Jika pembukaan gagal tampilkan alasan dan izinkan coba lagi; pembayaran yang sudah disimpan tetap sah. Nomor tidak valid menampilkan petunjuk perbaiki kontak. Kontak penanggung jawab keluar seluruhnya tetap dapat dipakai untuk piutang setelah ditinjau.

## 9. Keadaan UI bersama

| Keadaan | Perilaku |
| --- | --- |
| Loading awal | Skeleton/progres sederhana pada area isi; jangan mengisi angka dummy seperti data nyata |
| Memuat ulang | Pertahankan data sebelumnya dengan indikator sedang diperbarui; jangan klaim mutakhir saat sinkronisasi gagal |
| Daftar kosong | Penjelasan sesuai filter dan tindakan relevan; kosong tagihan berbeda dengan gagal API |
| Error isian | Pesan dekat field, fokus ke kesalahan pertama, masukan lain tidak hilang |
| Error layanan | Pesan singkat, Retry dan request ID bila perlu; tidak menampilkan traceback/SQL |
| Simpan berlangsung | Tombol menampilkan proses; cegah double tap, namun backend tetap idempoten |
| Konflik 409 | Jelaskan data berubah; muat ulang saldo/versi dan minta tinjau ulang |
| Sesi berakhir | Kembali login tanpa menampilkan data privat; draft sensitif tidak disimpan di localStorage |
| Kembali dari form | Konfirmasi buang perubahan; password/kode/token tidak dijadikan draft persisten |
| Pembatalan/finalisasi/keluar | Review dampak dan alasan/konfirmasi yang diperlukan sebelum commit |

Draft navigasi sementara boleh di memori Flutter, tetapi bukan jaminan bertahan saat browser ditutup. Draft data awal yang sah disimpan server melalui endpoint Persiapan. Jangan menambahkan autosave finansial atau antrean offline tanpa perubahan kebutuhan.

## 10. Penyerahan ke Figma dan OpenCode

Susunan frame yang disarankan: 00 Tokens & Components; 01 Auth; 02 Data Awal; 03 Beranda; 04 Kamar & Penghuni; 05 Masa Sewa; 06 Tagihan & Pembayaran; 07 Pengeluaran; 08 Laporan & Menu; 09 States. Nama frame mengikuti ID layar agar dapat dipetakan ke route dan AC.

Komponen minimal: AppBar, BottomNavigation, SearchField, FilterChip, GroupedListRow, StatusLabel, LabelValueRow, MoneyField, DateField, MethodSelector, AllocationRow, AttachmentPicker, ReviewSection, PrimaryButton, ErrorSummary dan ConfirmationDialog. Jangan membuat kartu/ikon khusus untuk setiap fitur bila struktur yang sama dapat digunakan kembali.

Prompt ringkas untuk agent implementasi:

> Baca docs/PRD.md, architecture.md, database.md, uml.md dan design.md. Gunakan visual oranye-putih yang telah dipilih sebagai referensi; jangan menyalin angka dummy atau menambah fitur dari screenshot. Implementasikan Flutter Web responsif dengan komponen bersama. Pertahankan login username/password dan setup kode pertama, pembayaran manual, alokasi satu kontrak, riwayat Penghunian, saldo awal terpisah serta WA manual. Tangani loading/error/empty/retry dan sesi kedaluwarsa. Laporkan konflik dokumen sebelum mengubah aturan bisnis.

Dokumen ini belum membuat atau menyunting frame Figma. Link node Figma yang disetujui dapat ditambahkan ke setiap ID layar setelah frame tersedia. Koneksi MCP pada OpenCode tidak berarti semua mockup raster otomatis menjadi komponen Figma yang editable.

## 11. Verifikasi desain ke kebutuhan

| Fitur PRD | Layar utama | Bukti penerimaan yang harus diuji |
| --- | --- | --- |
| KF-01 | ROOM-01/02 | AC-04/09/12/13; kamar perlu konfirmasi tidak dianggap kosong |
| KF-02 | RES-01/02, LEASE-02 | AC-05/07/10/11/37; dua nama dan riwayat tidak hilang |
| KF-03 | LEASE-01/02, ROOM-02 | AC-06–14/18/37–40; kontak, pengganti dan kontrak lanjutan |
| KF-04 | HOME-01, INV-01/02 | AC-15–18/43; sinkronisasi H−3 dan kalender |
| KF-05 | PAY-01/02/03, INV-02 | AC-19–24/36/41–47; saldo, alokasi dan pembatalan |
| KF-06 | EXP-01/02 | AC-29/36/49/50; biaya, bukti dan audit |
| KF-07 | REPORT-01 | AC-23/25/29/30/41/45/47/49/50; kas induk sekali |
| KF-08 | AUTH-01/03, MENU-01 | AC-02/03; sesi, logout, password lama |
| KF-09 | HOME-01 | AC-12/31/32/42; pengingat, angka kamar dan orang |
| KF-10 | WA-01 | AC-33–35/39/48; penerima/template, bukan bukti terkirim |
| KF-11 | INIT-01 | AC-25–28/44; draft, saldo lama, cutover dan finalisasi |
| KF-12 | AUTH-02 | AC-01; kode setup dan akun pertama saja |

Review di HP mitra meliputi penyelesaian input data awal, kontrak dua orang, cicilan beberapa periode, penggantian penghuni, pembatalan, pesan WA dan laporan. Ukur apakah label terbaca, nominal mudah diperiksa, tombol dapat dijangkau serta error dapat dipulihkan. Checklist/AC bukan bukti uji yang sudah lulus.

## 12. Riwayat perubahan

| Versi | Perubahan |
| --- | --- |
| 1.0 | Spesifikasi UI berdasarkan arah visual oranye pilihan pengguna, referensi Accomodio dan mockup Kamartha; mempertahankan kode setup, menetapkan navigasi/layar, alokasi dan review pembayaran, data awal serta state error/retry. Mengoreksi ringkasan kamar dan checkbox uang diterima dari contoh gambar |
