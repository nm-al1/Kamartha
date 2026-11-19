# PRD Kamartha

| Metadata | Nilai |
| --- | --- |
| Versi | 1.0 |
| Status | Final baseline kebutuhan produk versi pertama; disetujui pengguna untuk dilanjutkan ke arsitektur |
| Produk | Kamartha Sistem Informasi Manajemen Kos |
| Sasaran | Satu kos milik mitra, satu akun pengelola, penggunaan utama melalui HP |
| Acuan dokumen | Proposal_Kamartha_Revisi_Fasilitas_dan_Hunian.docx versi 6 |
| Acuan tambahan | Keputusan diskusi tentang paket satu/dua orang, satu tagihan kamar, keluarnya satu penghuni, dan jadwal pekan 11–16 |
| Bahasa dan zona waktu | Bahasa Indonesia; Asia/Makassar |
| Tenggat | Fitur wajib selesai pekan 14; pengujian formal pekan 15; presentasi pekan 16 |

PRD ini mendefinisikan perilaku Kamartha, batas fitur, serta kriteria penerimaan untuk implementasi dan pengujian. Kamartha membantu pengelola menggantikan pencatatan operasional kos secara manual dengan data terpusat yang dapat digunakan melalui HP.

PRD 1.0 menjadi acuan kebutuhan produk berdasarkan persetujuan pengguna untuk finalisasi. Ini bukan pernyataan bahwa aplikasi sudah dibuat, diuji atau disetujui ulang oleh dosen. Kode KF dan UC mengikuti proposal versi 6; perubahan setelah proposal tersebut dirinci di bagian 10 dan wajib disinkronkan. Pilihan teknologi dirumuskan pada architecture.md. Harga nyata, perangkat mitra dan ketentuan penilaian merupakan kebutuhan validasi eksternal, bukan alasan membuka ulang seluruh ruang lingkup. Perubahan perilaku produk setelah versi ini memerlukan catatan perubahan serta pembaruan kriteria uji.

## 1. Masalah dan tujuan

### 1.1 Masalah yang ditangani

- Data kamar, penghuni, sewa, tagihan dan transaksi tersebar di catatan manual.
- Pengecekan sisa pembayaran, tunggakan dan akhir sewa memerlukan pemeriksaan ulang.
- Rekap pemasukan serta pengeluaran berisiko salah hitung atau terlewat.
- Data lama sudah ada dan harus dimasukkan tanpa menggandakan pemasukan.
- Dua penghuni dalam satu kamar perlu dicatat sebagai dua orang, sementara harga dan tagihan tetap untuk satu kamar.

### 1.2 Hasil yang diharapkan

1. Pengelola dapat melihat penghuni dan keadaan kamar, termasuk kontrak yang habis tetapi huniannya belum dikonfirmasi.
2. Tagihan mengikuti paket dan harga kesepakatan, dengan sisa yang dapat ditelusuri ke saldo lama dan pembayaran baru.
3. Laporan kas menjumlah uang operasional yang benar-benar diterima serta pengeluaran, tanpa mengakui saldo pembayaran lama ulang.
4. Pengelola memperoleh daftar pengingat H−3 dan teks WhatsApp yang siap ditinjau serta dikirim.
5. Seluruh fitur wajib dapat didemonstrasikan dan diuji berdasarkan kebutuhan yang sama dengan proposal.

### 1.3 Ukuran keberhasilan

| Ukuran | Bukti penerimaan |
| --- | --- |
| Rekap migrasi cocok dengan buku mitra | Total tunggakan per periode dan keseluruhan sama setelah ditinjau pengelola |
| Saldo transaksi konsisten | Semua kasus hitung saldo, pembayaran, pembatalan dan laporan menghasilkan angka yang diharapkan |
| Tidak ada penagihan ganda | Pembukaan menu berulang dan pengiriman ulang permintaan yang sama tidak menambah catatan ganda |
| Paket dua orang berjalan | Satu kontrak/kamar memiliki dua nama, satu penanggung jawab dan satu tagihan per periode |
| Tidak ada kamar kosong palsu | Kontrak habis dengan hunian belum ditutup menghalangi penempatan penghuni berbeda |
| Dapat dipakai melalui HP | Pengelola dapat menyelesaikan skenario utama tanpa tombol/formulir terpotong |
| Siap ujian | Kebutuhan, kasus uji, bukti hasil aktual dan temuan dapat ditelusuri; hasil belum diisi sebelum pengujian |

## 2. Pengguna dan batas akses

### 2.1 Pengelola

Pengelola merupakan satu-satunya pengguna aplikasi. Satu instalasi melayani satu kos dan satu akun pengelola. Pengelola mengisi data, memverifikasi penerimaan uang, meninjau saldo awal, mengonfirmasi keadaan penghuni, serta mengirim pesan melalui WhatsApp.

Registrasi tidak terbuka untuk umum. Registrasi awal hanya membuat akun pertama menggunakan akses penyiapan yang diberikan kepada mitra. Setelah berhasil, pendaftaran ditutup.

### 2.2 Penghuni

Penghuni tidak memiliki akun atau portal. Penghuni membayar di luar aplikasi dan menerima komunikasi dari pengelola. Pada paket dua orang, dua nama dicatat tetapi tagihan tetap satu untuk kamar tersebut.

Penanggung jawab adalah kontak administratif kontrak dan tujuan utama pesan tagihan/akhir sewa. Penetapan atau penggantian kontak ini tidak menyatakan pemindahan tanggung jawab utang lama secara otomatis.

## 3. Ruang lingkup versi pertama

### 3.1 Fitur wajib

| Kode | Fitur | Use case |
| --- | --- | --- |
| KF-01 | Data kamar, kapasitas yang didukung, harga referensi dan ketersediaan | UC-02 |
| KF-02 | Data penghuni, identitas dan nomor WhatsApp | UC-03 |
| KF-03 | Paket, masa sewa, keanggotaan/penggantian penghuni, penanggung jawab, perpanjangan dan konfirmasi keluar | UC-04 |
| KF-04 | Tagihan pertama, tagihan periode berikutnya sejak H−3 dan pencegahan duplikasi | UC-05 |
| KF-05 | Pembayaran/cicilan Cash, Transfer, QRIS dan pembatalan catatan salah | UC-05 |
| KF-06 | Pengeluaran operasional, koreksi dan pembatalan beralasan | UC-06 |
| KF-07 | Laporan kas operasional | UC-08 |
| KF-08 | Login, logout, ganti password dan perlindungan akses | UC-01 |
| KF-09 | Dashboard, piutang, tunggakan dan pengingat H−3 | UC-07 |
| KF-10 | Pratinjau serta pembukaan pesan WhatsApp | UC-09 |
| KF-11 | Formulir data awal per periode, pemeriksaan rekap dan finalisasi | UC-10 |
| KF-12 | Registrasi awal akun pengelola | UC-11 |

Paket dua orang memperluas KF-02/KF-03/KF-11 dan tampilan terkait; tidak menambah portal, jenis pengguna atau tagihan individual.

### 3.2 Di luar ruang lingkup

- Akun penghuni, registrasi publik, banyak kos dan pengelola dengan tingkat hak akses berbeda.
- PIN sebagai pengganti password.
- Payment gateway, pendeteksian transfer otomatis dan validasi otomatis bukti pembayaran.
- Pengiriman WA otomatis, API pesan, bot balasan, status terkirim/dibaca dan log pengiriman.
- Pengaturan template pesan melalui menu khusus.
- Impor/ekspor Excel/CSV, booking, deposit, denda otomatis, prorata, kelebihan bayar dan refund.
- Pemisahan tagihan kamar dua orang menjadi utang individual atau pembagian harga otomatis per orang.
- Rekonstruksi seluruh transaksi kas sebelum tanggal mulai pencatatan.
- Penambahan fitur baru setelah pekan 14; perbaikan kesalahan tetap dilakukan.

Ruang lingkup kebutuhan produk dibekukan pada versi ini. Detail teknis boleh ditetapkan pada dokumen arsitektur selama tidak mengubah perilaku produk, ruang lingkup atau kriteria penerimaan. Validasi eksternal yang belum tersedia dicatat pada bagian 14.

## 4. Istilah dan data produk

| Istilah | Definisi |
| --- | --- |
| Jenis hunian | Paket untuk satu orang atau dua orang dalam satu kamar |
| Periode paket | Interval tagihan 1, 6 atau 12 bulan kalender |
| Masa sewa | Kesepakatan memakai satu kamar untuk rentang tertentu; dapat mencakup beberapa periode paket penuh |
| Penghunian | Hubungan satu orang dengan suatu masa sewa, termasuk tanggal masuk, keadaan tinggal dan tanggal keluar sendiri |
| Penanggung jawab | Satu kontak administratif yang dipilih dari penghuni kontrak; riwayat pergantiannya dipertahankan |
| Tagihan | Kewajiban untuk satu periode paket pada satu masa sewa/kamar |
| Pembayaran | Satu penerimaan uang baru yang dialokasikan ke satu atau beberapa tagihan dalam masa sewa yang sama, setelah diverifikasi pengelola |
| Saldo pembayaran lama | Total yang telah dibayar sebelum aplikasi mulai mencatat operasional; bukan pemasukan baru |
| Piutang | Sisa tagihan aktif yang belum lunas, termasuk yang belum jatuh tempo |
| Tunggakan | Sisa tagihan aktif yang tanggal jatuh temponya sudah dilewati |
| Persiapan | Mode memasukkan dan meninjau data awal; transaksi operasional belum dibuka |
| Aktif | Mode setelah finalisasi; transaksi operasional dibuka dan saldo awal dikunci |
| Konfirmasi hunian | Tindakan memastikan penghuni sudah keluar atau tetap tinggal melalui kontrak lanjutan yang sah |

