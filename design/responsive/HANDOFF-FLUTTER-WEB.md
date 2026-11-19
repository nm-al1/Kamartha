# Kamartha: handoff layout mobile responsif

## Status pekerjaan

Dokumen ini mencatat hasil penyempurnaan responsivitas dan penyesuaian sistem warna desain Kamartha melalui MCP FigCraft yang terhubung ke dokumen kerja aktif `design/kamartha-design-responsive.figcraft`.

- **Audit Struktural 28 Layar**: Selesai untuk seluruh 28 layar mobile operasional pada halaman `Design.md · Kamartha UI`. Seluruh root frame menggunakan vertical Auto Layout, scroll viewport mengisi sisa tinggi (`fill`), konten mengalir secara adaptif (`fill` width, `hug` height), dan footer/navbar terpisah secara hierarkis tanpa tumpang tindih.
- **Penyelarasan Layout Anti-Slop**: Menghilangkan padding bersarang ganda (*nested double-padding*) pada `HOME-01` (`Hero dan panel hunian` serta `Tindak lanjut · aliran`) yang sebelumnya menyusutkan kartu konten ke 296 px; seluruh kartu operasional kini mengisi penuh lebar konten 328 px dengan margin 16 px yang konsisten di semua layar. Token kelengkungan (*corner radius*) diselaraskan 100% (kartu 16 px, input 12 px, tombol 24 px, chip pill 999 px). Memperbaiki posisi ikon filter pada `INV-01` ke dalam header responsif di samping judul, merekonstruksi kartu `Ringkasan kas` pada `REPORT-01` menjadi modular dua kolom KPI dengan garis pembatas penuh dan baris surplus yang seimbang.
- **Implementasi Floating Pill Navbar (Persis Referensi)**: Mengubah bilah navigasi bawah menjadi desain kapsul mengambang (*floating pill capsule*) dengan permukaan putih `#FFFFFF`, sudut kapsul bulat penuh (*radius 32 px*), bayangan ambient difus lembut (`blur 16 px, offset [0, 4]`), dan margin mengambang (16 px kiri/kanan/bawah). State aktif item Beranda menggunakan ikon rumah *solid filled* oranye `#FD3D18` dengan teks SemiBold oranye, persis dengan referensi desain yang diberikan. Seluruh 4 varian master pada `Components · Kamartha` dan seluruh instansi layar operasional (`HOME-01`, `ROOM-01`, `INV-01`, `EXP-01`, `MENU-01`) telah diperbarui secara seragam.
- **Tata Letak Kanvas & Pemisahan Frame (Canvas Cleanliness)**: Memperbaiki posisi frame `STATE` (ID 2237) yang sebelumnya bertumpuk di bawah frame mobile `PAY-05` dan `EXP-03`. Seluruh layar baris kedua kini tersusun sebaris secara kontigu dengan jarak 70 px: `ROOM-03` (x=0), `RES-03` (x=430), `EXP-02` (x=860), `LEASE-03` (x=1290), `PAY-04` (x=1720), `PAY-05` (x=2150), `EXP-03` (x=2580), `INV-03` (x=3010), dan frame `STATE` diletakkan di paling kanan (x=3440, w=1200 px). Seluruh label judul merah di atas frame dinaikkan (Baris 1 ke `y = -40 px`, Baris 2 ke `y = 1750 px`) dengan jarak aman di atas judul native frame FigCraft sehingga tidak terjadi tabrakan teks sama sekali.
- **Penyelarasan Warna Persis Sesuai Referensi Visual**: Telah disesuaikan 100% mengikuti referensi visual asli `design/references/beranda-detail-pembayaran.png` ("Arah visual 03 - Adaptasi referensi Accomodio"). Seluruh token warna primer, tombol aksi, tautan, lencana status, tab aktif, dan kartu cepat diperbarui dari nilai lama (yang sebelumnya cenderung kecokelatan/rust) menjadi warna oranye hangat cerah, emerald green, warm amber, dan vivid red sesuai referensi.
- **Penyimpanan Dokumen Kerja**: Dokumen telah disimpan secara permanen ke `design/kamartha-design-responsive.figcraft` (dirty flag: false). File referensi sebelum responsivitas (`design/kamartha-design.figcraft`) dan file cadangan (`design/kamartha-design-before-responsive.figcraft`) tetap dipertahankan tanpa modifikasi.
- **Pembersihan Halaman Verifikasi**: Halaman sementara `QA responsif · sementara` telah dihapus dari dokumen setelah seluruh 50 berkas bukti ekspor selesai dihasilkan ulang dan diverifikasi di `design/responsive/verified/`.
- **Backend & Kode Aplikasi**: Sesuai batasan pekerjaan, backend, basis data, dan kode Flutter tidak disentuh.

