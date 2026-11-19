# Rencana Pengujian Kamartha

| Metadata | Nilai |
| --- | --- |
| Versi | 1.0 |
| Tanggal | 31 Oktober 2026, WITA |
| Acuan | PRD.md 1.0; architecture/database/uml/design.md 1.0 |
| Status | Rencana, belum hasil eksekusi; seluruh skenario Not Run |
| Target | Flutter Web di HP/laptop, FastAPI, PostgreSQL dan Storage Supabase |

Simpan sebagai `docs/test-plan.md`. Terdapat 50 **kelompok skenario black box**, satu per AC; setiap varian positif/negatif/batas/konkurensi dieksekusi sebagai run terpisah. Ini bukan klaim bahwa 50 test sederhana sudah membuktikan seluruh aplikasi atau bahwa kode telah tersedia.

## 1. Lingkungan dan cara mencatat

- Gunakan PostgreSQL test terisolasi dengan migration nyata; jangan menguji lock/constraint melalui SQLite. Pisahkan Storage test dari bucket/data mitra.
- Catat commit aplikasi, migration revision, versi dependency, OS/browser, ukuran viewport, perangkat dan jaringan. Clock bisnis dapat diinjeksi hanya pada test; jangan menyediakan pengubah tanggal bisnis publik di produksi.
- Data orang/harga/nomor WA sintetis. WA diuji dengan nomor milik tim dan pratinjau; tidak mengirim pesan ke penghuni nyata tanpa instruksi. Tidak menyimpan password, key atau identitas pribadi dalam bukti.
- Setiap keluarga dijalankan pada fixture yang di-reset atau snapshot bersih; jangan mengandalkan mutasi run sebelumnya, kecuali langkah dalam skenario memang berurutan.
- Login/data awal dapat menjadi setup fixture untuk tes fitur lain. Pengujian setup dan finalisasi sendiri tetap memakai flow aplikasi dan database kosong yang sesuai.
- Request gagal sebelum commit, konflik dan timeout respons sesudah commit adalah keadaan berbeda. Fault injection hanya test harness, bukan tombol aplikasi produksi.

Template hasil per varian:

| Run ID | Kasus/varian | Commit/lingkungan | Data/langkah aktual | Ekspektasi | Aktual | Status | Bukti/defect | Penguji/waktu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Belum diisi | BB-xx-P01 / N01 / B01 / C01 | Belum diisi | Belum diisi | Dari skenario | Belum diuji | Not Run | Belum ada | Belum diisi |

P=positif, N=negatif, B=batas, C=konkurensi/retry. Beri ID berurutan untuk beberapa varian sejenis. Status run: Not Run, Pass, Fail atau Blocked. Pass hanya setelah aktual cocok ekspektasi dan bukti tersedia. Satu varian Pass tidak menandai seluruh keluarga lulus. Pemetaan KF/UC/AC mengikuti PRD; detail UI/keamanan teknis juga mengikuti dokumen turunannya.

## 2. Fixture bersama

| Fixture | Data acuan |
| --- | --- |
| F-AUTH | Instalasi kosong untuk setup atau satu akun pengelola untuk login; frasa sandi uji >=8 karakter, bukan kredensial produksi |
| F-OPENING | Cutover 1 Okt 2026; mode Persiapan; invoice lama Rp900.000, opening_paid Rp400.000; termasuk satu invoice berjalan lunas |
| F-LEASE2 | Kamar A-03 kapasitas 2; Andi/Budi; harga total contoh Rp1.000.000/bulan; mulai 1 Okt–1 Des 2026 |
| F-PAY | Invoice Aktif sisa Rp500.000, belum ada penerimaan baru di fixture awal |
| F-MULTI | Clock 30 Okt 2026; satu lease mencakup Okt/Nov; sisa Okt Rp500.000, Nov Rp1.000.000, tempo Nov 1 Nov; total Rp1.500.000 |
| F-REPORT | Transaksi di batas awal/tengah/akhir/di luar rentang; satu penerimaan dua alokasi; satu catatan Batal dan satu saldo lama |
| F-FILES | JPG/PNG/PDF valid, rusak, ekstensi palsu dan berkas batas 2.097.152 byte; tanpa data pribadi |

Tanggal F-MULTI penting: November sudah tersedia H−3, sehingga contoh bukan izin membayar periode yang belum tersedia. Saldo awal tidak dibentuk sebagai payments. Fixture kalender/penerimaan terlambat memakai clock yang ditulis di kasus, bukan tanggal nyata komputer saat pengujian.

## 3. Black box: 50 keluarga skenario

Ekspektasi pada setiap kasus mengutip kebutuhan yang sedang diuji. Varian kegagalan DB/konkurensi diuji sebagai integrasi pendukung di samping pengamatan UI/API; black box tidak berarti boleh memalsukan hasil tanpa koneksi nyata. Bila satu keluarga memuat beberapa varian, catat tiap run terpisah menurut template bagian 1.

### BB-01 — AC-01

- **Acuan:** KF-12, UC-11; AC-01.
- **Prasyarat/data:** Instalasi kosong, kode setup tersedia privat.
- **Langkah utama:** Isi username valid dan frasa sandi >=8 karakter; buat akun; buka setup lagi.
- **Varian wajib:** Kode salah; konfirmasi beda; dua permintaan setup bersamaan.
- **Ekspektasi PRD:** Kode penyiapan benar, akun belum ada dan password/konfirmasi valid: satu akun dibuat lalu registrasi ditutup. Kode salah atau akun sudah ada: tidak membuat akun. Dua pendaftaran bersamaan tidak membuat dua akun.
- **Area pelaksanaan:** auth; AUTH-02; A-01/ST-03; managers/app_settings.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-02 — AC-02

- **Acuan:** KF-08, UC-01; AC-02.
- **Prasyarat/data:** Akun sudah ada, browser tanpa sesi.
- **Langkah utama:** Login sah; buka halaman data dan lampiran; logout; ulangi akses langsung.
- **Varian wajib:** Username/password salah/kosong; kegagalan ke-5/6; idle 119/120/121 menit menurut clock; API tanpa cookie.
- **Ekspektasi PRD:** Login sah membuat sesi; login salah/kosong ditolak. Percobaan dibatasi. Setelah logout atau tanpa sesi, halaman data, endpoint dan lampiran tidak dapat diakses.
- **Area pelaksanaan:** auth; AUTH-01; A-01; sessions/login_windows.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-03 — AC-03

- **Acuan:** KF-08, UC-01; AC-03.
- **Prasyarat/data:** Sesi sah dan password awal diketahui.
- **Langkah utama:** Ganti dengan password lama benar; login ulang; coba sesi dan password lama.
- **Varian wajib:** Password lama salah; baru kurang dari 8/lebih dari 128; konfirmasi berbeda; Lupa password tidak membuka signup.
- **Ekspektasi PRD:** Ganti password meminta password lama; input salah tidak mengubah kredensial. Lupa password tidak membuka registrasi publik.
- **Area pelaksanaan:** auth; AUTH-03/MENU-01; C-04; managers/sessions.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-04 — AC-04