### 4.1 Data minimum yang harus dapat direpresentasikan

| Data | Informasi inti |
| --- | --- |
| Pengelola | Username dan hash password; rincian kode penyiapan tidak dipublikasikan |
| Konfigurasi kos | Nama kos, tanggal mulai pencatatan, mode Persiapan/Aktif |
| Kamar | Nomor unik, tipe, dukungan hunian satu/dua orang, harga referensi, status turunan |
| Penghuni | Nama, identitas sesuai catatan mitra dan nomor WA; foto KTP tidak diwajibkan pada versi ini |
| Paket | Jenis hunian 1/2 orang, periode 1/6/12 bulan dan status aktif |
| Masa sewa | Kamar, paket, tanggal mulai/akhir, harga total per periode yang disepakati, sumber data dan penanggung jawab |
| Penghunian | Penghuni, masa sewa, tanggal masuk, keadaan masih tinggal/keluar/dilanjutkan, tanggal keluar jika diketahui |
| Tagihan | Masa sewa, periode, jatuh tempo, nominal, asal data, saldo pembayaran lama, pencatatan Aktif/Batal dan alasan pembatalan |
| Pembayaran | Masa sewa, total penerimaan, tanggal uang diterima, waktu pencatatan otomatis yang tidak dapat diedit, nominal, metode, bukti/referensi opsional, status Valid/Batal, alasan dan waktu pembatalan |
| Alokasi pembayaran | Pembayaran, tagihan dan nominal bagian penerimaan; satu baris per pasangan pembayaran/tagihan |
| Pengeluaran | Tanggal, nominal, kategori, keterangan, bukti opsional, status Valid/Batal dan riwayat koreksi beralasan dengan nilai lama/baru serta waktu server |

Ini adalah kebutuhan data produk, bukan skema tabel final. Pembagian tabel, tipe teknis, indeks, migrasi dan implementasi riwayat ditetapkan di `database.md` dan `architecture.md`.

## 5. Aturan bisnis

### 5.1 Paket dan harga

**BR-01.** Ada enam kombinasi: satu orang × 1/6/12 bulan dan dua orang × 1/6/12 bulan.

**BR-02.** Harga selalu merupakan total satu kamar untuk satu periode paket. Harga paket dua orang tidak otomatis dua kali harga satu orang. Harga 6/12 bulan tidak otomatis hasil perkalian tarif bulanan.

**BR-03.** Tarif riil harus diberikan mitra. Pada pembuatan kontrak, pengelola memilih kombinasi paket dan memasukkan harga kesepakatan. Versi pertama tidak memerlukan menu pengelolaan matriks tarif yang terpisah. Harga referensi kamar tidak boleh diam-diam menggantikan harga kontrak.

**BR-04.** Harga sudah termasuk air, listrik dan Wi-Fi. Tidak dibuat tagihan tambahan penghuni untuk ketiga fasilitas tersebut. Pembayaran biayanya oleh pengelola masuk pengeluaran operasional.

**BR-05.** Jenis hunian, periode paket dan harga kesepakatan disimpan sebagai snapshot kontrak. Perubahan tarif/paket berikutnya tidak mengubah kontrak atau tagihan lama.

### 5.2 Dua penghuni dan penanggung jawab

**BR-06.** Kontrak baru paket satu orang dimulai dengan satu nama; paket dua orang dengan dua nama berbeda. Nama awal harus berbeda; satu orang tidak boleh memiliki dua penghunian yang bertumpuk pada kontrak yang sama. Kamar harus mendukung jenis hunian yang dipilih.

**BR-07.** Selalu ada satu penanggung jawab administratif untuk kontrak yang masih dihuni. Pada awal paket dua orang, pengelola memilih salah satu dari kedua penghuni.

**BR-08.** Setiap orang mempunyai catatan masuk dan keluar sendiri. Keluar satu orang tidak mengakhiri seluruh kontrak, tidak mengubah paket/harga secara otomatis dan tidak membatalkan tagihan. Identitas serta riwayatnya tidak dihapus.

**BR-09.** Jika penanggung jawab keluar dan masih ada penghuni, pengelola harus menunjuk penghuni yang masih tinggal sebagai penanggung jawab berikutnya dalam tindakan simpan yang sama. Nama lama, nama baru, waktu dan alasan pergantian tetap dapat ditelusuri. Tagihan tidak dipecah atau dihapus karena pergantian ini.

**BR-10.** Saat kedua penghuni keluar, pengelola menyelesaikan pengakhiran sewa dan konfirmasi hunian dengan validasi tagihan. Kontak terakhir tetap tersedia untuk tindak lanjut piutang; tidak dibuat penanggung jawab aktif fiktif.

**BR-11.** Paket dua orang yang tinggal dihuni satu orang tetap memakai harga kesepakatan sampai ada kesepakatan baru pada batas periode. Perubahan menjadi paket satu orang memakai kontrak baru setelah kontrak lama diselesaikan pada batas periode yang sah; tidak berlaku surut dan tidak menghapus tagihan yang sudah menjadi kewajiban.

**BR-12.** Penghuni pengganti pada paket dua orang boleh masuk sebelum kontrak berakhir setelah pengelola memverifikasi penghuni lama sudah keluar. Tanggal masuk baru tidak sebelum keluarnya orang yang digantikan, tidak di masa depan, dan berada dalam rentang kontrak. Penghunian orang baru tidak boleh bertumpuk dengan penghunian lain; maksimal dua orang tinggal bersamaan, sesuai dukungan kamar. Catatan lama tidak ditimpa: tambahkan hubungan penghunian baru dengan tanggal masuknya. Riwayat kontrak dapat memuat lebih dari dua nama, tetapi bukan lebih dari dua penghuni bersamaan. Harga, akhir kontrak dan tagihan kamar tidak berubah; tunggakan lama tidak otomatis dialihkan atau dibagi kepada pendatang. Jika penanggung jawab masih tinggal, kontak tetap; perubahan kontak memerlukan pemilihan dari penghuni yang masih tinggal dan riwayat pergantian. Seluruh perubahan disimpan atomik. Jika semua penghuni sudah keluar atau kontrak telah berakhir, gunakan alur penutupan dan kontrak baru, bukan menghidupkan kontrak lama.

### 5.3 Masa sewa dan keberadaan penghuni

**BR-13.** Rentang kontrak memakai mulai inklusif dan akhir eksklusif. Contoh: mulai 10 Oktober dan akhir 10 November berarti periode tinggal sampai sebelum 10 November. Pesan harus membedakan batas akhir kontrak dari hari terakhir periode.

**BR-14.** Kontrak baru operasional dimulai pada atau setelah tanggal mulai pencatatan. Kontrak lama dimasukkan lewat inisialisasi. Kontrak kamar tidak boleh bertumpuk. Benturan orang diperiksa terhadap rentang penghunian masing-masing, termasuk penanggung jawab dan pendamping. Orang yang sudah dikonfirmasi keluar dapat memulai penghunian baru sejak batas keluar tersebut; kontrak bersama yang masih berjalan untuk orang lain tidak menahan orang yang telah keluar. Hunian yang belum ditutup tetap menghalangi penempatan orang itu di kontrak lain.

**BR-15.** Perpanjangan sebelum berakhir menambah sejumlah periode paket penuh dengan harga/paket sama, setelah memeriksa benturan. Perubahan paket/harga atau permintaan setelah kontrak berakhir memakai kontrak baru; tanggal tidak otomatis dimundurkan. Jeda tinggal yang belum tercatat diklarifikasi dengan mitra.

**BR-16.** Kontrak berakhir tidak membuktikan kamar sudah kosong. Penghuni yang belum dikonfirmasi keluar tetap menahan penempatan orang lain. Piutang, status kontrak dan keadaan hunian adalah tiga hal berbeda.

**BR-17.** Kontrak lanjutan untuk orang/kamar yang sama dapat menutup penghunian lama sebagai dilanjutkan, tanpa membuat tanggal keluar fisik fiktif. Penyimpanan lanjutan dan penutupan hubungan lama harus berhasil bersama atau dibatalkan bersama.

**BR-18.** Konfirmasi keluar mencatat orang yang keluar dan tanggal sebenarnya, tidak di masa depan. Tanggal keluar dapat sesudah akhir kontrak; hal ini tidak otomatis membuat tagihan atau memperpanjang kontrak. Pada migrasi, keadaan sudah keluar yang telah diverifikasi boleh dicatat tanpa mengarang tanggal yang tidak diketahui.

