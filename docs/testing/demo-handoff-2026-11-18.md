# KAMARTHA — demo lokal

Demo pertama menunjukkan alur pengelola dan pratinjau Excel dengan database
lokal khusus presentasi. WA tampil sebagai prototipe uji yang nonaktif.

## Menjalankan demo

Pastikan port 8001 dan 8081 kosong. Dari root workspace jalankan:

```powershell
backend\.venv\Scripts\python.exe ops\local_demo.py --database kamartha_demo_presentation --port 8001 --origin http://localhost:8081
```

Pastikan terminal menampilkan nama database tersebut. Skrip memeriksa PostgreSQL
lokal, menjalankan migrasi pada database demo, dan memakai Storage sementara.
Gunakan kode setup lokal dari konfigurasi privat jika browser memintanya.

Bila belum ada hasil build, jalankan dari folder `frontend`:

```powershell
flutter build web --release --no-web-resources-cdn --dart-define=API_URL=http://localhost:8001/api/v1
```

Kembali ke root dan jalankan di terminal lain:

```powershell
backend\.venv\Scripts\python.exe -m http.server 8081 --bind 127.0.0.1 --directory frontend/build/web
```

Buka <http://localhost:8081>. Build ini memuat CanvasKit dari server lokal.
Setelah selesai, tekan Ctrl+C di terminal server
berkas dan backend. Database demo dapat dipakai lagi.

## Tes APK Android debug lewat USB

Sambungkan HP, aktifkan USB debugging, dan izinkan komputer ini di HP.
Backend debug memakai PostgreSQL sekali pakai dan WA nonaktif. Jalankan dari
root workspace setelah memastikan port 8001 kosong:

```powershell
backend\.venv\Scripts\python.exe ops\test_postgres.py --android-demo
```

Build dari folder `frontend`, lalu dari root cek perangkat dan teruskan port:

```powershell
flutter build apk --debug --dart-define=API_URL=http://127.0.0.1:8001/api/v1
```

```powershell
& D:/dev/android-sdk/platform-tools/adb.exe devices -l
& D:/dev/android-sdk/platform-tools/adb.exe reverse tcp:8001 tcp:8001
& D:/dev/android-sdk/platform-tools/adb.exe install -r frontend/build/app/outputs/flutter-apk/app-debug.apk
```

Buka KAMARTHA di HP dan gunakan akun database debug. Jika perlu setup awal,
isi kode setup lokal dari konfigurasi privat. Bisa memakai
`KAMARTHA_ANDROID_SETUP_CODE` jika kode lokal belum disiapkan. Sesi Android debug disimpan
di memori. Menutup proses aplikasi memerlukan login ulang.

Setelah tes, hentikan backend dengan Ctrl+C dan hapus penerusan port dengan
`adb reverse --remove tcp:8001`. Menghentikan backend sekaligus membuang
database demo sekali pakai.

## Urutan presentasi

1. Masuk dan buka formulir kamar. Tunjukkan tipe Standar dan pilihan kapasitas
   1 atau 2. Kembali tanpa menyimpan.
2. Buka **Menu → Data awal**. Di database demo, simpan tanggal batas yang
   sesuai periode contoh. Pilih **Impor Excel**, buka pratinjau workbook v2,
   dan berhenti di pratinjau. Untuk contoh v2 lima kamar, pakai 2026-11-12.
3. Jelaskan validasi per baris, konflik existing, dan invoice periode berjalan
   yang tetap tercatat saat lunas. Konfirmasi hanya menghasilkan draft.
   Finalisasi terpisah. Draft utama yang belum lengkap perlu pilihan kamar,
   penanggung jawab, dan penghuni dari pengelola sebelum impor utama.
4. Tunjukkan **WA otomatis (uji)** dalam keadaan nonaktif. Pengujian
   terisolasi dapat membuktikan jadwal dan logika duplikasi. Pengiriman nyata
   perlu uji di HP penerima.

## Uji WA nyata setelah disetujui

Siapkan nomor pengirim, penerima, dan invoice uji melalui konfigurasi lokal
privat. Gunakan database demo ACTIVE yang diizinkan. Pastikan API dan worker
menunjuk database itu secara eksplisit. Isi allowlist API, worker, dan bridge
dengan nomor yang sama dalam format digit internasional `62…`. Isi token
bridge yang sama pada API, worker, dan bridge lewat konfigurasi privat.

1. Dari `whatsapp`, jalankan `node --env-file=.env bridge.mjs` dengan Chrome
   lokal. Default bridge adalah loopback port 3001. Simpan sesi dan ledger
   di direktori privat dan persisten.
2. Dari `backend`, jalankan
   `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001`
   dengan profil lokal, origin `http://localhost:8081`, dan WA aktif pada
   konfigurasi demo privat. Scan QR dengan HP pengirim.
3. Dari `backend`, jalankan satu
   `.\.venv\Scripts\python.exe -m app.modules.reminders.worker` dengan
   konfigurasi yang sama. Jadwal mulai pukul 09.00 WITA dan dapat menyusul
   pada hari yang sama. Worker dapat membuat invoice mendatang. Invoice
   tersebut baru dapat dikirimi pesan setelah disetujui dan masuk allowlist.
4. Konfirmasi kedua pesan pada HP penerima dan cek riwayat. SENT berarti
   server WA menerima. UNKNOWN tidak dikirim ulang otomatis.
5. Hentikan worker dahulu dengan Ctrl+C dan pastikan terminal kembali ke
   prompt. Baru hentikan bridge, backend, dan server berkas.

`WHATSAPP_ALLOW_DEMO_DATE` default false. Aktifkan hanya untuk uji tanggal
yang disetujui. Run manual dapat mengirim pesan nyata dan memakai slot
deduplikasi yang sama dengan jadwal otomatis.

## Bukti pengujian

- `backend\.venv\Scripts\python.exe ops\test_postgres.py tests -q --tb=short`:
  208 tes dan 38 subtes lulus pada PostgreSQL loopback sekali pakai. Termasuk
  privilege migration 0008, backup/restore isi reminder, impor v2, persaingan
  dua worker, dan rekonsiliasi ack. ACL direktori Windows dikecualikan dari
  round-trip fixture. Fungsi proteksi backup operasional tetap dipakai.
- `flutter test --reporter expanded`: 177 lulus. Analyzer SDK aktif
  melaporkan 30 info deprecation Material tanpa warning/error.
  `pubspec.lock` tetap sama.
- `npm test`: dua tes ledger lulus dengan transport tiruan.
- Release web tanpa CDN berhasil. Browser smoke impor dengan API sintetis
  lulus di 320 × 568, 390 × 844, dan 800 × 360. Konfirmasi di browser memakai
  respons tiruan; perubahan draft diuji terpisah pada PostgreSQL terisolasi.
- Browser WA dengan status sintetis nonaktif dan tombol perbarui lulus di
  320 × 568, 390 × 844, dan 1280 × 900.
- Smoke FigCraft lengkap berhenti pada 320 × 568 karena Escape tidak menutup
  dialog perpanjangan kontrak setelah input diedit. Lihat audit AFTER 014.
- QR nyata, penerimaan pesan di HP, build container, dan deployment belum
  diverifikasi. Workspace ini tidak menyediakan Docker.