- **Acuan:** KF-01, UC-02; AC-04.
- **Prasyarat/data:** Kamar A-01 tersedia dalam data uji.
- **Langkah utama:** Tambah kamar valid; coba nomor A-01 dan variasi kapital/spasi; periksa fasilitas/harga.
- **Varian wajib:** Harga 0/-1; nomor kosong; upaya hapus kamar bersejarah; perubahan kapasitas yang merusak kontrak.
- **Ekspektasi PRD:** Nomor kamar ganda dan harga tidak positif ditolak. Kamar bersejarah tidak dapat dihapus. Harga/fasilitas ditampilkan sebagai total termasuk air, listrik, Wi-Fi.
- **Area pelaksanaan:** rooms; ROOM-01/02; C-01; rooms.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-05 — AC-05

- **Acuan:** KF-02, UC-03; AC-05.
- **Prasyarat/data:** Daftar penghuni kosong atau dataset terisolasi.
- **Langkah utama:** Tambah orang dengan nama/identitas sah; coba WA kosong/invalid; buka aksi pesan.
- **Varian wajib:** Nama/identitas kosong ditolak; nama sama pada dua orang tidak otomatis dianggap orang sama; WA invalid tidak menghapus orang.
- **Ekspektasi PRD:** Nama/identitas wajib divalidasi. Nomor WA kosong/invalid tidak menghapus penghuni atau menghalangi pencatatan lain, tetapi aksi WA menunjukkan alasan tidak tersedia.
- **Area pelaksanaan:** residents/messaging; RES-01/02; C-01/S-04; residents.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-06 — AC-06

- **Acuan:** KF-03, UC-04; AC-06.
- **Prasyarat/data:** Kamar mendukung dua orang; enam paket seed tersedia.
- **Langkah utama:** Buat kontrak terpisah untuk enam kombinasi dengan harga kesepakatan berbeda; periksa nominal invoice.
- **Varian wajib:** Harga contoh 1 orang bulanan Rp900.000, 2 orang Rp1.300.000, 6 bulan Rp5.000.000; tidak memakai faktor otomatis.
- **Ekspektasi PRD:** Enam kombinasi jenis hunian/periode dapat dipilih. Harga dua orang tidak dihitung otomatis dua kali harga satu orang. Harga 6/12 bulan bukan perkalian otomatis.
- **Area pelaksanaan:** leases/billing; LEASE-01; A-02/C-01; packages/leases.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-07 — AC-07

- **Acuan:** KF-03, UC-04; AC-07.
- **Prasyarat/data:** Penghuni Andi/Budi dan kamar kapasitas 1/2 tersedia.
- **Langkah utama:** Pilih paket satu lalu dua orang, isi jumlah nama dan kontak sesuai; tinjau dan simpan.
- **Varian wajib:** Dua nama sama; satu nama pada paket dua orang; kontak bukan anggota; paket dua orang di kamar kapasitas satu.
- **Ekspektasi PRD:** Paket satu orang menerima satu nama. Paket dua orang memerlukan dua nama berbeda dan satu penanggung jawab dari kedua nama itu. Paket melebihi dukungan kamar atau orang duplikat ditolak.
- **Area pelaksanaan:** leases; LEASE-01; A-02/S-01; occupancies/responsible_history.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-08 — AC-08

- **Acuan:** KF-03, UC-04; AC-08.
- **Prasyarat/data:** Mode Aktif; kamar dan orang tidak benturan.
- **Langkah utama:** Simpan satu kontrak sah; periksa kontrak, penghunian dan tagihan pertama.
- **Varian wajib:** Gangguan uji saat membuat invoice; ulangi permintaan sama; pastikan tidak ada data parsial.
- **Ekspektasi PRD:** Kontrak baru menyimpan kesepakatan dan satu tagihan pertama. Gagal di salah satu penyimpanan membatalkan seluruh perubahan.
- **Area pelaksanaan:** leases/billing; LEASE-01; A-02/S-01; leases/occupancies/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-09 — AC-09

- **Acuan:** KF-03, UC-04; AC-09.
- **Prasyarat/data:** Ada kontrak kamar dan penghunian orang yang bertumpuk.
- **Langkah utama:** Coba kontrak baru pada rentang bertumpuk; coba orang yang sama sebagai pendamping di kamar lain.
- **Varian wajib:** Kontrak habis tetapi orang belum keluar; batas akhir sama awal berikutnya; dua pengajuan kamar sama bersamaan.
- **Ekspektasi PRD:** Benturan kontrak kamar atau benturan orang, termasuk pendamping, ditolak. Hunian lama yang belum ditutup menahan penempatan penghuni berbeda walau kontrak sudah habis.
- **Area pelaksanaan:** leases; LEASE-01/02; A-02/C-01; leases/occupancies.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-10 — AC-10

- **Acuan:** KF-03, UC-04; AC-10.
- **Prasyarat/data:** Andi dan Budi masih tinggal pada kontrak dua orang.
- **Langkah utama:** Keluarkan Budi dengan tanggal sebenarnya; buka penghuni kini dan riwayat; periksa invoice.
- **Varian wajib:** Tanggal keluar masa depan; tanggal sebelum masuk; keluar orang yang sudah keluar.
- **Ekspektasi PRD:** Pada paket dua orang, satu orang keluar: tanggal keluar hanya milik orang itu, jumlah tinggal turun menjadi satu, harga/tagihan tetap, nama lama tetap di riwayat.
- **Area pelaksanaan:** leases; LEASE-02/ROOM-02; A-03; occupancies.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-11 — AC-11

- **Acuan:** KF-03, UC-04; AC-11.
- **Prasyarat/data:** Andi penanggung jawab, Budi tetap tinggal.
- **Langkah utama:** Keluarkan Andi; pilih Budi sebagai penerus; buka pratinjau WA dan riwayat kontak.
- **Varian wajib:** Tidak memilih penerus; penerus orang luar/sudah keluar; gangguan simpan kontak harus rollback keluar.
- **Ekspektasi PRD:** Penanggung jawab keluar sementara orang kedua tinggal: simpan meminta penerus yang valid. Pergantian tercatat dan pesan berikutnya memakai kontak baru; tagihan lama tidak dihapus/dipecah.
- **Area pelaksanaan:** leases/messaging; LEASE-02/WA-01; A-03/S-04; responsible_history.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-12 — AC-12

- **Acuan:** KF-03, UC-04; AC-12.
- **Prasyarat/data:** Kontrak habis, penghunian masih STAYING dan punya piutang.
- **Langkah utama:** Buka kamar lalu lunasi utang; baca status kontrak dan fisik kamar kembali.
- **Varian wajib:** Ulangi pada kontrak habis yang sudah lunas; kedua keadaan tetap perlu konfirmasi bila orang belum keluar.
- **Ekspektasi PRD:** Kontrak habis dan masih ada orang yang belum keluar: kamar Perlu konfirmasi. Pelunasan utang tidak mengubah status kamar menjadi Kosong.
- **Area pelaksanaan:** rooms/leases; ROOM-02/HOME-01; A-03/ST-01; leases/occupancies.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-13 — AC-13