### 5.4 Periode dan pembentukan tagihan

**BR-19.** Satu masa sewa memiliki satu tagihan kamar per periode, termasuk paket dua orang. Tagihan pertama dibuat bersama kontrak baru. Harga tagihan operasional adalah snapshot harga total per periode, bukan dikalikan jumlah penghuni.

**BR-20.** Tagihan berikutnya dibuat atau dilengkapi ketika dashboard/tagihan dibuka, sejak tiga hari kalender sebelum periode dimulai. Proses juga melengkapi periode operasional terdahulu yang terlewat. Tidak ada kewajiban menjalankan penjadwal latar belakang pada versi tombol WA ini.

**BR-21.** Awal periode baru harus masih berada dalam masa sewa efektif. Kontrak yang hanya sampai 10 April tidak menghasilkan tagihan periode mulai 10 April kecuali kontraknya sudah diperpanjang. H−3 akhir sewa tetap dapat ditampilkan tanpa membuat tagihan kontrak baru.

**BR-22.** Batas periode dihitung dari tanggal mulai asli ditambah kelipatan 1/6/12 bulan kalender. Jika hari tidak tersedia, gunakan hari terakhir bulan; pada bulan yang mendukung, kembali ke hari asal. Satu bulan bukan selalu 30 hari.

**BR-23.** Jatuh tempo operasional adalah awal periode tagihan. Pembayaran H−3 boleh diterima untuk tagihan yang sudah tersedia. Tidak ada jadwal jatuh tempo per cicilan tersendiri.

**BR-24.** Pasangan masa sewa dan awal periode wajib unik. Pembukaan menu berulang tidak membentuk ulang tagihan. Periode sebelum batas pencatatan memakai data awal yang diverifikasi, bukan dibentuk ulang otomatis.

**BR-25.** Jika semua penghuni keluar lebih awal, tagihan untuk periode yang sudah dimulai tetap tersimpan tanpa prorata/refund. Tagihan H−3 untuk periode yang belum dimulai dan belum menerima pembayaran dapat dibatalkan beralasan. Jika sudah ada penerimaan pada periode yang dipotong, pengakhiran ditolak dan pengelola diminta menyelesaikan kesepakatan di luar alur refund yang belum didukung. Keluar satu orang sementara orang lain tetap tinggal tidak memicu pembatalan ini.

### 5.5 Pembayaran, saldo dan status

**BR-26.** Pengelola memastikan uang diterima sebelum mencatatnya. Metode wajib salah satu Cash, Transfer atau QRIS. Bukti bukan konfirmasi otomatis dan tidak menggantikan pemeriksaan penerimaan uang.

**BR-27.** Pembayaran harus untuk tagihan dengan pencatatan Aktif dan memiliki sisa. Nominal harus `0 < nominal <= sisa`. Tanggal bayar adalah tanggal uang benar-benar diterima, diisi pengelola; tidak boleh di masa depan atau sebelum batas pencatatan. Waktu pencatatan direkam otomatis dari waktu server, ditampilkan sesuai Asia/Makassar dan tidak dapat diubah pengelola. Uang diterima tanggal 10 tetapi dicatat tanggal 12 tetap memakai tanggal bayar 10 dan waktu pencatatan 12. Waktu pembuatan catatan tagihan bukan batas bawah tanggal penerimaan jika tagihan untuk periode sah baru dilengkapi ketika aplikasi dibuka. Jendela pembentukan tagihan berikutnya tetap H−3; pembayaran untuk periode berikutnya tidak dimundurkan ke sebelum ketersediaan logis periode tersebut. Pemisahan tanggal penerimaan dan waktu catat tidak membuka refund, pembayaran sebelum batas pencatatan atau periode di luar kontrak. Jika tanggal bayar salah, batalkan catatan beralasan dan catat ulang; waktu catat asli tetap tersimpan.

**BR-28.** Setiap cicilan dapat memakai metode berbeda. Versi pertama tidak membagi tagihan dua orang menjadi subtagihan per nama. Satu penerimaan dapat dialokasikan manual ke satu atau beberapa tagihan Aktif pada masa sewa yang sama. Jumlah alokasi harus tepat sama dengan total uang diterima; setiap bagian positif dan tidak melebihi sisa tagihannya. Tidak ada alokasi ke kontrak lain atau pembagian otomatis ke nama penghuni. Satu pembayaran induk menyimpan tanggal penerimaan, metode dan bukti; rincian alokasi menghubungkannya ke tagihan. Saldo memakai alokasi Valid, laporan kas menghitung pembayaran induk sekali. Seluruh alokasi disimpan atomik dan idempoten, termasuk pemeriksaan saldo saat bersamaan. Pembatalan membatalkan seluruh penerimaan beserta alokasinya; jika pembagiannya salah, batalkan beralasan lalu catat ulang tanpa menghapus riwayat.

**BR-29.** Rumus saldo untuk tagihan Aktif:

```text
totalDibayar = dibayarSebelumSistem + jumlah alokasi dari pembayaran Valid baru
sisa = nominalTagihan - totalDibayar
```

`dibayarSebelumSistem` hanya diisi untuk tagihan data awal dan bernilai nol untuk tagihan operasional baru.

**BR-30.** Urutan penentuan status:

| Kondisi | Status |
| --- | --- |
| Pencatatan tagihan dibatalkan | Dibatalkan; tidak menjadi piutang atau sasaran pembayaran/pengingat |
| Sisa = 0 | Lunas |
| Sisa > 0 dan hari ini > jatuh tempo | Menunggak, termasuk jika sudah mencicil |
| Sisa > 0, belum lewat jatuh tempo, totalDibayar > 0 | Dibayar sebagian |
| Sisa > 0, belum lewat jatuh tempo, totalDibayar = 0 | Belum dibayar |

Hari jatuh tempo belum dianggap lewat. Denda dan pergeseran jatuh tempo otomatis tidak disediakan. Status dihitung dengan tanggal acuan Asia/Makassar, bukan nilai status lama yang dibiarkan tersimpan tanpa diperbarui.

**BR-31.** Pembayaran salah dibatalkan dengan alasan dan dicatat ulang jika perlu. Catatan asal tidak dihapus. Catatan Batal tidak dihitung sebagai pelunasan atau pemasukan; pembatalan bukan pengembalian uang. Pembatalan dapat mengubah tagihan Lunas menjadi sebagian atau Menunggak sesuai tanggal dan sisa terbaru.

**BR-32.** Pelunasan utang setelah kontrak berakhir tetap diperbolehkan. Pelunasan tidak membuka kontrak lagi, mengubah paket atau menganggap penghuni masuk kembali.

**BR-33.** Pengiriman ulang permintaan simpan yang sama tidak boleh menambah catatan. Dua permintaan berbeda yang bersamaan tidak boleh membuat total melebihi nominal tagihan. Kegagalan simpan tidak boleh meninggalkan saldo berubah tanpa transaksi yang lengkap.

### 5.6 Inisialisasi data lama

**BR-34.** Pilih satu tanggal mulai pencatatan sebelum mengisi data awal. Catatan mitra tersedia sebagai tagihan dan pembayaran per periode. Formulir berulang memuat kamar, jenis paket, daftar penghunian dengan batas satu/dua orang tinggal bersamaan, penanggung jawab, keadaan tinggal masing-masing, kontrak, tagihan berjalan dan seluruh tunggakan.

**BR-35.** Setiap baris tagihan memuat periode, jatuh tempo asli, nominal asli dan total dibayar sebelum tanggal mulai pencatatan. Sisa dihitung aplikasi. Angka yang tidak diketahui harus diklarifikasi, bukan diisi fiktif agar lolos validasi.

**BR-36.** Tagihan periode berjalan yang sudah lunas tetap dimasukkan untuk mencegah penagihan ulang. Periode lama yang sudah lunas tidak wajib dimigrasikan seluruhnya. Data penghuni yang sudah keluar tetapi berutang tetap boleh dimasukkan bersama kontrak lamanya.

**BR-37.** Data awal menyimpan rekap pembayaran sebelum sistem per tagihan, bukan menciptakan seluruh transaksi historis. Tidak diminta metode/tanggal pembayaran lama yang tidak diketahui. Pada paket dua orang, sisa tetap saldo tagihan kamar, bukan saldo masing-masing orang.

**BR-38.** Dalam mode Persiapan, pembayaran/pengeluaran operasional belum dibuka. Transaksi nyata sejak tanggal batas dicatat di catatan pendamping untuk dimasukkan setelah finalisasi dengan tanggal penerimaan sebenarnya. Transaksi tersebut tidak boleh dimasukkan lagi sebagai pembayaran sebelum sistem.

**BR-39.** Finalisasi memerlukan rekap penghuni/hunian, kontrak, tagihan dan total piutang yang cocok dengan catatan mitra. Pengelola menyatakan periode lama lain sudah diselesaikan. Finalisasi ditolak jika data tidak valid. Mode, tanggal batas dan saldo awal dikunci setelah finalisasi; koreksi kemudian melalui prosedur pemeliharaan dengan backup dan verifikasi mitra, bukan edit bebas.

