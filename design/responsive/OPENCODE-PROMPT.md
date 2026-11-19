# Panduan Instruksi Implementasi OpenCode (Kamartha Flutter)

Dokumen ini berisi instruksi dan konteks lengkap bagi **OpenCode** untuk mengimplementasikan antarmuka aplikasi Kamartha ke dalam proyek Flutter (`frontend/`), berdasarkan hasil penyempurnaan desain FigCraft terbaru.

---

## 1. Berkas Acuan Desain & Panduan Teknis

- **Berkas Desain Utama (Wajib)**:  
  `design/kamartha-design-responsive.figcraft`  
  *(Path absolut: `C:/Users/nmal1/Desktop/KAMARTHA/design/kamartha-design-responsive.figcraft`)*  
  > [!IMPORTANT]
  > Jangan gunakan `design/kamartha-design.figcraft` (versi sebelum responsif) atau `design/kamartha-design-before-responsive.figcraft` (arsip cadangan). Gunakan hanya `kamartha-design-responsive.figcraft`.
  > OpenCode dapat mengakses dokumen ini melalui MCP FigCraft lokal port `47800` sebagaimana terkonfigurasi di `opencode.jsonc`.

- **Dokumentasi Handoff Teknis**:  
  [`design/responsive/HANDOFF-FLUTTER-WEB.md`](file:///C:/Users/nmal1/Desktop/KAMARTHA/design/responsive/HANDOFF-FLUTTER-WEB.md)  
  Berisi aturan lengkap mengenai `SafeArea`, `TextScaler`, keyboard management, dan pemetaan token.

- **Referensi Render Visual**:  
  Folder [`design/responsive/verified/`](file:///C:/Users/nmal1/Desktop/KAMARTHA/design/responsive/verified/)  
  *(Lihat berkas PNG dengan akhiran `-clean-nav.png`, `-floating-nav.png`, dan `-13px.png` sebagai acuan visual piksel nyata).*

- **Dokumen Bisnis & PRD**:  
  [`docs/design.md`](file:///C:/Users/nmal1/Desktop/KAMARTHA/docs/design.md) dan [`docs/PRD.md`](file:///C:/Users/nmal1/Desktop/KAMARTHA/docs/PRD.md).

---

## 2. Sistem Token Warna & Tipografi (100% Presisi Accomodio)

### Palet Warna
| Token | Hex | Kegunaan UI |
| --- | --- | --- |
| `primary_action` | `#FD3D18` | Tombol utama, tab navigasi aktif, aksi penting WhatsApp |
| `brand` | `#FA6921` | Logo Kamartha, swatch identitas header |
| `link` | `#FE4300` | Tautan kontekstual ("Lihat semua tagihan →", "Ubah", "Kelola") |
| `ink` | `#142039` | Judul layar, teks utama, angka nominal, nomor kamar, label |
| `secondary_text`| `#526079` | Subjudul, metadata, label/ikon navbar tidak aktif |
| `background` | `#F3F6F9` | Latar belakang seluruh halaman aplikasi |
| `surface` | `#FFFFFF` | Kartu, input formulir, modal bottom sheet, floating navbar |
| `border` | `#DCE3EB` | Garis tepi kartu, batas input formulir |
| `divider` | `#EEF2F6` | Garis pemisah tipis antar-item di dalam kartu |
| `success` | `#08964D` | Teks status Lunas / Dihuni (background: `#D5F5E5`) |
| `warning` | `#FE6507` | Teks status Perlu konfirmasi / Jatuh tempo (background: `#FFF3E0`) |
| `danger` | `#E53935` | Teks status Terlambat / Menunggak (background: `#FEE2E2`) |

### Tipografi (Font: Inter)
- **Display 30 px** (SemiBold): Nomor kamar utama (`ROOM-02`).
- **Heading 24 px** (SemiBold): Judul layar header (`Beranda`, `Kamar`, `Tagihan`, `Menu`).
- **Body 16 px** (Regular 400 & SemiBold 600): Isi utama, input formulir, label tombol.
- **Metadata 14 px** (Regular 400 & SemiBold 600): Penjelasan, status, tanggal, rincian biaya.
- **Navbar Label 13 px**: 
  - Item aktif: `FontWeight.w600` (SemiBold), warna `#FD3D18`.
  - Item tidak aktif: `FontWeight.w500` (Medium), warna `#526079`.

### Bentuk & Sudut (BorderRadius)
- Tombol utama: Tinggi min 48 px, `BorderRadius.circular(24)`
- Input formulir: Tinggi min 52 px, `BorderRadius.circular(12)`
- Kartu & panel daftar: `BorderRadius.circular(16)`
- Chip filter & lencana status: `BorderRadius.circular(999)`

---

## 3. Komponen Utama: Floating Capsule Navbar (Pill Nav)

Navigasi bawah menggunakan desain kapsul mengambang (*floating pill capsule*) pada 5 layar utama (`HOME-01`, `ROOM-01`, `INV-01`, `EXP-01`, `MENU-01`):

1. **Wadah Kapsul (*Floating Container*)**:
   - Tinggi kapsul: **64 logical px**, `BorderRadius.circular(32)`.
   - Lebar: Mengikuti lebar konten (`fill width`) dengan margin 16 px kiri & kanan (lebar 328 px pada layar 360 px).
   - Warna latar: Putih solid `Colors.white` (`#FFFFFF`).
   - Bayangan mengambang difus:
     ```dart
     boxShadow: [
       BoxShadow(
         color: Color(0x1F142039), // rgba(20, 32, 57, 0.12)
         blurRadius: 16.0,
         offset: Offset(0, 4),
       ),
     ]
     ```
   - Posisi mengambang: Diberi jarak 8 px dari konten di atasnya dan margin bawah 16 px di atas `SafeArea(bottom: true)`.

2. **Empat Tab & Ikon Vektor Superclean**:
   - **`Beranda`**: Ikon rumah bersiluet simetris dengan pintu lengkung di tengah (*door cutout*).
     - *State Aktif*: *Solid filled* oranye `#FD3D18`.
     - *State Inaktif*: *Outline* slate grey `#526079` (1.8 px).
   - **`Kamar`**: Ikon ranjang hotel tampak depan (*front-facing bed* gaya Lucide) dengan sandaran kepala (*headboard*), kasur (*mattress*), dan kaki ranjang.
   - **`Tagihan`**: Lembar dokumen tagihan bersudut bulat (*rounded invoice document*) dengan 3 garis rincian bersih (tanpa gerigi zig-zag kasar).
   - **`Menu`**: Tiga garis horizontal simetris dengan ujung membulat halus (*round stroke caps*).

---

## 4. Aturan Responsivitas & Platform (Android & iOS)

1. **Edge-to-Edge & Safe Area**:
   - Selalu gunakan `SafeArea` untuk membungkus area layar/navbar.
   - Jangan pernah melakukan *hardcode* padding status bar atau tinggi home indicator.
2. **Keyboard Management**:
   - Gunakan `Scaffold(resizeToAvoidBottomInset: true)`.
   - Pastikan field input formulir menggunakan `Scrollable.ensureVisible(context)` saat mendapatkan fokus agar tidak tertutup keyboard virtual.
3. **Penghormatan Text Scaling (Accessibility)**:
   - Dukung `MediaQuery.textScalerOf(context)` hingga pembesaran 200%.
   - Dilarang mematikan scaling secara global atau memaksakan `FittedBox` yang memotong angka nominal uang atau nama penghuni panjang.
4. **Navigasi Kontekstual**:
   - Tombol kembali (Back Button) berupa tombol transparan 48×48 dengan ikon panah kiri outline 24×24, wajib mengikuti riwayat navigasi pengguna (*contextual history*), bukan selalu diarahkan ke Beranda.
5. **Struktur Konten Gulir**:
   - Area konten scroll mengisi ruang tersisa di antara header dan navbar (`Expanded`).
   - Pada layar Tinjau Pembayaran (`PAY-02`), tombol aksi berada di akhir aliran scroll agar formulir tetap dapat dioperasikan pada layar kecil saat font diperbesar.

---

## 5. Langkah Pengerjaan yang Disarankan untuk OpenCode

1. **Pemeriksaan Proyek**: Buka folder `frontend/`, periksa `pubspec.yaml`, dan identifikasi struktur tema/widget yang sudah ada.
2. **Setup Tema & Token**: Selaraskan token warna Accomodio dan font Inter di `ThemeData`.
3. **Bangun Widget Floating Capsule Navbar**: Buat komponen `KamarthaFloatingNavBar` dengan 4 tab, ikon vektor bersih, dan bayangan mengambang.
4. **Implementasikan Layar Utama**: Terapkan pada layar `Beranda`, `Kamar`, `Tagihan`, dan `Menu` dengan Auto Layout yang adaptif.
5. **Verifikasi Tampilan**: Cocokkan hasil build dengan ekspor verifikasi di `design/responsive/verified/`.


---

## 6. Sistem Identitas Brand & Logo Kamartha

Logo resmi Kamartha dirancang dengan filosofi **"Kamar"** (hunian/pondasi ruangan) dan **"Artha"** (kemakmuran/keteraturan finansial). Monogram arsitektural **"K"** menggabungkan pilar tegak (keamanan & stabilitas kamar kos) dengan sayap ganda bersudut atap dan akselerasi pertumbuhan (keteraturan pembukuan & masa depan kos yang sehat).

### Berkas Aset Logo Siap Pakai
Seluruh aset logo telah diekspor dalam format SVG vektor dan PNG resolusi tinggi di [`frontend/assets/logo/`](file:///C:/Users/nmal1/Desktop/KAMARTHA/frontend/assets/logo/) dan [`design/exports/logo/`](file:///C:/Users/nmal1/Desktop/KAMARTHA/design/exports/logo/):
- `app-icon.svg` & `app-icon-512.png`: Ikon aplikasi utama (squircle gradient oranye `#FD3D18` → `#FA6921` → `#EF3A0E` dengan monogram K putih).
- `app-icon-inverted.svg`: Ikon versi permukaan terang (squircle putih dengan monogram K oranye).
- `app-icon-dark.svg`: Ikon versi permukaan gelap (squircle navy slate `#142039` dengan monogram K putih).
- `logo-mark.svg` & `logo-mark-white.svg`: Vektor monogram K berdiri sendiri (standalone).
- `logo-horizontal.svg`: Lockup horizontal lengkap (badge ikon 56×56 + wordmark "kamartha" 28px Bold + tagline "Kelola kos, lebih teratur." 12px) untuk tema terang / web app.
- `logo-horizontal-dark.svg`: Lockup horizontal untuk tema gelap / dark mode.
- `logo-stacked.svg`: Lockup vertikal / stacked (badge di atas teks) untuk layar login dan splash.

### Penempatan pada Antarmuka Layar
1. **Layar Masuk (`AUTH-01`) [401]**:
   - Wadah badge: 56×56 squircle putih (`cornerRadius: 14.0`).
   - Ikon logo di dalam: Vektor Monogram K 30×30 gradien oranye.
   - Di bawah badge: Teks `kamartha` (24px, Bold, `#FFFFFF`) dan tagline `Kelola kos, lebih teratur.` (14px, Medium, `#FFFFFF`).
2. **Layar Beranda (`HOME-01`) [421]**:
   - Header oranye memiliki lockup horizontal terpadu: Badge putih 32×32 (`cornerRadius: 9.0`) berisi Monogram K 18×18 gradien oranye, berdampingan dengan teks `kamartha` (26px, Bold, `#FFFFFF`).
3. **Komponen Master FigCraft**:
   - Halaman `Components · Kamartha` (Page 2276) memuat frame showcase `Brand · Logo Kamartha` [3722] pada koordinat `x=480.0, y=440.0`.