- **Acuan:** KF-03, UC-04; AC-13.
- **Prasyarat/data:** Kontrak dua orang, utang tersisa dan tidak ada kontrak lain yang menahan.
- **Langkah utama:** Keluarkan satu orang lalu yang terakhir melalui alur sah; periksa status kamar dan piutang.
- **Varian wajib:** Satu orang keluar saja; ada kontrak terjadwal lain; pelunasan utang tidak menjadi syarat penghapusan riwayat.
- **Ekspektasi PRD:** Setelah semua orang keluar dan hunian ditutup, kamar dapat menjadi Kosong tanpa menghapus utang. Menutup hanya satu dari dua orang tidak membuat kamar Kosong.
- **Area pelaksanaan:** leases/rooms; LEASE-02; A-03; occupancies/leases/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-14 — AC-14

- **Acuan:** KF-03, UC-04; AC-14.
- **Prasyarat/data:** Kontrak belum habis; satu anggota pernah keluar.
- **Langkah utama:** Perpanjang satu periode penuh dengan paket/harga sama; baca akhir baru dan anggota.
- **Varian wajib:** Paket/harga berubah memakai kontrak baru; permintaan setelah habis; benturan kontrak lanjutan.
- **Ekspektasi PRD:** Perpanjangan sah menambah periode penuh dan tidak menghidupkan kembali hubungan orang yang sudah keluar. Paket/harga baru tidak mengubah riwayat lama.
- **Area pelaksanaan:** leases; LEASE-02; A-03/C-01; leases/business_events.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-15 — AC-15

- **Acuan:** KF-04, UC-05; AC-15.
- **Prasyarat/data:** Sewa 10 Okt 2026–10 Okt 2027, paket enam bulan; clock dapat dikontrol di test.
- **Langkah utama:** Pada 6 Apr 2027 buka menu; lanjut clock 7 Apr dan buka lagi; ulangi beberapa kali.
- **Varian wajib:** Dua synchronize bersamaan; aplikasi baru dibuka 15 Apr harus melengkapi periode yang terlewat.
- **Ekspektasi PRD:** Kontrak enam bulanan mulai 10 Oktober 2026 sampai 10 Oktober 2027: tagihan periode 10 April 2027 tersedia saat menu dibuka 7 April; pada 6 April belum dibentuk. Pembukaan berulang tetap satu tagihan periode.
- **Area pelaksanaan:** billing; HOME-01/INV-01; A-04; invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-16 — AC-16

- **Acuan:** KF-04, UC-05; AC-16.
- **Prasyarat/data:** Sewa berakhir 10 Apr 2027 dan tidak diperpanjang.
- **Langkah utama:** Clock 7 Apr; buka dashboard, daftar invoice dan pengingat akhir sewa.
- **Varian wajib:** Clock 10/11 Apr; tetap tidak membuat periode mulai 10 Apr hanya karena masih ada hunian.
- **Ekspektasi PRD:** Kontrak hanya sampai 10 April tanpa perpanjangan: tidak ada tagihan periode mulai 10 April, meskipun pengingat akhir sewa tampil pada 7 April.
- **Area pelaksanaan:** billing/dashboard; HOME-01/INV-01; A-04; leases/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-17 — AC-17

- **Acuan:** KF-04, UC-05; AC-17.
- **Prasyarat/data:** Fixture kalender jangkar asli 31 Jan.
- **Langkah utama:** Hitung/bentuk periode bulanan Jan–Mar 2027 lalu Jan–Mar 2028.
- **Varian wajib:** 31 Jan→28 Feb→31 Mar; kabisat 29 Feb; paket 6/12 bulan dan peralihan tahun.
- **Ekspektasi PRD:** Mulai 31 Januari 2027 dengan periode bulanan menghasilkan batas 28 Februari lalu 31 Maret. Tahun kabisat memakai 29 Februari.
- **Area pelaksanaan:** billing; LEASE-01/INV-02; A-04; leases/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-18 — AC-18

- **Acuan:** KF-04/05, UC-04/05; AC-18.
- **Prasyarat/data:** Pada 29 Okt, invoice 1 Nov sudah tersedia H-3; kontrak mencakup November.
- **Langkah utama:** Ajukan semua keluar efektif 31 Okt; periksa invoice mendatang yang belum dibayar.
- **Varian wajib:** Fixture terpisah invoice Nov sudah dibayar: pemotongan ditolak; satu penghuni keluar saja tidak membatalkan; invoice periode berjalan tetap.
- **Ekspektasi PRD:** Seluruh penghuni mengakhiri sebelum periode H−3 dimulai: tagihan mendatang tanpa pembayaran dibatalkan beralasan; tagihan mendatang yang sudah menerima pembayaran menghalangi pengakhiran yang memotongnya. Keluar satu orang saja tidak membatalkannya.
- **Area pelaksanaan:** leases/billing; LEASE-02; A-03/A-04; leases/invoices/payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-19 — AC-19

- **Acuan:** KF-05, UC-05; AC-19.
- **Prasyarat/data:** Sisa Rp500.000; hari penerimaan >=cutover dan tidak masa depan.
- **Langkah utama:** Catat Transfer Rp200.000; buka detail invoice, induk dan laporan tanggal penerimaan.
- **Varian wajib:** Cicilan kedua dengan Cash/QRIS; exact remaining; bukti opsional bukan syarat memastikan uang diterima.
- **Ekspektasi PRD:** Sisa Rp500.000 dibayar Transfer Rp200.000: tepat satu pembayaran tersimpan, sisa Rp300.000 dan kas baru Rp200.000 pada tanggal penerimaan.
- **Area pelaksanaan:** payments/reports; PAY-01/03; A-05/S-02; payments/payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-20 — AC-20

- **Acuan:** KF-05, UC-05; AC-20.
- **Prasyarat/data:** Invoice Aktif dengan sisa Rp500.000.
- **Langkah utama:** Kirim varian nominal/metode/tanggal dan invoice Batal; periksa perubahan saldo serta jumlah transaksi.
- **Varian wajib:** Nominal -1,0,1,500000,500001; metode kosong/asing; besok; tidak memaksa status dari klien.
- **Ekspektasi PRD:** Nominal nol, negatif, di atas sisa, metode kosong/di luar pilihan, tanggal masa depan atau tagihan Batal ditolak tanpa perubahan saldo.
- **Area pelaksanaan:** payments; PAY-01/02; A-05/S-02; payments/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-21 — AC-21