---

## Sistem token warna (100% presisi referensi Accomodio)

Palet warna telah diselaraskan persis dengan sampel piksel dari referensi visual operasional:

| Token | Nilai Hex | Peran & Penggunaan UI |
| --- | --- | --- |
| `primary_action` | `#FD3D18` | Tombol utama ("Catat pembayaran", "Simpan pembayaran →", "Masuk"), teks aksi WhatsApp, ikon pencatatan cepat. |
| `brand` | `#FA6921` | Logo brand header, swatch identitas visual Kamartha. |
| `link` | `#FE4300` | Tautan kontekstual ("Lihat semua tagihan →", "Ubah", "Kelola", "Lupa password"). |
| `ink` | `#142039` | Judul layar, teks utama, angka nominal, nomor kamar, label input. |
| `secondary_text`| `#526079` | Subjudul, label metadata, placeholder pencarian, ikon/label navbar tidak aktif. |
| `background` | `#F3F6F9` | Latar belakang halaman aplikasi (cool soft grey-white). |
| `surface` | `#FFFFFF` | Permukaan kartu, panel hunian, input formulir, navbar bawah. |
| `border` | `#DCE3EB` | Garis tepi kartu, pemisah baris, batas input default. |
| `divider` | `#EEF2F6` | Garis pemisah tipis antar-item di dalam kartu. |
| `success` | `#08964D` | Teks & titik status lunas / dihuni (vibrant emerald green). |
| `success_bg` | `#D5F5E5` | Latar belakang chip status lunas / dihuni (crisp mint). |
| `warning` | `#FE6507` | Teks & titik status perlu konfirmasi / dibayar sebagian / jatuh tempo besok (warm amber-orange). |
| `warning_bg` | `#FFF3E0` | Latar belakang chip status peringatan / persiapan. |
| `danger` | `#E53935` | Teks & titik status terlambat / menunggak (vivid red). |
| `danger_bg` | `#FEE2E2` | Latar belakang chip status menunggak. |
| `room_chip_bg` | `#ECF2F7` | Latar chip nomor kamar ("A-05", "B-01", "A-03") dengan teks ink `#142039`. |
| `tab_active_bg`| `#091C39` | Latar belakang tab aktif "Tagihan" dengan lencana oranye `#FF511D`. |
| `tab_inactive` | `#ECF2F7` | Latar belakang tab tidak aktif "Akhir sewa" dengan teks slate `#54627F`. |
| `header_grad` | `#F85413` → `#FA6921` → `#EF3A0E` | Gradien linier latar header Beranda dan Login (tetap oranye cerah hangat, tanpa nuansa gelap rust). |

### Komponen Kunci Khusus
1. **Pencatatan Cepat (Beranda)**: Menggunakan tombol pill putih (`#FFFFFF`) dengan border halus (`#DCE3EB`), ikon oranye cerah (`#FD3D18`), dan teks dark ink (`#142039`), bukan latar peach.
2. **Total Uang Diterima (Tinjau Pembayaran)**: Angka nominal berukuran besar ditampilkan dalam warna oranye cerah (`#FD3D18` / `#FE561D`) untuk penegasan visual yang kuat.
3. **Navbar Aktif**: Ikon outline 24×24 dan label item aktif diwarnai oranye cerah (`#FE4300` / `#FD3D18`), sedangkan item tidak aktif menggunakan slate grey (`#526079`).