### 5.7 Pengeluaran dan laporan

**BR-40.** Pengeluaran memiliki nominal positif, tanggal tidak di masa depan dan tidak sebelum batas pencatatan, kategori, keterangan serta bukti opsional. Kategori: Listrik, Air, Internet/Wi-Fi, Perbaikan, Gaji dan Lainnya. Pengelola boleh mengoreksi tanggal, nominal, kategori, keterangan atau lampiran dengan alasan wajib. Nilai sebelum/sesudah, pelaku dan waktu server dipertahankan; validasi yang sama berlaku saat koreksi. Tidak ada hapus permanen melalui aplikasi. Catatan duplikat atau transaksi yang sebenarnya tidak terjadi dibatalkan beralasan, bukan diubah menjadi nominal nol; catatan Batal dikecualikan dari laporan. Pembatalan ini merupakan koreksi pencatatan, bukan transaksi uang kembali. Laporan mengikuti pengeluaran Valid terbaru berdasarkan tanggal pengeluaran; perubahan tanggal dapat memindahkan pengeluaran antarrentang laporan. Koreksi beserta riwayat harus disimpan atomik; jika gagal, catatan dan rekap tetap seperti sebelumnya.

**BR-41.** Pemasukan laporan adalah jumlah total penerimaan induk pembayaran Valid baru, masing-masing dihitung tepat sekali tanpa dikalikan jumlah alokasinya, berdasarkan tanggal uang diterima, bukan waktu pencatatan. Pengeluaran hanya menghitung catatan Valid berdasarkan tanggal pengeluaran. Kedua batas rentang termasuk. Tagihan belum dibayar adalah piutang, bukan kas; saldo pembayaran sebelum sistem bukan kas baru. Laporan ini rekap kas, bukan laporan laba akrual. Pencatatan terlambat dapat memperbarui rekap tanggal penerimaan terdahulu; laporan selalu memakai catatan valid terbaru dan bukan snapshot laporan historis yang dibekukan.

**BR-42.** Rentang terbalik dan rentang sebelum batas pencatatan ditolak dengan penjelasan. Data kosong menghasilkan nol. Ringkasan bulan pertama memakai batas yang lebih akhir antara awal bulan dan tanggal mulai pencatatan, dengan label batas tersebut.

**BR-43.** Pembatalan catatan salah membuat laporan menghitung ulang berdasarkan data valid terbaru pada tanggal transaksi asal. Aplikasi tidak membuat transaksi refund atau pembalikan kas baru pada hari pembatalan.

### 5.8 Pengingat dan WhatsApp

**BR-44.** Daftar pengingat dihitung saat dashboard/tagihan dibuka. Pengingat pembayaran tampil sejak H−3 jatuh tempo jika ada sisa, tetap terlihat saat jatuh tempo dan berubah menjadi tunggakan setelah lewat. Setelah lunas, pengingat pembayaran berhenti.

**BR-45.** Pengingat akhir sewa tampil sejak H−3 akhir kontrak, termasuk jika tagihan sudah lunas. Setelah kontrak berakhir dan penghuni belum keluar, tampil sebagai perlu tindak lanjut hunian. Perpanjangan mengubah tanggal acuan. Jika dua konteks jatuh pada hari sama, pratinjau dapat menggabungkannya tanpa menagih kontrak baru yang belum disepakati.

**BR-46.** Tombol komunikasi umum tersedia pada detail penghuni. Pesan tagihan, pembayaran dan akhir sewa mengikuti penanggung jawab administratif kontrak. Nomor kosong/invalid menonaktifkan aksi dengan alasan. Nomor lokal dinormalisasi ke format internasional dan data dibaca ulang sebelum pratinjau dibuka. Pengelola memastikan penerima bersedia dihubungi.

**BR-47.** Setiap pembayaran Valid baru menyediakan konfirmasi. Pembayaran pertama pada setiap tagihan menyertakan ringkasan masa sewa, jenis hunian dan periode tagihan. Cicilan berikutnya tetap menyediakan konfirmasi nominal serta sisa terbaru. Pembayaran Batal tidak boleh diberi konfirmasi seolah masih valid.

**BR-48.** Pengelola meninjau pratinjau, memilih Buka WhatsApp, lalu mengedit atau menekan Kirim di WhatsApp. Membuka percakapan tidak mengubah status keuangan dan tidak menjadi bukti pesan terkirim. Kegagalan membuka WA tidak membatalkan pembayaran yang sudah tersimpan. Bukti pembayaran serta nomor identitas sensitif tidak dimasukkan ke tautan.

**BR-49.** Jika kedua penghuni sudah keluar, kontak terakhir kontrak tetap dapat dipakai untuk tindak lanjut piutang setelah ditinjau pengelola. Aplikasi tidak membuat status penghuni aktif palsu agar tombol penagihan tersedia.

## 6. Alur pengguna utama

### F-01 Penyiapan pertama

Prasyarat: akses penyiapan tersedia dan akun pengelola belum ada.

1. Pengelola mengisi kode penyiapan, username, password dan konfirmasi.
2. Sistem memvalidasi lalu membuat akun tunggal; registrasi berikutnya ditutup.
3. Pengelola login dan menetapkan tanggal mulai pencatatan.
4. Pengelola mengisi kamar, penghuni, keanggotaan satu/dua orang, kontrak dan baris tagihan lama.
5. Sistem menampilkan kesalahan per isian; simpan satu berkas tidak menghasilkan data parsial.
6. Pengelola membandingkan rekap dengan catatan mitra lalu memfinalisasi.
7. Sistem membuka mode Aktif. Pengulangan finalisasi tidak mereset tanggal atau saldo awal.

### F-02 Penghuni dan kontrak baru

Prasyarat: mode Aktif; kamar mendukung paket dan tidak tertahan hunian sebelumnya.

1. Pilih kamar dan penghuni: satu nama untuk paket satu orang atau dua nama berbeda untuk paket dua orang.
2. Pilih penanggung jawab, periode 1/6/12 bulan, tanggal serta harga total kamar per periode.
3. Sistem memvalidasi kapasitas, benturan kamar/orang, periode dan nominal.
4. Simpan kontrak, hubungan penghuni, snapshot kesepakatan dan tagihan pertama sebagai satu kesatuan.
5. Tampilkan ringkasan; mencatat kontrak tidak menyatakan pembayaran sudah diterima.

### F-03 Pembayaran dan konfirmasi

1. Buka tagihan dan periksa sisa.
2. Pengelola memastikan uang diterima di luar aplikasi.
3. Isi tanggal uang diterima, nominal, metode serta bukti/referensi opsional. Jika baru dicatat beberapa hari kemudian, gunakan tanggal penerimaan sebenarnya; aplikasi merekam waktu input secara otomatis.
4. Jika uang melunasi beberapa periode, pilih tagihan dalam masa sewa yang sama dan isi nominal bagian masing-masing. Sistem memeriksa total alokasi tepat sama dengan penerimaan, lalu menyimpan pembayaran beserta semua alokasi sekaligus; jika satu bagian gagal, seluruh saldo tetap.
5. Tampilkan tanggal bayar, waktu pencatatan, sisa/status terbaru dan tombol konfirmasi WA. Pelunasan penuh menghasilkan Lunas, sedangkan sisa positif setelah jatuh tempo tetap Menunggak walaupun cicilan pertama diterima tepat waktu. Pesan untuk beberapa tagihan merinci alokasi per periode, total penerimaan dan sisa terbaru masing-masing, tanpa menghitung penerimaan berulang. Membuka WA adalah tindakan pilihan, bukan bagian wajib transaksi simpan.

### F-04 Salah satu penghuni keluar

1. Pilih nama yang benar pada kontrak dua orang, bukan langsung memilih kamar kosong.
2. Catat tanggal keluar. Jika orang tersebut penanggung jawab, pilih orang yang masih tinggal sebagai penerus kontak.
3. Sistem menyimpan perubahan orang dan penanggung jawab bersama; identitas/riwayat lama tetap ada.
4. Paket, harga, tagihan dan utang tetap; kamar masih Dihuni selama kontrak berlaku dan masih ada penghuni.
5. Jika kontraknya sudah berakhir dan penghuni lain masih tinggal, kamar Perlu konfirmasi dan kontrak harus ditindaklanjuti.

### F-04A Penghuni pengganti pada kontrak dua orang

Prasyarat: kontrak paket dua orang belum berakhir, masih ada penghuni yang tinggal, dan penghuni yang digantikan sudah dicatat keluar.

1. Buka kontrak, periksa riwayat keluar dan kapasitas pada tanggal masuk baru.
2. Pilih data orang baru atau buat data penghuni; isi tanggal masuk sebenarnya.
3. Sistem memeriksa maksimal dua orang bersamaan, benturan orang, rentang kontrak dan tidak adanya penghunian ganda.
4. Penanggung jawab yang masih tinggal tetap digunakan. Jika pengelola memilih perubahan kontak, pilih penghuni yang masih tinggal dan simpan riwayat pergantiannya.
5. Simpan hubungan orang baru tanpa menimpa nama/tanggal keluar orang lama.
6. Tampilkan penghuni terkini dan riwayat. Harga, akhir kontrak, tagihan serta sisa utang tetap; tidak ada pembagian utang otomatis kepada pendatang.
7. Jika validasi atau penyimpanan gagal, tidak ada perubahan sebagian. Permintaan yang sama dikirim ulang tidak menambah hubungan ganda.