- **Acuan:** KF-05, UC-05; AC-21.
- **Prasyarat/data:** Tagihan Rp900.000 jatuh tempo 10 Okt, dibayar Rp400.000.
- **Langkah utama:** Baca status pada tanggal 10 lalu 11; lunasi sisa dan baca lagi.
- **Varian wajib:** Belum dibayar; opening_paid sebagian; CANCELLED harus diutamakan dari sisa nol.
- **Ekspektasi PRD:** Tagihan jatuh tempo 10 Oktober dengan pembayaran sebagian: tanggal 10 masih Dibayar sebagian, tanggal 11 menjadi Menunggak. Sisa nol selalu Lunas untuk tagihan Aktif.
- **Area pelaksanaan:** billing; INV-02; ST-01; invoices/payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-22 — AC-22

- **Acuan:** KF-05, UC-05; AC-22.
- **Prasyarat/data:** Sisa Rp500.000; dua koneksi dan idempotency key terkontrol.
- **Langkah utama:** Ulangi request Rp200.000 dengan key/payload sama; uji dua key masing-masing Rp300.000 bersamaan pada fixture bersih.
- **Varian wajib:** Key sama payload beda; respons hilang sesudah commit; error setelah insert induk sebelum alokasi.
- **Ekspektasi PRD:** Simpan ulang permintaan yang sama tidak menambah pembayaran; permintaan berbeda bersamaan tidak menghasilkan kelebihan bayar. Gagal simpan tidak meninggalkan data parsial.
- **Area pelaksanaan:** payments; PAY-01/03; A-05/S-02; idempotency_records/payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-23 — AC-23

- **Acuan:** KF-05/07, UC-05/08; AC-23.
- **Prasyarat/data:** Pembayaran Rp200.000 Valid pada invoice berutang.
- **Langkah utama:** Batalkan dengan alasan; buka riwayat, sisa dan laporan tanggal asal.
- **Varian wajib:** Alasan kosong; batal ulang idempoten; hari telah melewati tempo; tidak ada transaksi refund baru.
- **Ekspektasi PRD:** Pembayaran dibatalkan beralasan: catatan asal tetap ada, sisa dihitung ulang, nominalnya tidak dihitung dalam kas, dan status mengikuti tanggal acuan terbaru.
- **Area pelaksanaan:** payments/reports; PAY-03; ST-02/S-02; payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-24 — AC-24

- **Acuan:** KF-05, UC-05; AC-24.
- **Prasyarat/data:** Kontrak sudah berakhir, invoice Aktif masih sisa.
- **Langkah utama:** Catat pelunasan; buka invoice, kontrak dan status hunian.
- **Varian wajib:** Mantan penghuni sudah keluar; yang belum keluar tetap perlu konfirmasi; tidak mengubah tanggal kontrak.
- **Ekspektasi PRD:** Kontrak sudah Berakhir, tagihan masih berutang: pelunasan diterima, tagihan Lunas, kontrak tetap Berakhir dan hunian tidak dibuka kembali.
- **Area pelaksanaan:** payments/leases; PAY-03/LEASE-02; A-05; payments/occupancies.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-25 — AC-25

- **Acuan:** KF-11, UC-10; AC-25.
- **Prasyarat/data:** Mode Persiapan; invoice lama nominal Rp900.000, opening_paid Rp400.000.
- **Langkah utama:** Simpan/finalisasi; periksa sisa/kas; catat pembayaran baru Rp200.000.
- **Varian wajib:** Kas awal nol; sisa akhir Rp300.000; jangan membuat baris payments untuk Rp400.000 lama.
- **Ekspektasi PRD:** Tagihan lama Rp900.000, dibayar sebelum sistem Rp400.000: sisa awal Rp500.000 dan kas baru nol. Pembayaran baru Rp200.000 menyisakan Rp300.000 dan kas bertambah Rp200.000.
- **Area pelaksanaan:** initialization/payments; INIT-01/PAY-03; A-01/A-05; invoices/payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-26 — AC-26

- **Acuan:** KF-11, UC-10; AC-26.
- **Prasyarat/data:** Data awal dua orang, satu telah keluar; invoice berjalan sudah lunas.
- **Langkah utama:** Masukkan keadaan per orang dan invoice lunas; finalisasi; buka menu berulang.
- **Varian wajib:** Unknown tanggal keluar terverifikasi tidak diarang; belum lengkap tetap draft; tidak menggandakan invoice berjalan lunas.
- **Ekspektasi PRD:** Data awal dua orang dapat memuat satu sudah keluar dan satu masih tinggal; saldo tagihan kamar tetap satu. Tagihan berjalan lunas tidak dibentuk ulang setelah finalisasi.
- **Area pelaksanaan:** initialization/billing; INIT-01; A-01/A-04; occupancies/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-27 — AC-27

- **Acuan:** KF-11, UC-10; AC-27.
- **Prasyarat/data:** Mode Persiapan dengan beberapa draft.
- **Langkah utama:** Coba finalisasi tiap varian salah; perbaiki berkas dan ulang simpan key sama.
- **Varian wajib:** Opening_paid -1 atau amount+1; periode sama; benturan kamar/orang; identitas/tanggal wajib belum tersedia.
- **Ekspektasi PRD:** Saldo lama negatif/melebihi nominal, periode ganda, benturan orang/kamar atau data wajib belum lengkap menolak finalisasi. Simpan ulang berkas tidak menggandakan data.
- **Area pelaksanaan:** initialization; INIT-01; A-01; initialization_records.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-28 — AC-28

- **Acuan:** KF-11, UC-10; AC-28.
- **Prasyarat/data:** Data awal lengkap dan rekap cocok buku fixture.
- **Langkah utama:** Tinjau/finalisasi; coba edit cutover dan saldo awal lewat UI/API; ulangi finalisasi.
- **Varian wajib:** Dua finalisasi bersamaan; form Persiapan masih terbuka pada tab lain; transaksi operasional belum aktif sebelum commit.
- **Ekspektasi PRD:** Finalisasi sah membuka mode Aktif dan mengunci saldo awal/tanggal batas. Mengulang finalisasi tidak mereset operasional.
- **Area pelaksanaan:** initialization; INIT-01; A-01/ST-03; app_settings/initialization_finalizations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-29 — AC-29

- **Acuan:** KF-06/07, UC-06/08; AC-29.
- **Prasyarat/data:** Mode Aktif dan invoice penghuni sudah ada.
- **Langkah utama:** Catat Internet/Wi-Fi Rp350.000 dengan tanggal sah; periksa laporan dan nominal invoice.
- **Varian wajib:** Nominal nol/negatif; sebelum cutover; besok; kategori luar pilihan; air/listrik juga tidak menambah tagihan penghuni.
- **Ekspektasi PRD:** Biaya Internet/Wi-Fi dicatat sebagai pengeluaran: total pengeluaran bertambah; tagihan penghuni tidak bertambah. Nominal/tanggal invalid ditolak.
- **Area pelaksanaan:** expenses/reports; EXP-01/02; A-06/C-03; expenses.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-30 — AC-30