---

## Sistem layout

Gunakan logical pixels, bukan faktor skala atas seluruh frame 390×844. Ukuran 390×844 merupakan referensi kanonis desain mobile, sedangkan implementasi aktual wajib adaptif terhadap constraints dinamis.

### Struktur halaman

1. **Inset atas perangkat**: Ditangani via `SafeArea` / `MediaQuery.paddingOf(context).top`.
2. **Header berukuran sesuai isinya (`hug`)**: Tombol kembali 48×48 transparan dengan ikon outline 24×24. Judul dan konteks header dapat membungkus secara vertikal tanpa pemotongan.
3. **Area gulir (`fill`)**: Mengisi sisa tinggi layar di antara header dan footer. Kolom konten mengikuti lebar tersedia (`fill`), sedangkan tinggi kelompok mengikuti isi (`hug`).
4. **Footer aksi atau navbar**: Mengikuti aliran layout terpisah di bawah viewport gulir, bukan ditumpuk di atas field terakhir. Pada layar sangat sempit / teks besar (seperti PAY-02 Tinjau pembayaran), footer dipindahkan ke akhir konten gulir agar area interaksi formulir tidak terhimpit.
5. **Inset bawah perangkat**: Diterapkan tepat sekali pada container paling bawah (navbar atau safe area bawah halaman).

Login menggulirkan brand dan formulir sebagai satu kesatuan. Beranda menggulirkan hero sapaan, panel hunian, dan tindak lanjut, sementara navbar berada di luar area gulir. Latar oranye mengikuti pertumbuhan tinggi blok sapaan sehingga teks tanggal dan kartu hunian tidak saling bertabrakan.

### Lebar dan teks

- Gunakan `LayoutBuilder` pada area halaman/konten untuk membaca `BoxConstraints` aktual dalam logical pixels.
- **Padding horizontal responsif**: 16 logical px untuk lebar viewport < 390 px (profil Narrow); 20 logical px ketika ruang mencukupi (profil Regular).
- Input, panel kartu, kelompok informasi, dan tombol utama mengikuti lebar konten (`fill width`).
- **Penanganan Teks Panjang**: Nama dan metadata penting wajib dapat membungkus (`softWrap: true`). Dilarang memakai `FittedBox` atau penurunan ukuran font drastis yang merusak keterbacaan data krusial.
- **Nominal dan Angka**: Nominal diberikan ruang intrinsik yang cukup. Jika kombinasi label dan nominal tidak muat satu baris pada viewport sempit, tata label di atas nominal. Seluruh digit nominal wajib terbaca utuh.
- **Pasangan Label/Nilai**: Disusun berpasangan per baris/kelompok (horizontal frame per item). Dilarang memisahkan semua label ke satu kolom kiri dan semua nilai ke satu kolom kanan terpisah karena perbedaan jumlah baris teks akan menggeser alignment pasangan.
- **Skala Font**: Isi/input 16, metadata penting 14, dan label navbar 13 pada skala normal (100%), sesuai `docs/design.md`.

### Safe area dan Android modern (Edge-to-Edge)

Pada Android 14 dan Android 15, mode **Edge-to-Edge** diwajibkan secara default di mana aplikasi merender konten di balik bilah status (*status bar*) dan bilah navigasi gestur (*gesture navigation bar*). Desain Kamartha telah diselaraskan penuh dengan parameter Android modern:

1. **Inset Atas (`safe_top`)**: **40 logical px** (mengakomodasi *punch-hole camera cutout* / kamera tengah perangkat modern seperti Samsung Galaxy A/S series dan Google Pixel 7/8/9).
2. **Inset Bawah (`safe_bottom`)**: **24 logical px** (mengakomodasi *gesture navigation bar pill* modern; bukan 0 px gaya lawas 3-tombol).
3. **Margin Layar (`screen_padding`)**: **16 logical px** (standar margin compact Material Design 3 untuk layar < 600 dp).
4. **Floating Capsule Bottom Navigation Bar (Pill Floating Nav)**:
   - Mengikuti referensi desain modern kapsul mengambang (*floating pill*):
     - **Bentuk Kapsul**: Ujung bulat penuh (*pill shape*) menggunakan `BorderRadius.circular(32)`.
     - **Dimensi**: Lebar kartu kapsul 328 px pada layar 360 px (margin kiri & kanan 16 px), tinggi kapsul 64 px.
     - **Margin Mengambang**: Memiliki jarak bebas (*air gap*) 8 px dari konten di atasnya dan 16 px di atas area gestur bawah sistem Android/iOS (total tinggi container: 88 px).
     - **Permukaan & Bayangan**: Warna putih solid `#FFFFFF` dengan bayangan lembut mengambang (*soft ambient drop shadow*): `BoxShadow(color: Color(0x1F142039), blurRadius: 16, offset: Offset(0, 4))`.
     - **Ikon Bersih & Modern (*Superclean Vector Icons*)**:
       - **Beranda**: Ikon rumah beratap simetris dengan pintu lengkung (*door cutout*). Saat aktif, berwarna oranye *solid filled* `#FD3D18` (persis gambar referensi); saat tidak aktif, berupa garis *outline* slate grey `#526079`.
       - **Kamar**: Ikon tempat tidur modern tampak depan (*front-facing bed* gaya Lucide) dengan sandaran kepala (*headboard*), kasur (*mattress*), dan kaki ranjang yang seimbang secara optik.
       - **Tagihan**: Ikon lembar dokumen tagihan bersudut bulat (*rounded invoice sheet*) dengan 3 baris rincian bersih (menghilangkan gerigi zig-zag kasar sebelumnya).
       - **Menu**: Tiga garis horizontal simetris dengan ujung kapsul membulat halus (*round stroke caps*).
     - **State Aktif (Persis Referensi)**:
       - Item `Beranda` aktif menggunakan ikon rumah *solid filled* oranye cerah `#FD3D18` dengan teks SemiBold `#FD3D18`.
       - Item `Kamar`, `Tagihan`, dan `Menu` aktif menggunakan ikon tegas `#FD3D18` (bobot 2.2 px) dengan teks SemiBold `#FD3D18`.
     - **State Tidak Aktif**: Ikon outline bersih berwarna slate grey `#526079` (bobot 1.8 px, `strokeJoin: round`) dengan teks Regular 12 px `#526079`.
5. **Footer Aksi Tetap**: Seluruh tombol aksi pada footer bawah dinaikkan dengan bantalan 16–24 px agar tidak tertutup atau terganggu oleh gestur geser horizontal OS Android, serta tersusun harmonis di atas bilah navigasi mengambang.

- Mode variabel responsif pada FigCraft (`Responsive · device insets`):
  - `Android modern (Edge-to-Edge)` *(Default Mode)*: Inset atas 40 px, inset bawah 24 px.
  - `Android legacy (3-button)`: Inset atas 24 px, bawah 0 px (simulasi 3-tombol lawas).
  - `iPhone example`: Inset atas 44 px, bawah 34 px (simulasi Dynamic Island / Notch).
- Baseline kanonis mobile pada halaman `Design.md · Kamartha UI`: **360×800 logical px** (rasio 20:9), standar acuan compact modern Android. Layout adaptif penuh (`fill width`, `hug/fill height`) sehingga otomatis membentang elegan ke ukuran Pixel (412×915 px) maupun iPhone (390×844 px).