### F-05 Seluruh penghuni keluar atau meneruskan sewa

- Keluar: pastikan semua orang tercatat keluar, validasi pengakhiran/tagihan, lalu konfirmasi hunian ditutup. Piutang tetap tersedia.
- Perpanjang kontrak sama: periksa periode penuh, harga/paket tetap dan tidak ada benturan; hubungan orang yang masih tinggal dilanjutkan tanpa membuat keluar fiktif.
- Paket/harga berubah: buat kontrak lanjutan pada batas periode yang sah; simpan bersama penutupan hubungan lama. Penghuni yang sudah keluar tidak otomatis dimasukkan kembali.

### F-06 Pemantauan dan laporan

1. Buka dashboard; sistem melengkapi tagihan yang memenuhi jendela H−3.
2. Periksa pembayaran mendekati tempo, tunggakan, akhir sewa dan hunian perlu konfirmasi.
3. Tindak lanjuti melalui detail data atau pesan WA.
4. Catat pengeluaran saat ada biaya operasional.
5. Pilih rentang laporan yang valid, lihat pemasukan, pengeluaran, selisih kas serta rincian transaksi.

## 7. Status yang ditampilkan

| Objek | Status | Makna |
| --- | --- | --- |
| Aplikasi | Persiapan / Aktif | Data awal belum atau sudah difinalisasi |
| Kontrak | Belum mulai / Aktif / Berakhir | Mengikuti tanggal dan pengakhiran; tidak mengikuti pelunasan |
| Penghunian orang | Masih tinggal / Keluar / Dilanjutkan | Mengikuti keadaan setiap orang, bukan status tagihannya |
| Kamar | Kosong | Tidak ada hunian yang belum ditutup atau kontrak aktif yang menahan kamar; kontrak terjadwal tetap diperiksa saat memilih rentang baru |
| Kamar | Dihuni | Kontrak berlaku dan masih ada penghuni yang tinggal |
| Kamar | Perlu konfirmasi | Kontrak habis tetapi masih ada hunian yang belum ditutup; penempatan orang lain ditahan |
| Tagihan | Belum dibayar / Dibayar sebagian / Menunggak / Lunas / Dibatalkan | Mengikuti BR-30 |
| Pembayaran | Valid / Batal | Menentukan apakah nominal dihitung |
| Pesan WA | Tidak ada status pengiriman | Aplikasi hanya menyiapkan teks dan membuka percakapan |

Hitungan penghuni aktif harus mendefinisikan keadaan secara jelas: daftar orang yang masih tinggal dipisahkan dari kontrak aktif dan orang yang kontraknya habis namun masih berada di kamar. Orang yang dilanjutkan ke kontrak baru tidak dihitung dua kali.

## 8. Kriteria penerimaan

Semua AC di bawah merupakan rancangan pengujian, belum hasil aktual. Kasus pada keputusan terbuka baru difinalisasi setelah keputusan tersebut ditutup.