- **Acuan:** KF-07, UC-08; AC-30.
- **Prasyarat/data:** Transaksi tanggal awal, tengah, akhir dan luar rentang; ada saldo lama.
- **Langkah utama:** Buka laporan dua batas tanggal; cocokkan total dan rincian.
- **Varian wajib:** date_from>date_to; sebelum cutover; data kosong nol; awal bulan pertama memakai cutover bila lebih akhir.
- **Ekspektasi PRD:** Dua batas tanggal laporan termasuk, tanggal sebelum batas pencatatan/rentang terbalik ditolak, data kosong menghasilkan nol, saldo pembayaran lama dikecualikan.
- **Area pelaksanaan:** reports; REPORT-01; A-06; payments/expenses.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-31 — AC-31

- **Acuan:** KF-09, UC-07; AC-31.
- **Prasyarat/data:** Invoice tempo 1 Nov belum lunas dan sewa berakhir 1 Des.
- **Langkah utama:** Periksa 28/29 Okt, 1/2 Nov; lunasi; lihat daftar tagihan dan akhir sewa.
- **Varian wajib:** H-4 tidak muncul reminder tagihan; H-3 muncul; akhir sewa tetap punya reminder sendiri walau invoice lunas.
- **Ekspektasi PRD:** Pengingat tagihan muncul mulai H−3, tetap terlihat saat tempo dan menjadi tunggakan setelah lewat; lunas menghentikan pengingat pembayaran tanpa menghilangkan pengingat akhir sewa.
- **Area pelaksanaan:** dashboard/billing; HOME-01; A-04/ST-01; invoices/leases.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-32 — AC-32

- **Acuan:** KF-09, UC-07; AC-32.
- **Prasyarat/data:** 10 kamar: 7 Dihuni, 2 Kosong, 1 Perlu konfirmasi; daftar orang fixture diverifikasi.
- **Langkah utama:** Buka dashboard dan filter kamar; hitung orang aktual dan kamar secara terpisah.
- **Varian wajib:** Satu kamar dua orang; orang dilanjutkan tidak dua kali; kontrak habis tidak mengurangi orang masih tinggal.
- **Ekspektasi PRD:** Dashboard membedakan jumlah kamar, jumlah orang, kontrak aktif dan hunian perlu konfirmasi. Satu kamar dua penghuni berarti satu kamar dihuni dan dua orang tinggal.
- **Area pelaksanaan:** dashboard/rooms; HOME-01/ROOM-01; C-01; occupancies/rooms.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-33 — AC-33

- **Acuan:** KF-10, UC-09; AC-33.
- **Prasyarat/data:** Satu invoice baru dan satu invoice yang sudah menerima cicilan.
- **Langkah utama:** Catat pembayaran pertama masing-masing; buka pesan; catat cicilan berikutnya dan buka pesan.
- **Varian wajib:** Pembayaran Batal ditolak sebagai sumber valid; tentukan pertama berdasarkan alokasi induk Valid.
- **Ekspektasi PRD:** Konfirmasi pembayaran pertama setiap tagihan memuat periode/paket, nominal terpilih dan sisa terbaru; cicilan berikutnya menyediakan konfirmasi. Pembayaran Batal ditolak sebagai sumber konfirmasi valid.
- **Area pelaksanaan:** messaging; WA-01; S-04; payments/payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-34 — AC-34

- **Acuan:** KF-10, UC-09; AC-34.
- **Prasyarat/data:** Penanggung jawab mempunyai nomor uji yang dikendalikan tim.
- **Langkah utama:** Buka pratinjau; cocokkan penerima dan teks; buka WA di HP tanpa mengirim ke orang lain.
- **Varian wajib:** WA kosong/invalid; format lokal/internasional; paket dua orang selalu kontak administratif terkini.
- **Ekspektasi PRD:** Nomor WA invalid ditolak; nomor valid membuka penerima dan teks yang sesuai. Paket dua orang memakai penanggung jawab yang dipilih. Tidak ada status terkirim otomatis.
- **Area pelaksanaan:** messaging; WA-01; S-04; residents/responsible_history.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-35 — AC-35

- **Acuan:** KF-10, UC-09; AC-35.
- **Prasyarat/data:** Pembayaran sudah commit; akses WA dapat sengaja diblok.
- **Langkah utama:** Klik Buka WhatsApp; batalkan atau gagalkan pembukaan; kembali ke aplikasi dan baca saldo.
- **Varian wajib:** Jangan mengirim pesan nyata tanpa otorisasi; tidak ada status otomatis terkirim/dibaca atau rollback uang.
- **Ekspektasi PRD:** WA gagal dibuka atau pengelola tidak mengirim: pembayaran yang sudah tersimpan tetap ada dan saldo tetap benar. Tidak ada perubahan finansial karena klik tautan.
- **Area pelaksanaan:** messaging/payments; WA-01/PAY-03; S-04; payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-36 — AC-36

- **Acuan:** KF-05/06; AC-36.
- **Prasyarat/data:** Sesi valid dan fixture file nonpribadi.
- **Langkah utama:** Upload JPG/PNG/PDF valid pada pembayaran dan pengeluaran; buka melalui endpoint sah.
- **Varian wajib:** Ukuran 2097151/2097152/2097153 byte; file kosong/rusak; ekstensi palsu; akses file tanpa sesi.
- **Ekspektasi PRD:** Lampiran JPG/PNG/PDF sampai 2 MB diterima bila valid. Tipe lain, file rusak/tidak sesuai tipe atau melebihi batas ditolak dengan pesan yang jelas.
- **Area pelaksanaan:** attachments; PAY-01/EXP-02; S-03; attachments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-37 — AC-37

- **Acuan:** KF-02/03, UC-03/04; AC-37.
- **Prasyarat/data:** Andi/Budi pada kontrak dua orang; Andi keluar tanggal 15, akhir kontrak tanggal 30.
- **Langkah utama:** Tambahkan Citra masuk tanggal 15 atau sesudahnya sebelum akhir; baca anggota, riwayat dan saldo.
- **Varian wajib:** Riwayat tiga nama, kini Budi/Citra; harga/akhir/utang tetap; tidak ada overwrite resident lama.
- **Ekspektasi PRD:** Andi/Budi pada kontrak dua orang: Andi keluar, Citra masuk sesudahnya sebelum kontrak berakhir. Riwayat memuat tiga nama, yang tinggal Budi/Citra; harga, tanggal akhir, tagihan dan sisa tetap.
- **Area pelaksanaan:** leases; LEASE-02; A-03/C-01; occupancies.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-38 — AC-38