### Gulir dan keyboard

- Pada ruang vertikal terbatas, pertahankan area gulir yang dibatasi viewport dan konten yang dapat memanjang melampaui viewport.
- Gunakan `Scaffold(resizeToAvoidBottomInset: true)` dengan pengelolaan keyboard yang eksplisit melalui `MediaQuery.viewInsetsOf(context).bottom`.
- Jangan menambahkan tinggi keyboard dua kali ketika `Scaffold` sudah mengurangi ruang body.
- Saat field mendapat fokus, pastikan field, label/pesan validasi, dan kontrol aksi dapat digulir ke area yang terlihat menggunakan `Scrollable.ensureVisible`. Footer tidak boleh menutupi field terakhir.
- Jika footer aksi dan teks besar memakai sebagian besar layar, susun tombol aksi di akhir konten gulir agar area formulir tetap dapat dioperasikan.

### Text scaling

- Hormati `MediaQuery.textScalerOf(context)` dan preferensi aksesibilitas pengguna. Jangan mematikan scaling secara global atau membatasi `maxScaleFactor < 2.0`.
- Tinggi tombol minimal 48 px dan tinggi input minimal 52 px (radius 24 untuk tombol, 12 untuk input). Ini adalah tinggi minimum; label yang membungkus wajib menambah tinggi kontrol secara dinamis.
- **Navbar**: Mempertahankan empat kolom sama lebar (`fill width`). Area item bertambah tinggi mengikuti label yang membungkus; ikon tetap 24×24 fixed.
- Pisahkan area item navbar dari inset bawah dinamis.

---

## Verifikasi yang benar-benar dilakukan

Verifikasi menyeluruh dilakukan terhadap lima layar perwakilan:
1. **HOME-01 Beranda** (ID 421)
2. **AUTH-01 Login** (ID 401)
3. **ROOM-02 Detail kamar** (ID 510)
4. **PAY-01 Catat pembayaran** (ID 592)
5. **PAY-02 Tinjau pembayaran** (ID 624)

### Matriks Pengujian dan Berkas Bukti

Seluruh berkas bukti disimpan dalam folder `design/responsive/verified/`:

| Ukuran logical px | Profil Density / Inset | Skala Teks 100% (Normal) | Skala Teks 200% (Stress Test) | Status |
| --- | --- | --- | --- | --- |
| **320×568** | Narrow (pad 16); Android (24/0) | 5 PNG viewport (`-100pct.png`) | 5 PNG viewport + 5 PNG konten penuh (`-scrolled.png`) | Diverifikasi utuh |
| **360×800** | Narrow (pad 16); Android (24/0) | 5 PNG viewport (`-100pct.png`) | 5 PNG viewport (`-200pct-stress.png`) | Diverifikasi utuh |
| **390×844** | Regular (pad 20); iPhone (44/34) | 5 PNG viewport (`-100pct.png`) | 5 PNG viewport + 5 PNG konten penuh (`-scrolled.png`) | Diverifikasi utuh |
| **430×932** | Regular (pad 20); iPhone (44/34) | 5 PNG viewport (`-100pct.png`) | 5 PNG viewport (`-200pct-stress.png`) | Diverifikasi utuh |

Total: **50 berkas PNG verifikasi** dihasilkan dan diperiksa melalui visual inspection.

### Kondisi Stress Test 200%
- Nama penghuni panjang: `Muhammad Nur Alamsyah Pratama bin Abdullah`
- Nominal panjang: `Rp12.345.678`
- Username panjang pada Login: `pengelola kamartha nama panjang`
- Pembesaran font node teks 200% (bukan zoom transform seluruh frame).

### Temuan Visual dan Perilaku Layout