| ID | Acuan | Kondisi dan hasil yang harus dipenuhi |
| --- | --- | --- |
| AC-01 | KF-12, UC-11 | Kode penyiapan benar, akun belum ada dan password/konfirmasi valid: satu akun dibuat lalu registrasi ditutup. Kode salah atau akun sudah ada: tidak membuat akun. Dua pendaftaran bersamaan tidak membuat dua akun. |
| AC-02 | KF-08, UC-01 | Login sah membuat sesi; login salah/kosong ditolak. Percobaan dibatasi. Setelah logout atau tanpa sesi, halaman data, endpoint dan lampiran tidak dapat diakses. |
| AC-03 | KF-08, UC-01 | Ganti password meminta password lama; input salah tidak mengubah kredensial. Lupa password tidak membuka registrasi publik. |
| AC-04 | KF-01, UC-02 | Nomor kamar ganda dan harga tidak positif ditolak. Kamar bersejarah tidak dapat dihapus. Harga/fasilitas ditampilkan sebagai total termasuk air, listrik, Wi-Fi. |
| AC-05 | KF-02, UC-03 | Nama/identitas wajib divalidasi. Nomor WA kosong/invalid tidak menghapus penghuni atau menghalangi pencatatan lain, tetapi aksi WA menunjukkan alasan tidak tersedia. |
| AC-06 | KF-03, UC-04 | Enam kombinasi jenis hunian/periode dapat dipilih. Harga dua orang tidak dihitung otomatis dua kali harga satu orang. Harga 6/12 bulan bukan perkalian otomatis. |
| AC-07 | KF-03, UC-04 | Paket satu orang menerima satu nama. Paket dua orang memerlukan dua nama berbeda dan satu penanggung jawab dari kedua nama itu. Paket melebihi dukungan kamar atau orang duplikat ditolak. |
| AC-08 | KF-03, UC-04 | Kontrak baru menyimpan kesepakatan dan satu tagihan pertama. Gagal di salah satu penyimpanan membatalkan seluruh perubahan. |
| AC-09 | KF-03, UC-04 | Benturan kontrak kamar atau benturan orang, termasuk pendamping, ditolak. Hunian lama yang belum ditutup menahan penempatan penghuni berbeda walau kontrak sudah habis. |
| AC-10 | KF-03, UC-04 | Pada paket dua orang, satu orang keluar: tanggal keluar hanya milik orang itu, jumlah tinggal turun menjadi satu, harga/tagihan tetap, nama lama tetap di riwayat. |
| AC-11 | KF-03, UC-04 | Penanggung jawab keluar sementara orang kedua tinggal: simpan meminta penerus yang valid. Pergantian tercatat dan pesan berikutnya memakai kontak baru; tagihan lama tidak dihapus/dipecah. |
| AC-12 | KF-03, UC-04 | Kontrak habis dan masih ada orang yang belum keluar: kamar Perlu konfirmasi. Pelunasan utang tidak mengubah status kamar menjadi Kosong. |
| AC-13 | KF-03, UC-04 | Setelah semua orang keluar dan hunian ditutup, kamar dapat menjadi Kosong tanpa menghapus utang. Menutup hanya satu dari dua orang tidak membuat kamar Kosong. |
| AC-14 | KF-03, UC-04 | Perpanjangan sah menambah periode penuh dan tidak menghidupkan kembali hubungan orang yang sudah keluar. Paket/harga baru tidak mengubah riwayat lama. |
| AC-15 | KF-04, UC-05 | Kontrak enam bulanan mulai 10 Oktober 2026 sampai 10 Oktober 2027: tagihan periode 10 April 2027 tersedia saat menu dibuka 7 April; pada 6 April belum dibentuk. Pembukaan berulang tetap satu tagihan periode. |
| AC-16 | KF-04, UC-05 | Kontrak hanya sampai 10 April tanpa perpanjangan: tidak ada tagihan periode mulai 10 April, meskipun pengingat akhir sewa tampil pada 7 April. |
| AC-17 | KF-04, UC-05 | Mulai 31 Januari 2027 dengan periode bulanan menghasilkan batas 28 Februari lalu 31 Maret. Tahun kabisat memakai 29 Februari. |
| AC-18 | KF-04/05, UC-04/05 | Seluruh penghuni mengakhiri sebelum periode H−3 dimulai: tagihan mendatang tanpa pembayaran dibatalkan beralasan; tagihan mendatang yang sudah menerima pembayaran menghalangi pengakhiran yang memotongnya. Keluar satu orang saja tidak membatalkannya. |
| AC-19 | KF-05, UC-05 | Sisa Rp500.000 dibayar Transfer Rp200.000: tepat satu pembayaran tersimpan, sisa Rp300.000 dan kas baru Rp200.000 pada tanggal penerimaan. |
| AC-20 | KF-05, UC-05 | Nominal nol, negatif, di atas sisa, metode kosong/di luar pilihan, tanggal masa depan atau tagihan Batal ditolak tanpa perubahan saldo. |
| AC-21 | KF-05, UC-05 | Tagihan jatuh tempo 10 Oktober dengan pembayaran sebagian: tanggal 10 masih Dibayar sebagian, tanggal 11 menjadi Menunggak. Sisa nol selalu Lunas untuk tagihan Aktif. |
| AC-22 | KF-05, UC-05 | Simpan ulang permintaan yang sama tidak menambah pembayaran; permintaan berbeda bersamaan tidak menghasilkan kelebihan bayar. Gagal simpan tidak meninggalkan data parsial. |
| AC-23 | KF-05/07, UC-05/08 | Pembayaran dibatalkan beralasan: catatan asal tetap ada, sisa dihitung ulang, nominalnya tidak dihitung dalam kas, dan status mengikuti tanggal acuan terbaru. |
| AC-24 | KF-05, UC-05 | Kontrak sudah Berakhir, tagihan masih berutang: pelunasan diterima, tagihan Lunas, kontrak tetap Berakhir dan hunian tidak dibuka kembali. |
| AC-25 | KF-11, UC-10 | Tagihan lama Rp900.000, dibayar sebelum sistem Rp400.000: sisa awal Rp500.000 dan kas baru nol. Pembayaran baru Rp200.000 menyisakan Rp300.000 dan kas bertambah Rp200.000. |
| AC-26 | KF-11, UC-10 | Data awal dua orang dapat memuat satu sudah keluar dan satu masih tinggal; saldo tagihan kamar tetap satu. Tagihan berjalan lunas tidak dibentuk ulang setelah finalisasi. |
| AC-27 | KF-11, UC-10 | Saldo lama negatif/melebihi nominal, periode ganda, benturan orang/kamar atau data wajib belum lengkap menolak finalisasi. Simpan ulang berkas tidak menggandakan data. |
| AC-28 | KF-11, UC-10 | Finalisasi sah membuka mode Aktif dan mengunci saldo awal/tanggal batas. Mengulang finalisasi tidak mereset operasional. |
| AC-29 | KF-06/07, UC-06/08 | Biaya Internet/Wi-Fi dicatat sebagai pengeluaran: total pengeluaran bertambah; tagihan penghuni tidak bertambah. Nominal/tanggal invalid ditolak. |
| AC-30 | KF-07, UC-08 | Dua batas tanggal laporan termasuk, tanggal sebelum batas pencatatan/rentang terbalik ditolak, data kosong menghasilkan nol, saldo pembayaran lama dikecualikan. |
| AC-31 | KF-09, UC-07 | Pengingat tagihan muncul mulai H−3, tetap terlihat saat tempo dan menjadi tunggakan setelah lewat; lunas menghentikan pengingat pembayaran tanpa menghilangkan pengingat akhir sewa. |
| AC-32 | KF-09, UC-07 | Dashboard membedakan jumlah kamar, jumlah orang, kontrak aktif dan hunian perlu konfirmasi. Satu kamar dua penghuni berarti satu kamar dihuni dan dua orang tinggal. |
| AC-33 | KF-10, UC-09 | Konfirmasi pembayaran pertama setiap tagihan memuat periode/paket, nominal terpilih dan sisa terbaru; cicilan berikutnya menyediakan konfirmasi. Pembayaran Batal ditolak sebagai sumber konfirmasi valid. |
| AC-34 | KF-10, UC-09 | Nomor WA invalid ditolak; nomor valid membuka penerima dan teks yang sesuai. Paket dua orang memakai penanggung jawab yang dipilih. Tidak ada status terkirim otomatis. |
| AC-35 | KF-10, UC-09 | WA gagal dibuka atau pengelola tidak mengirim: pembayaran yang sudah tersimpan tetap ada dan saldo tetap benar. Tidak ada perubahan finansial karena klik tautan. |
| AC-36 | KF-05/06 | Lampiran JPG/PNG/PDF sampai 2 MB diterima bila valid. Tipe lain, file rusak/tidak sesuai tipe atau melebihi batas ditolak dengan pesan yang jelas. |
| AC-37 | KF-02/03, UC-03/04 | Andi/Budi pada kontrak dua orang: Andi keluar, Citra masuk sesudahnya sebelum kontrak berakhir. Riwayat memuat tiga nama, yang tinggal Budi/Citra; harga, tanggal akhir, tagihan dan sisa tetap. |
| AC-38 | KF-03, UC-04 | Menambah orang ketika dua orang masih tinggal, tanggal masuk sebelum keluarnya orang yang digantikan, benturan orang, tanggal masa depan atau masuk setelah akhir kontrak ditolak tanpa perubahan. |
| AC-39 | KF-03/10, UC-04/09 | Penggantian penghuni tidak otomatis mengganti penanggung jawab yang masih tinggal atau membagi tunggakan. Perubahan kontak yang dipilih pengelola memakai penghuni yang masih tinggal dan mempertahankan riwayat. |
| AC-40 | KF-03, UC-04 | Simpan pengganti gagal atau permintaan yang sama diulang: tidak ada hubungan orang ganda atau perubahan harga/tagihan; keadaan terakhir yang sah tetap konsisten. |
| AC-41 | KF-05/07, UC-05/08 | Tagihan Rp900.000 jatuh tempo 10 Oktober, uang pelunasan penuh diterima 10 Oktober tetapi dicatat 12 Oktober: tanggal bayar 10, waktu catat otomatis 12, status setelah simpan Lunas, pemasukan masuk rekap tanggal 10. |
| AC-42 | KF-05/09, UC-05/07 | Dari tagihan Rp900.000, cicilan Rp400.000 diterima 10 Oktober dan dicatat 12 Oktober: sisa Rp500.000 dan status pada 12 Oktober tetap Menunggak; tanggal cicilan tepat waktu tidak menggeser jatuh tempo sisa. |
| AC-43 | KF-04/05, UC-05 | Tagihan periode sah yang memenuhi aturan H−3 baru dilengkapi saat aplikasi dibuka setelah tanggal penerimaan: tanggal uang diterima yang sah tetap dapat dipakai walaupun lebih awal dari waktu pembuatan catatan tagihan. Waktu pencatatan otomatis tidak dapat diedit untuk menyamarkan input terlambat. |
| AC-44 | KF-05/11, UC-05/10 | Tanggal bayar sebelum batas pencatatan atau di masa depan ditolak sebagai pembayaran operasional. Penerimaan sebelum batas termasuk saldo awal sesuai prosedur; penolakan tidak mengubah waktu catat/saldo dan tidak membuka ulang finalisasi. |
| AC-45 | KF-05/07, UC-05/08 | Penerimaan Rp1.500.000 dialokasikan Rp500.000 melunasi Oktober dan Rp1.000.000 melunasi November pada masa sewa sama: dua saldo benar dan kas bertambah tepat Rp1.500.000 sekali. |
| AC-46 | KF-05, UC-05 | Total alokasi tidak sama dengan penerimaan, bagian nol/negatif, melebihi sisa, tagihan Batal atau lintas masa sewa ditolak; tidak ada pembayaran/alokasi sebagian tersimpan. |
| AC-47 | KF-05/07, UC-05/08 | Pengulangan permintaan tidak menggandakan penerimaan; pembayaran bersamaan tidak melampaui saldo. Membatalkan penerimaan beralasan membatalkan seluruh alokasinya, memulihkan sisa dan mengecualikan total kas sekali; riwayat utuh. |
| AC-48 | KF-10, UC-09 | Konfirmasi WA penerimaan beberapa periode menampilkan total uang, alokasi tiap periode dan sisa terbaru tanpa penggandaan. Penentuan pembayaran pertama dilakukan per tagihan berdasarkan alokasi Valid. |
| AC-49 | KF-06/07, UC-06/08 | Pengeluaran Rp150.000 dikoreksi menjadi Rp100.000 dengan alasan: nilai lama/baru, pelaku dan waktu server tetap dapat ditelusuri; laporan memakai Rp100.000. Jika tanggal diubah, laporan rentang lama/baru ikut benar; koreksi invalid atau gagal tidak mengubah data dan riwayat sebagian. |
| AC-50 | KF-06/07, UC-06/08 | Pengeluaran duplikat dibatalkan dengan alasan: catatan dan riwayat tetap tersimpan, tidak dihitung pada laporan. Tanpa alasan ditolak; tidak tersedia hapus permanen atau transaksi refund otomatis. |

Angka tarif pada contoh adalah data uji, bukan tarif mitra.

## 9. Kebutuhan kualitas dan antarmuka

### 9.1 KNF-01 Kinerja

Target dari proposal: pencarian dan laporan paling lama 3 detik di lingkungan uji lokal dengan 100 kamar, 500 penghuni termasuk riwayat, dan 10.000 transaksi. Ini target yang harus diukur, bukan klaim telah tercapai. Perangkat, browser, jaringan, data uji, langkah dan waktu pengukuran dicatat. Target hosting/HP riil ditinjau setelah lingkungan dipilih.

### 9.2 KNF-02 Keandalan

- Pembuatan kontrak beserta penghuni/tagihan pertama, pembayaran dan finalisasi tidak menghasilkan data parsial.
- Penyimpanan ganda dan pembentukan tagihan berulang dicegah di sisi penyimpanan, bukan hanya dengan menonaktifkan tombol.
- Saldo lama terpisah dari kas baru dan dapat ditelusuri per periode.
- Backup mencakup basis data serta lampiran. Prosedur pemulihan diuji dengan mencocokkan jumlah data, saldo, akses login dan pembukaan lampiran pada hasil pemulihan.
- Jadwal, penanggung jawab, lokasi penyimpanan dan retensi backup ditetapkan sebelum pemakaian mitra; lihat O-06.

### 9.3 KNF-03 Akses dan penggunaan melalui HP