- **Acuan:** KF-03, UC-04; AC-38.
- **Prasyarat/data:** Kontrak dua orang dengan variasi kapasitas/tanggal.
- **Langkah utama:** Coba masuk pengganti ketika penuh, sebelum orang lama keluar, pada tanggal benturan, masa depan atau batas akhir kontrak.
- **Varian wajib:** Batas sama tanggal keluar boleh jika tidak overlap; entered_on=akhir kontrak ditolak karena akhir eksklusif.
- **Ekspektasi PRD:** Menambah orang ketika dua orang masih tinggal, tanggal masuk sebelum keluarnya orang yang digantikan, benturan orang, tanggal masa depan atau masuk setelah akhir kontrak ditolak tanpa perubahan.
- **Area pelaksanaan:** leases; LEASE-02; A-03; occupancies.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-39 — AC-39

- **Acuan:** KF-03/10, UC-04/09; AC-39.
- **Prasyarat/data:** Budi tetap penanggung jawab saat Andi diganti Citra; utang masih ada.
- **Langkah utama:** Simpan pengganti tanpa ubah kontak; lalu lakukan pergantian kontak eksplisit dengan alasan.
- **Varian wajib:** Kontak lama tetap sampai dipilih ulang; kontak orang luar/keluar ditolak; tidak membuat utang per nama.
- **Ekspektasi PRD:** Penggantian penghuni tidak otomatis mengganti penanggung jawab yang masih tinggal atau membagi tunggakan. Perubahan kontak yang dipilih pengelola memakai penghuni yang masih tinggal dan mempertahankan riwayat.
- **Area pelaksanaan:** leases/messaging; LEASE-02/WA-01; A-03/S-04; responsible_history.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-40 — AC-40

- **Acuan:** KF-03, UC-04; AC-40.
- **Prasyarat/data:** Alur pengganti sah dan fault injection tersedia hanya di test.
- **Langkah utama:** Gagalkan simpan sebelum commit; kemudian kirim request sah dengan key sama berulang.
- **Varian wajib:** Dua request serentak tidak membuat orang ketiga; transaksi gagal tidak mengubah kontak atau harga.
- **Ekspektasi PRD:** Simpan pengganti gagal atau permintaan yang sama diulang: tidak ada hubungan orang ganda atau perubahan harga/tagihan; keadaan terakhir yang sah tetap konsisten.
- **Area pelaksanaan:** leases; LEASE-02; A-03; occupancies/idempotency_records.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-41 — AC-41

- **Acuan:** KF-05/07, UC-05/08; AC-41.
- **Prasyarat/data:** Clock 12 Okt; cutover <=10 Okt; invoice Rp900.000 tempo 10 Okt tersedia secara logis.
- **Langkah utama:** Catat penuh received_on=10 Okt; buka detail dan laporan tanggal 10 serta 12.
- **Varian wajib:** Kas tanggal 10 Rp900.000 dan tanggal 12 nol untuk fixture itu; recorded_at tanggal 12 immutable; status Lunas.
- **Ekspektasi PRD:** Tagihan Rp900.000 jatuh tempo 10 Oktober, uang pelunasan penuh diterima 10 Oktober tetapi dicatat 12 Oktober: tanggal bayar 10, waktu catat otomatis 12, status setelah simpan Lunas, pemasukan masuk rekap tanggal 10.
- **Area pelaksanaan:** payments/reports; PAY-03/REPORT-01; A-05/ST-01; payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-42 — AC-42

- **Acuan:** KF-05/09, UC-05/07; AC-42.
- **Prasyarat/data:** Fixture AC-41 terpisah, belum ada pembayaran.
- **Langkah utama:** Catat Rp400.000 diterima 10 Okt saat input 12 Okt; baca sisa dan tempo.
- **Varian wajib:** Sisa Rp500.000 Menunggak pada 12 Okt, tempo tetap 10; kas tetap tanggal penerimaan.
- **Ekspektasi PRD:** Dari tagihan Rp900.000, cicilan Rp400.000 diterima 10 Oktober dan dicatat 12 Oktober: sisa Rp500.000 dan status pada 12 Oktober tetap Menunggak; tanggal cicilan tepat waktu tidak menggeser jatuh tempo sisa.
- **Area pelaksanaan:** payments/billing; PAY-03/INV-02; ST-01; payments/invoices.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-43 — AC-43

- **Acuan:** KF-04/05, UC-05; AC-43.
- **Prasyarat/data:** Periode mulai 10 Okt baru dimaterialisasi 12 Okt; ketersediaan logis sejak 7 Okt.
- **Langkah utama:** Catat penerimaan sah tanggal 10 Okt; periksa tanggal bayar dan waktu input.
- **Varian wajib:** Penerimaan periode berikutnya sebelum H-3 ditolak; tidak mengizinkan data sebelum cutover atau di luar kontrak.
- **Ekspektasi PRD:** Tagihan periode sah yang memenuhi aturan H−3 baru dilengkapi saat aplikasi dibuka setelah tanggal penerimaan: tanggal uang diterima yang sah tetap dapat dipakai walaupun lebih awal dari waktu pembuatan catatan tagihan. Waktu pencatatan otomatis tidak dapat diedit untuk menyamarkan input terlambat.
- **Area pelaksanaan:** billing/payments; PAY-01/03; A-04/S-02; invoices/payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-44 — AC-44

- **Acuan:** KF-05/11, UC-05/10; AC-44.
- **Prasyarat/data:** Cutover 1 Okt dan mode Aktif, clock 12 Okt.
- **Langkah utama:** Coba penerimaan 30 Sep dan 13 Okt; periksa saldo, mode serta data awal.
- **Varian wajib:** Tanggal 1 Okt dan 12 Okt diuji bila periode logis sah; penolakan tidak membuka ulang Persiapan.
- **Ekspektasi PRD:** Tanggal bayar sebelum batas pencatatan atau di masa depan ditolak sebagai pembayaran operasional. Penerimaan sebelum batas termasuk saldo awal sesuai prosedur; penolakan tidak mengubah waktu catat/saldo dan tidak membuka ulang finalisasi.
- **Area pelaksanaan:** payments/initialization; PAY-01/INIT-01; A-01/A-05; app_settings/payments.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-45 — AC-45

- **Acuan:** KF-05/07, UC-05/08; AC-45.
- **Prasyarat/data:** Clock 30 Okt, cutover 1 Okt; invoice Okt sisa Rp500.000 dan Nov sisa Rp1.000.000, periode mulai 1 Nov sudah H-3.
- **Langkah utama:** Catat total Rp1.500.000 dengan dua alokasi; baca dua invoice, induk dan laporan.
- **Varian wajib:** Pemasukan tepat Rp1.500.000, kedua sisa nol, satu induk dan dua rincian.
- **Ekspektasi PRD:** Penerimaan Rp1.500.000 dialokasikan Rp500.000 melunasi Oktober dan Rp1.000.000 melunasi November pada masa sewa sama: dua saldo benar dan kas bertambah tepat Rp1.500.000 sekali.
- **Area pelaksanaan:** payments/reports; PAY-01/03; S-02/C-02; payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-46 — AC-46