1. **Pemecahan Kata pada 320 px / 200%**:
   - Pada judul header tertentu (mis. "Tinjau pembayaran", "Detail kamar") dan label navbar pada lebar 320 px dengan skala teks 200%, kata dapat membungkus antar-baris (misal: "Bera / nda", "Kama / r", "Tagih / an", "Pem- / bayaran").
   - **Catatan Desain**: Teks tidak terpotong atau keluar batas frame (zero horizontal overflow); Auto Layout memperbesar tinggi header/navbar secara dinamis. Namun pemisahan suku kata ini adalah konsekuensi matematis dari ruang kolom 72–80 px pada font 26–48 px. Implementasi Flutter disarankan mendukung `hyphens: auto` atau penyesuaian label singkat jika diperlukan.
2. **Nama dan Nominal Panjang**:
   - Nama panjang `Muhammad Nur Alamsyah Pratama bin Abdullah` membungkus bersih dalam kartu kamar dan rincian alokasi.
   - Nominal `Rp12.345.678` pada total uang diterima membungkus menjadi dua baris pada 320 px / 200% tanpa ada digit yang terpotong.
3. **Pasangan Rincian & Separator**:
   - Pasangan label dan nilai pada rincian penerimaan dan alokasi tersusun dalam baris horizontal mandiri sehingga label tidak bergeser dari nilainya.
   - Garis pemisah mengikuti lebar kelompok (`fill width`).
4. **State Awal Pembayaran**:
   - Checkbox konfirmasi penerimaan uang tetap kosong / unchecked pada state awal.
   - Tombol simpan pembayaran tetap disabled dengan gaya warna yang sesuai.
5. **Footer Tinjau Pembayaran**:
   - Footer aksi diletakkan di akhir aliran konten gulir (`Footer tinjau · akhir konten gulir`), sehingga pada viewport pendek dan teks besar, seluruh data alokasi dan checkbox dapat digulir dan dioperasikan tanpa tertutup tombol tetap.

---

## Batas klaim verifikasi

Harap diperhatikan batas lingkup verifikasi desain ini:
- **Inspeksi Node & Render Statis**: Membuktikan struktur Auto Layout, constraints, hierarki pembungkusan teks, dan tampilan statis pada posisi gulir awal serta konten penuh.
- **Simulasi Ukuran Teks**: Membuktikan bahwa frame tidak mengalami overflow horizontal ketika node teks diperbesar 200%.
- **Belum Teruji**: Pengoperasian gulir interaktif, klik prototipe, interaksi fokus input, perilaku keyboard virtual, kompatibilitas browser engine (Blink/WebKit), dan pengujian UAT pada perangkat fisik nyata **belum diuji** dan berada di luar cakupan FigCraft.

---

## Daftar pengujian Flutter Web pada perangkat nyata

Daftar berikut wajib dijalankan oleh tim implementasi sebelum rilis:

1. **Perangkat & Browser**:
   - Chrome pada Android nyata (dengan navigasi gesture dan 3-tombol).
   - Safari pada iPhone nyata (dengan Dynamic Island / notch dan home bar).
2. **Orientasi & Viewport**:
   - Pengujian portrait dan landscape.
   - Viewport pendek (mis. perangkat lawas atau saat toolbar URL browser muncul penuh).
3. **Aksesibilitas Teks**:
   - Ukuran teks sistem 100%, 150%, dan 200% melalui pengaturan OS (Android Font Size / iOS Dynamic Type).
   - Pengujian pembaca layar (TalkBack / VoiceOver) pada tombol kembali, checkbox, dan nominal.
4. **Interaksi Keyboard**:
   - Keyboard virtual terbuka pada field Username dan Password (memastikan tombol Masuk dan link Lupa Password tetap dapat dijangkau).
   - Keyboard terbuka pada input nominal dan tanggal di formulir pembayaran.
5. **Navigasi & State**:
   - Tombol kembali (Back Button) mengikuti riwayat alur contextual, bukan hardcode ke Beranda.
   - Checkbox wajib dicentang sebelum tombol Simpan Pembayaran berubah menjadi aktif.
