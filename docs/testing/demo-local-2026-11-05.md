# Demo lokal login, registrasi, dan dashboard

Tanggal verifikasi: 5 November 2026, waktu lokal Asia/Makassar.
Lingkungan: PostgreSQL lokal, database uji `kamartha_test`, API lokal, Flutter Web release.
Database pengembangan `kamartha_dev` tidak diubah dan tidak direset.

## Alamat dan akun demo

- Aplikasi: <http://localhost:8081>
- API: <http://localhost:8001/api/v1>
- Username: `pengelola`
- Password: `DemoPass2026!`

Akun di atas hanya untuk demo lokal. Jangan memakai password ini di lingkungan
production.

## Alur yang dapat diperlihatkan

1. Buka <http://localhost:8081>. Halaman masuk tampil.
2. Klik **Lihat registrasi awal** untuk memperlihatkan halaman registrasi.
   Registrasi akun pertama sudah dipakai, jadi halaman menyatakan registrasi
   sudah ditutup. Ini sesuai aturan satu pengelola.
3. Kembali, lalu masuk dengan akun demo.
4. Dashboard tampil dalam **Mode Persiapan**. Transaksi belum dibuka.
5. Buka ikon pengelola di kanan atas, lalu **Keluar**.
6. Setelah keluar, buka `/#/home`; aplikasi mengembalikan ke halaman masuk.

## Hasil verifikasi otomatis

Perintah browser QA dijalankan pada viewport 390x844 dengan Chrome headless.
Hasil akhir:

```text
PASS registration -> login -> preparation dashboard -> reload -> logout -> protected route
PASS wrong password rejected; first-account registration closes; preparation has no billing writes
PASS screenshots at 320/390/430/1280; no document overflow or uncaught JavaScript errors
```

Yang diperiksa:

- Registrasi akun pertama mengembalikan HTTP 201.
- Password salah mengembalikan HTTP 401 dan pesan ditampilkan.
- Login benar mengembalikan HTTP 200 dan membuka dashboard.
- Dashboard Mode Persiapan tidak memanggil `/billing/synchronize`.
- Sesi bertahan setelah halaman dimuat ulang.
- Logout mengembalikan HTTP 200 dan menghapus akses.
- Rute terlindungi mengembalikan pengguna ke halaman masuk.
- Halaman registrasi menolak akun kedua.
- Tidak ada overflow horizontal pada 320, 390, 430, dan 1280 piksel.
- Tidak ada error JavaScript yang tidak tertangani.

Bukti tangkapan layar ada di
[`evidence/2026-11-05-auth-demo/`](evidence/2026-11-05-auth-demo/):

- `01-login-390.png`
- `02-registrasi-terisi-390.png`
- `03-dashboard-320.png`
- `03-dashboard-390.png`
- `03-dashboard-430.png`
- `03-dashboard-1280.png`
- `04-registrasi-ditutup.png`

## Tes otomatis yang dijalankan

- Backend: `tests/unit/test_local_demo.py` — 9 lulus.
- Frontend: `widget_test.dart`, `operations_test.dart`,
  `initialization_flow_test.dart` — 15 lulus.
- Browser QA: 1 alur utama lulus dengan bukti di atas.

Tes ini terarah. Suite lengkap, UAT, audit aksesibilitas manual, pengujian
Safari, dan pengujian pembayaran belum dijalankan.

## Cara menjalankan ulang

Dari akar repositori:

```powershell
backend\.venv\Scripts\python.exe ops\local_demo.py `
  --database kamartha_test --allow-test-database --reuse-test-database `
  --port 8001 --origin http://localhost:8081
```

Di terminal lain:

```powershell
python -m http.server 8081 --bind 127.0.0.1 --directory frontend\build\web
```

Build web harus memakai CanvasKit lokal agar tidak menunggu CDN:

```powershell
cd frontend
flutter build web --release --no-web-resources-cdn `
  --dart-define=API_URL=http://localhost:8001/api/v1
```

## Batas yang harus disebut

- Tampilan masih UI Flutter saat ini, belum disinkronkan ke desain FigCraft.
- Demo memakai database uji `kamartha_test`, bukan database produksi.
- Lampiran memakai `FakeStorage`; Supabase Storage belum diuji live.
- Modul pembayaran, laporan, dan operasi lain belum diperlihatkan pada demo ini.
- Registrasi pertama hanya sekali. Untuk mengulang registrasi dari nol, akun
  demo pada `kamartha_test` harus dihapus terlebih dahulu. Jangan menghapus
  data `kamartha_dev`.