- **Acuan:** KF-05, UC-05; AC-46.
- **Prasyarat/data:** Fixture dua tagihan dari AC-45 dan satu tagihan kontrak lain.
- **Langkah utama:** Kirim total tidak cocok lalu bagian tidak valid; ganti salah satu invoice ke kontrak lain.
- **Varian wajib:** Bagian nol/negatif/melebihi sisa; invoice Batal; kegagalan satu bagian tidak menyimpan bagian lain.
- **Ekspektasi PRD:** Total alokasi tidak sama dengan penerimaan, bagian nol/negatif, melebihi sisa, tagihan Batal atau lintas masa sewa ditolak; tidak ada pembayaran/alokasi sebagian tersimpan.
- **Area pelaksanaan:** payments; PAY-01/02; A-05/S-02; payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-47 — AC-47

- **Acuan:** KF-05/07, UC-05/08; AC-47.
- **Prasyarat/data:** Dua invoice satu kontrak dan fasilitas konkurensi dua koneksi.
- **Langkah utama:** Retry penerimaan multiinvoice, jalankan dua pembayaran bersamaan, lalu batalkan induk sah beralasan.
- **Varian wajib:** Saldo tidak berlebih; seluruh alokasi induk batal dikecualikan, kas turun sekali, asal tetap tersimpan.
- **Ekspektasi PRD:** Pengulangan permintaan tidak menggandakan penerimaan; pembayaran bersamaan tidak melampaui saldo. Membatalkan penerimaan beralasan membatalkan seluruh alokasinya, memulihkan sisa dan mengecualikan total kas sekali; riwayat utuh.
- **Area pelaksanaan:** payments/reports; PAY-03; S-02/ST-02; payments/payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-48 — AC-48

- **Acuan:** KF-10, UC-09; AC-48.
- **Prasyarat/data:** Penerimaan AC-45 dan nomor WA milik tim.
- **Langkah utama:** Buka pratinjau; cocokkan total, periode, alokasi dan sisa masing-masing.
- **Varian wajib:** Satu alokasi merupakan pembayaran pertama sementara invoice lain sudah punya cicilan; pesan tidak menggandakan total.
- **Ekspektasi PRD:** Konfirmasi WA penerimaan beberapa periode menampilkan total uang, alokasi tiap periode dan sisa terbaru tanpa penggandaan. Penentuan pembayaran pertama dilakukan per tagihan berdasarkan alokasi Valid.
- **Area pelaksanaan:** messaging; WA-01; S-04/C-02; payment_allocations.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-49 — AC-49

- **Acuan:** KF-06/07, UC-06/08; AC-49.
- **Prasyarat/data:** Pengeluaran Valid Rp150.000, versi awal dan rentang laporan terkontrol.
- **Langkah utama:** Koreksi Rp100.000 dengan alasan; pindahkan tanggal ke rentang lain; lihat audit dan laporan.
- **Varian wajib:** Alasan kosong; versi stale; tanggal/nominal invalid; fault sebelum audit commit harus rollback seluruh perubahan.
- **Ekspektasi PRD:** Pengeluaran Rp150.000 dikoreksi menjadi Rp100.000 dengan alasan: nilai lama/baru, pelaku dan waktu server tetap dapat ditelusuri; laporan memakai Rp100.000. Jika tanggal diubah, laporan rentang lama/baru ikut benar; koreksi invalid atau gagal tidak mengubah data dan riwayat sebagian.
- **Area pelaksanaan:** expenses/reports; EXP-02/REPORT-01; A-06/C-03; expenses/expense_audits.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

### BB-50 — AC-50

- **Acuan:** KF-06/07, UC-06/08; AC-50.
- **Prasyarat/data:** Dua pengeluaran duplikat telah dicatat pada dataset terisolasi.
- **Langkah utama:** Batalkan satu dengan alasan; lihat riwayat dan laporan; coba tanpa alasan.
- **Varian wajib:** Batal ulang tidak mengurangi kas dua kali; tidak ada delete permanen atau transaksi refund otomatis.
- **Ekspektasi PRD:** Pengeluaran duplikat dibatalkan dengan alasan: catatan dan riwayat tetap tersimpan, tidak dihitung pada laporan. Tanpa alasan ditolak; tidak tersedia hapus permanen atau transaksi refund otomatis.
- **Area pelaksanaan:** expenses/reports; EXP-02/REPORT-01; A-06/C-03; expenses/expense_audits.
- **Hasil aktual / bukti / penguji / waktu:** belum diisi. **Status: Not Run.**

## 4. Pengujian kualitas dan keamanan tambahan

| ID | Langkah dan target | Bukti yang diperlukan | Status |
| --- | --- | --- | --- |
| Q-01 | Ukur pencarian/laporan lokal pada 100 kamar, 500 penghuni historis dan 10.000 transaksi; target PRD <=3 detik | Perangkat, query, data, waktu respons/render dan hasil aktual; hosting/HP dicatat terpisah | Not Run |
| Q-02 | Selesaikan setup, kontrak dua orang, cicilan, keluar, WA dan laporan pada viewport 360/390/430 serta laptop 1280 | Screenshot/rekaman, tombol tidak tertutup keyboard/nav, baris akhir dapat diakses | Not Run |
| Q-03 | Perbesar teks/zoom, navigasi keyboard dan uji label status tanpa bergantung warna | Fokus terlihat, label/input terbaca, pesan error terhubung; kontras token diperiksa aktual | Not Run |
| Q-04 | Direct API tanpa sesi, cookie dicabut/idle, CSRF salah/hilang dan Origin tidak sah | Respons ditolak, DB tidak berubah, tidak ada secret/SQL bocor | Not Run |
| Q-05 | Uji Data API anonim Supabase dan akses langsung tabel privat | Tabel bisnis tidak dapat dibaca/ditulis klien; runtime role tidak punya privilege owner | Not Run |
| Q-06 | Putus jaringan setelah commit, ulang key; ubah payload dengan key sama | Satu hasil bisnis dan konflik 409 pada payload berbeda; UI membaca saldo terbaru | Not Run |
| Q-07 | Upload bersamaan cleaner: STAGED→DELETING tidak dapat ditautkan; LINKED/audit tidak dibersihkan | Objek, metadata dan referensi konsisten; retry penghapusan aman | Not Run |
| Q-08 | Restore dump dan objek ke lingkungan terisolasi; cocokkan saldo/jumlah/checksum, cabut sesi pulihan sebelum akses produksi | Manifest, migration, log restore aman, lama pemulihan dan hasil verifikasi | Not Run |
| Q-09 | Koreksi data saat laporan dibaca; cocokkan total dan rincian satu snapshot | Tidak ada header/detail dari versi berbeda; kas induk tidak berulang | Not Run |
| Q-10 | Periksa build Flutter dan log server/repo atas kredensial serta data pribadi | Tidak ada DB password, secret Storage, token/cookie/password atau identitas sensitif pada artefak publik | Not Run |