- Username/password, password minimal 8 karakter sesuai revisi pengguna yang mendukung frasa sandi, konfirmasi pada registrasi, hash password dan pembatasan percobaan login.
- Semua halaman data, endpoint dan lampiran memerlukan sesi pengelola. Registrasi awal dilindungi dan ditutup setelah akun dibuat.
- Ganti password memakai password lama; pemulihan lewat pemeliharaan yang memverifikasi pemilik, tanpa registrasi ulang publik.
- Formulir dua penghuni, daftar tagihan dan pratinjau WA dapat digunakan pada layar HP tanpa tombol terpotong. Pengguliran daftar boleh dilakukan, tetapi tindakan utama tetap dapat dijangkau.
- Pesan kesalahan menjelaskan isian yang perlu diperbaiki; kesalahan tidak menghapus seluruh masukan yang sudah diisi.
- Tombol simpan menunjukkan proses dan hasil. Pembatalan pembayaran, finalisasi data awal dan konfirmasi keluar meminta pemeriksaan ringkasan sebelum disimpan.
- Kata status diberi label jelas; pengguna tidak harus memahami warna untuk membedakannya.
- Browser dan perangkat penerimaan ditetapkan berdasarkan HP pengelola dan laptop tim; validasi perangkat riil dilakukan sebelum pekan 15.

### 9.4 Susunan halaman awal untuk ditinjau di design.md

| Halaman | Tugas utama |
| --- | --- |
| Penyiapan / Login | Registrasi awal, masuk, ganti password saat sudah masuk |
| Data awal | Formulir berkas penghuni/kontrak, baris tagihan, rekap dan finalisasi |
| Dashboard | Ringkasan kamar/orang, kas, piutang dan daftar tindak lanjut |
| Kamar | Pencarian, data kamar, dukungan paket dan ketersediaan |
| Penghuni | Pencarian, detail orang, riwayat dan kontak WA |
| Masa sewa | Dua pilihan paket, satu/dua nama, penanggung jawab, tanggal, perpanjangan dan keluar per orang |
| Tagihan dan pembayaran | Periode, sisa, cicilan, pembatalan dan konfirmasi WA |
| Pengeluaran | Catat/lihat biaya, koreksi dengan riwayat dan pembatalan beralasan |
| Laporan | Rentang tanggal, rincian dan total kas |

Paket dipilih sebagai bagian masa sewa; belum diperlukan menu paket atau tarif terpisah. Susunan navigasi ini usulan desain yang mengikuti fitur, bukan kewajiban membuat satu halaman untuk setiap kelas.

## 10. Perubahan yang diperlukan pada proposal dan diagram

Proposal versi 6 tetap menjadi dasar untuk aturan yang tidak berubah. Penambahan dua orang harus dicatat sebagai revisi berikutnya, bukan diklaim sudah tergambar di versi 6.

| Artefak | Perubahan |
| --- | --- |
| KF-01 | Tambahkan dukungan jenis hunian kamar; kapasitas kamar bukan tarif per orang |
| KF-02/KF-03 | Hubungkan kedua penghuni ke kontrak, catat keluar per orang dan penanggung jawab administratif |
| KF-04/KF-05 | Sertakan alokasi satu penerimaan ke beberapa tagihan, simpan atomik dan kas sekali. Tegaskan satu tagihan kamar per periode dan satu saldo bersama; pisahkan tanggal uang diterima dari waktu pencatatan otomatis, termasuk tagihan yang baru dilengkapi belakangan |
| KF-06/KF-07 | Tambahkan koreksi/pembatalan pengeluaran beralasan, riwayat nilai lama/baru dan rekap hanya catatan Valid |
| KF-09 | Bedakan hitungan kamar, orang tinggal, kontrak aktif dan hunian perlu konfirmasi |
| KF-10 | Arahkan pesan tagihan/akhir sewa ke penanggung jawab terkini; riwayat kontak tidak dihapus |
| KF-11 | Migrasi dua nama, keadaan tinggal per orang dan saldo per tagihan kamar |
| Use case | Sebelas UC tetap; rincian UC-03/04/05/07/09/10 diperluas |
| Activity | Tambahkan validasi jumlah nama, pemilihan/penggantian penanggung jawab serta keluar satu orang tanpa mengakhiri seluruh kontrak, serta penghuni pengganti tanpa menimpa riwayat |
| Class | Tambahkan hubungan Penghunian antara Penghuni dan MasaSewa; pindahkan tanggal masuk/keluar orang ke hubungan ini. Satu kontrak dapat memiliki banyak hubungan historis, dengan maksimal dua orang tinggal bersamaan pada paket dua orang; tetapkan jenis hunian pada paket dan snapshot kontrak. Pembayaran memiliki rincian AlokasiPembayaran ke satu/beberapa tagihan; kas dihitung dari induk penerimaan |
| Sequence | Simpan kontrak dengan satu/dua penghunian secara atomik; keluar penanggung jawab dan penunjukan penerus disimpan bersama; pembayaran dengan seluruh alokasinya dan koreksi pengeluaran dengan riwayat disimpan atomik |
| Pengujian | Tambahkan enam kombinasi paket, keluar satu orang, penggantian penanggung jawab, hitungan kamar/orang dan satu tagihan bersama |

TanggalKeluarAktual pada MasaSewa saja tidak dapat merepresentasikan dua orang yang keluar pada tanggal berbeda atau riwayat penghuni pengganti. Penutupan hunian tingkat kontrak harus diturunkan dari hubungan orang dan kelanjutannya; satu boolean kontrak tidak boleh menjadi satu-satunya bukti bahwa kedua orang sudah keluar.

## 11. Pemetaan kebutuhan ke implementasi dan pengujian

| Kebutuhan | Modul calon implementasi | AC utama |
| --- | --- | --- |
| KF-01 | Kamar dan ketersediaan | AC-04, AC-09, AC-12, AC-13 |
| KF-02 | Penghuni dan kontak | AC-05, AC-07, AC-10, AC-11, AC-37 |
| KF-03 | Masa sewa, paket dan penghunian | AC-06 sampai AC-14, AC-18, AC-37 sampai AC-40 |
| KF-04 | Pembentukan periode/tagihan | AC-08, AC-15 sampai AC-18, AC-43 |
| KF-05 | Pembayaran dan koreksi | AC-19 sampai AC-24, AC-36, AC-41 sampai AC-47 |
| KF-06 | Pengeluaran | AC-29, AC-36, AC-49, AC-50 |
| KF-07 | Laporan kas | AC-23, AC-25, AC-29, AC-30, AC-41, AC-45, AC-47, AC-49, AC-50 |
| KF-08 | Sesi dan akun | AC-02, AC-03 |
| KF-09 | Dashboard dan pengingat | AC-12, AC-31, AC-32, AC-42 |
| KF-10 | Penyusunan pesan WA | AC-33 sampai AC-35, AC-39, AC-48 |
| KF-11 | Inisialisasi | AC-25 sampai AC-28, AC-44 |
| KF-12 | Penyiapan akun awal | AC-01 |

Nama modul merupakan pembagian tanggung jawab produk; struktur folder dan framework belum ditetapkan.

## 12. Rencana verifikasi

### 12.1 Black box

Susun kasus dari AC, termasuk alur berhasil, masukan tidak valid, batas tanggal/nominal/jumlah orang, perubahan status dan kegagalan. Setiap kasus mencatat ID, KF/UC/AC, prasyarat, data, langkah, hasil yang diharapkan, hasil aktual, bukti, status dan versi aplikasi. Uji fitur WA mencakup pembukaan penerima/teks di HP; klik tombol saja tidak membuktikan pesan sudah dikirim.

### 12.2 White box

Setelah kode tersedia, pilih logika jumlah penghuni, benturan interval, kalender paket, tagihan H−3, saldo/pembatalan, finalisasi, ketersediaan kamar dan template WA. Susun control flow dari kode aktual; identifikasi percabangan/jalur yang diuji dan catat cakupan. Jika dosen mewajibkan basis path atau perhitungan kompleksitas siklomatis, gunakan fungsi aktual sebagai dasar perhitungan. Diagram rancangan tidak menggantikan bukti white box kode.

Target awal: seluruh aturan saldo dan cabang status penting diuji. Persentase cakupan dan format laporan formal ditetapkan sesuai ketentuan dosen, bukan diklaim sudah 100% dalam PRD.

### 12.3 Penerimaan bersama mitra

Gunakan data uji atau data mitra yang telah diperiksa. Pengelola mencoba memasukkan data awal, kontrak dua orang, cicilan berbeda metode, keluar satu orang, pengingat WA serta laporan melalui HP. Koreksi hasilnya sebelum penyerahan. Riwayat anggota kelompok dan data pribadi pada dokumen administrasi tidak menjadi data demo otomatis.

## 13. Jadwal dan prioritas

Semua fitur pada KF-01 sampai KF-12 merupakan ruang lingkup wajib. Urutan di bawah mengatur pengerjaan dan ketergantungan, bukan izin menghilangkan fitur tanpa perubahan kebutuhan.