## 5. White box: berdasarkan kode aktual

White box dilakukan setelah fungsi tersedia. Nama fungsi di bawah adalah kandidat tanggung jawab, bukan klaim nama/path kode yang sudah ada. Buat CFG dari fungsi yang benar-benar diimplementasikan pada commit yang dicatat. Semua hasil/cakupan belum diukur.

| ID | Kandidat logika | Percabangan/jalur yang harus dibuktikan | Acuan utama |
| --- | --- | --- | --- |
| WB-01 | Registrasi singleton dan autentikasi/sesi | Kode salah/benar, akun sudah ada, login gagal, throttle, idle, logout dan password lama | BB-01–03, Q-04 |
| WB-02 | Kalender jangkar dan periode sah | Akhir bulan/kabisat, 1/6/12 bulan, H−4/H−3, akhir eksklusif dan cutover | BB-15–18/43 |
| WB-03 | Status dan sisa tagihan | Batal, nol, positif setelah tempo, sebagian dan belum dibayar; saldo negatif sebagai invariant violation | BB-19–21/41/42 |
| WB-04 | Penerimaan/alokasi | Total tepat/tidak, setiap bagian valid/invalid, lintas lease, tanggal sah, banyak invoice | BB-19/20/43–46 |
| WB-05 | Idempotency dan transaksi | Key baru/replay/konflik, exception sebelum commit, commit respons hilang; rollback audit/alokasi | BB-08/22/40/47/49, Q-06 |
| WB-06 | Benturan interval dan kapasitas | Orang/kamar bertumpuk, batas berdampingan, tanggal unknown migrasi, hunian belum ditutup | BB-07/09/12/13/38 |
| WB-07 | Kontak, keluar, pengganti dan lanjutan | Kontak keluar/penerus, sisa satu/semua, kontrak habis, pengganti penuh, identitas lama tetap | BB-10–14/37–40 |
| WB-08 | Data awal dan finalisasi | Draft valid/invalid, agregat saldo, mode sebelum/sesudah dan finalisasi ulang | BB-25–28/44 |
| WB-09 | Pembatalan dan audit biaya | Alasan kosong/valid, versi stale, gagal audit, tanggal pindah rentang, batal ulang | BB-23/49/50 |
| WB-10 | Template pesan dan kontak | Pertama per invoice/cicilan, induk Batal, nomor invalid, banyak alokasi dan kontak terakhir | BB-33–35/39/48 |
| WB-11 | Query laporan | Valid/Batal, batas inklusif, saldo lama dikecualikan dan induk dengan banyak alokasi | BB-25/29/30/41/45/47/49/50 |
| WB-12 | Siklus lampiran | File sah/rusak, pemilik staged benar/salah, expired/DELETING/LINKED, kompensasi Storage | BB-36, Q-07 |

Untuk setiap fungsi terpilih:

1. Catat path/simbol, rentang baris, commit, input/return dan dependency aktual.
2. Gambar CFG aktual serta beri ID node/edge. Tentukan satu aturan penghitung keputusan termasuk compound boolean sesuai rubrik dosen dan gunakan konsisten.
3. Hitung V(G)=E−N+2P pada graf yang didefinisikan; untuk satu graf terhubung P=1. Jangan mengisi E/N atau kompleksitas dari diagram rancangan dan jangan menebak nilai sebelum kode tersedia.
4. Tentukan himpunan jalur independen, data agar jalur ditempuh, assertion efek/hasil serta status eksekusi. Jelaskan jalur infeasible dengan alasan, bukan mengklaim semuanya tercapai.
5. Jalankan pytest dan coverage.py dengan branch coverage; simpan laporan aktual beserta fungsi/branch yang belum diuji. Target rancangan adalah semua cabang aturan bisnis kritis mempunyai test, bukan janji cakupan 100% seluruh repo.
6. Uji DB lock/konkurensi dengan koneksi PostgreSQL terpisah. Unit mock hanya membuktikan fungsi lokal, bukan atomisitas/locking database.

Template catatan white box:

| WB/fungsi | Commit/path | Node/edge dan V(G) | Jalur & data | Test aktual | Statement/branch aktual | Hasil/bukti |
| --- | --- | --- | --- | --- | --- | --- |
| Belum dipilih | Belum ada | Belum dihitung | Belum dibuat dari CFG | Belum dijalankan | Belum diukur | Not Run |

## 6. UAT bersama mitra

Pengelola mencoba melalui HP nyata: login; data awal dan rekap; kontrak satu/dua orang; cicilan beberapa metode/periode; keluar satu orang dan pengganti; konfirmasi hunian; pesan WA; pengeluaran/koreksi dan laporan. Gunakan data yang telah diperiksa; jangan mengirim pesan nyata sebagai efek tak sengaja demo.

Catat tugas, langkah yang membuat bingung, bantuan yang dibutuhkan, kesalahan, komentar, keputusan perbaikan dan retest. UAT bukan sekadar tanda tangan tanpa percobaan. Tarif/kamar nyata dan penerimaan WA manual oleh dosen tetap perlu diverifikasi; dokumen ini tidak mengklaim telah mendapat persetujuan pihak lain.

## 7. Defect, prioritas dan kriteria selesai

| Tingkat | Contoh | Tindakan |
| --- | --- | --- |
| Blocker | Data hilang, akses tanpa izin, transaksi mengganda, saldo salah, kamar masih dihuni ditawarkan kosong | Hentikan penyerahan; perbaiki dan retest jalur terkait |
| Major | Fitur wajib gagal, finalisasi terhambat, form HP tidak dapat diselesaikan | Selesaikan sebelum uji penerimaan final |
| Minor | Kekeliruan tampilan yang tidak menghalangi tugas dan tidak mengubah makna data | Catat, prioritaskan dan setujui keputusan rilis secara eksplisit |

Defect mencatat ID, run asal, expected/actual, langkah reproduksi, bukti, commit, severity, penanggung jawab, status dan retest. Severity berbeda dari prioritas jadwal. Kriteria siap presentasi: semua KF wajib berjalan, varian kritis saldo/akses/hunian lulus, tidak ada Blocker/Major terbuka, hasil 50 keluarga ditinjau per varian, backup/restore dicoba dan bukti disimpan. Jangan menandai kasus Blocked sebagai Pass untuk memenuhi persentase.

Unit/integrasi dibuat selama pekan 12–14; fitur selesai akhir pekan 14; pengujian formal/perbaikan/retest/UAT pekan 15; presentasi pekan 16. Tanggal kalender dan pembagian anggota belum diberikan. Format white box akhir disesuaikan rubrik dosen sebelum eksekusi formal.

## 8. Riwayat perubahan

| Versi | Perubahan |
| --- | --- |
| 1.0 | Rencana 50 keluarga black box dari AC PRD, 10 kualitas/keamanan, 12 area white box, template bukti/defect, fixture dan UAT. Tidak berisi hasil lulus atau cakupan rekaan |