| Pekan | Keluaran |
| --- | --- |
| 11 | Tinjau PRD, tutup keputusan penting, sesuaikan proposal/diagram dua orang, pilih teknologi, rancangan data dan antarmuka |
| 12 | Penyiapan akun/sesi, kamar, penghuni, paket/penghunian dan alur data awal; pengujian unit/fitur sejak awal |
| 13 | Kontrak, kalender periode, tagihan, pembayaran/pembatalan dan pengeluaran; uji saldo serta integritas |
| 14 | Dashboard, pengingat, WA, laporan dan integrasi konfirmasi hunian; seluruh fitur wajib dapat dijalankan pada akhir pekan |
| 15 | Black box dan white box formal, perbaikan temuan, pengujian ulang, dokumentasi serta penerimaan mitra |
| 16 | Presentasi/demonstrasi, menggunakan versi dan data demo yang sudah diperiksa |

Tanggal kalender, kapasitas waktu anggota dan pembagian pekerjaan belum diberikan; tidak diasumsikan sudah ada. Pekerjaan pengujian tidak ditunda seluruhnya ke pekan 15. Jika jadwal terancam, kurangi pekerjaan opsional melalui keputusan tim/dosen; jangan diam-diam menghapus kontrol saldo atau kasus dua penghuni.

## 14. Keputusan final dan kebutuhan validasi

| ID | Keputusan | Status dan usulan | Perlu diputuskan |
| --- | --- | --- | --- |
| O-01 | Pengiriman WA | Final untuk versi pertama: tombol, pratinjau template dan kirim manual melalui WhatsApp. Tidak ada biaya API WA dalam rancangan ini | Tim mengonfirmasi kesesuaian dengan penilaian dosen; persetujuan dosen atas perubahan tidak diasumsikan. Jika diminta otomatis, catat sebagai perubahan kebutuhan dan anggaran |
| O-02 | Penghuni pengganti | Final sesuai BR-12 dan AC-37 sampai AC-40 | Sinkronisasi proposal/diagram |
| O-03 | Tanggal penerimaan dan waktu catat | Final sesuai BR-27/41 dan AC-41 sampai AC-44 | Sinkronisasi proposal/diagram |
| O-04 | Satu penerimaan beberapa tagihan | Final: alokasi manual dalam masa sewa sama, total tepat, atomik, kas sekali, pembatalan seluruh penerimaan | Model induk pembayaran dan alokasi wajib tercermin dalam diagram/data |
| O-05 | Koreksi pengeluaran | Final: ubah beralasan dengan nilai lama/baru, pelaku dan waktu; pembatalan beralasan untuk catatan salah/duplikat, tanpa hapus permanen. Lihat BR-40, AC-49/50 | Terapkan dalam KF-06 dan laporan |
| O-06 | Teknologi, hosting dan backup | Didelegasikan ke architecture.md. Backup wajib mencakup DB dan lampiran, tersedia di luar server aplikasi dengan akses terbatas. Baseline: setiap hari setelah ada transaksi, sebelum deployment/migrasi, retensi 7 harian dan 4 mingguan; pemulihan diuji sebelum serah terima | Tim menetapkan satu penanggung jawab bernama, media dan cara menjalankan backup sebelum data nyata digunakan; provider dan biaya tidak diasumsikan gratis |
| O-07 | Keamanan dan data wajib | Arsitektur menetapkan parameter teknis. Baseline: username unik tanpa membedakan huruf besar/kecil, 4–32 karakter huruf/angka/titik/garis bawah; password minimal 8 karakter sesuai revisi pengguna; batas awal 5 kegagalan login per 15 menit per username dan IP; sesi berakhir setelah 120 menit tanpa aktivitas, tanpa remember-me pada versi pertama | Nama penghuni wajib; identitas berupa jenis/nomor sesuai catatan mitra dan bukan wajib NIK. WA opsional tetapi aksi pesan dinonaktifkan jika tidak valid. Proteksi sesi, CSRF dan hashing mengikuti framework |
| O-08 | Tarif dan kamar dua orang | Model final: enam kombinasi paket, tarif total kamar dimasukkan per kesepakatan, dukungan hunian ditentukan per kamar | Tarif/kamar nyata diverifikasi bersama mitra sebelum operasional; angka contoh tidak boleh dipakai sebagai tarif asli |
| O-09 | Pengujian white box | Final: unit/feature test selama pembangunan; white box formal memakai kode aktual pada fungsi bisnis inti, control flow, kompleksitas siklomatis dan basis path pada fungsi yang dipilih; hasil aktual dan cakupan dilaporkan apa adanya | Tim mencocokkan format dan fungsi yang dipilih dengan rubrik dosen sebelum pekan 15. Tidak mengklaim cakupan 100% tanpa bukti |

Persetujuan finalisasi oleh pengguna menutup keputusan kebutuhan produk dan mendelegasikan rincian teknis ke arsitektur. Persetujuan pihak lain, harga nyata, kemampuan perangkat, pembagian tugas tim dan biaya hosting tetap harus dibuktikan. Hal-hal tersebut tidak boleh diisi dengan data rekaan. Backup merupakan kebutuhan operasional, bukan menu penjadwalan baru bagi pengelola.

## 15. Syarat siap implementasi dan selesai

### 15.1 Baseline kebutuhan dan kesiapan implementasi

- [x] Pengguna menyetujui finalisasi kebutuhan versi pertama dan melanjutkan ke arsitektur. Peninjauan internal seluruh anggota tim tetap dilakukan.
- [x] Batas kebutuhan O-01 sampai O-09 ditetapkan; kebutuhan validasi eksternal dan delegasi teknis dicatat secara eksplisit pada bagian 14.
- [ ] Proposal serta use case/activity/class/sequence disesuaikan dengan keputusan dua orang dan keluar per orang.
- [ ] Arsitektur, model data dan desain halaman ditetapkan tanpa mengubah aturan bisnis diam-diam.
- [ ] Kasus uji untuk saldo, paket dua orang, hunian dan pengingat sudah tersedia sebagai acuan.

### 15.2 Selesai untuk uji formal

- [ ] Seluruh fitur wajib dapat dijalankan pada akhir pekan 14.
- [ ] Kebutuhan dipetakan ke modul dan kasus uji.
- [ ] Tidak ada kesalahan terbuka yang menyebabkan kehilangan data, akses tanpa izin, saldo salah, tagihan ganda atau penempatan kamar yang masih dihuni.
- [ ] Bukti pengujian serta temuan tersedia; perbaikan diuji ulang.
- [ ] Backup dan pemulihan telah dicoba, serta panduan pengelola tersedia.
- [ ] Data demo dan versi untuk presentasi dipastikan; tidak bergantung pada data pribadi asli yang tidak diperlukan.

## 16. Dokumen lanjutan

| Dokumen | Tanggung jawab |
| --- | --- |
| design.md | Navigasi, formulir, tampilan HP, keadaan kosong/gagal/berhasil dan pratinjau pesan |
| architecture.md | Teknologi, batas layanan, autentikasi, penyimpanan berkas, transaksi, deployment dan pemulihan |
| database.md | Skema termasuk Penghunian, relasi, snapshot, batas integritas serta migrasi |
| test-plan.md | Kasus rinci dan rencana black box/white box berdasarkan AC serta kode aktual |
| traceability.md | Pemetaan final KF/UC/BR/AC ke diagram, kode, kasus uji dan bukti |

Dokumen lanjutan belum dibuat dalam revisi PRD ini. Setiap perubahan keputusan bisnis harus memperbarui PRD dan artefak terkait, bukan hanya kode.

## 17. Riwayat perubahan

| Versi | Perubahan |
| --- | --- |
| 0.1 | Draf awal berdasarkan proposal versi 6, ditambah keputusan satu/dua orang, satu tagihan kamar, pencatatan keluar per orang dan jadwal pekan 11–16. Keputusan terbuka diberi ID agar tidak dianggap sudah disetujui. |
| 0.2 | Penghuni pengganti pada paket dua orang diizinkan melalui pengelola; riwayat dapat lebih dari dua nama tetapi maksimal dua orang tinggal bersamaan. Menutup O-02, memperbarui BR-12, menambah F-04A serta AC-37 sampai AC-40. Harga, akhir kontrak dan tagihan tetap. |
| 0.3 | Tanggal bayar mengikuti penerimaan sebenarnya; waktu pencatatan otomatis dipisahkan. Menutup O-03, memperjelas BR-27/41, serta menambah AC-41 sampai AC-44 untuk laporan dan status pada input terlambat. |
| 0.4 | Menutup O-04: satu penerimaan dapat dialokasikan manual ke beberapa tagihan dalam masa sewa yang sama; total tepat, kas sekali, transaksi atomik dan pembatalan seluruh penerimaan. Menambah AC-45 sampai AC-48. Sisa keputusan akan dibahas sekaligus agar tidak membutuhkan persetujuan satu per satu. |
| 1.0 | Finalisasi kebutuhan atas instruksi pengguna. Menetapkan koreksi/pembatalan pengeluaran dengan riwayat (AC-49/50), memperjelas kas dihitung dari induk pembayaran sekali, menutup keputusan produk dan menetapkan baseline keamanan/backup serta kebutuhan validasi eksternal. Teknologi dibahas pada arsitektur; tidak mengklaim proposal, kode atau pengujian telah selesai. |
