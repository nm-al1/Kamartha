# Supabase staging setup

Tanggal: 2026-11-05
Status: **provisioned, lolos smoke, dan akun pengelola pertama dibuat** pada
2026-11-05. Project Supabase berisi 22 tabel schema `kamartha`, role
`kamartha_runtime`, bucket privat `kamartha-files`, dan satu akun `pengelola`.
Login browser penuh dan backup belum diuji.

## Hasil 2026-11-05

| Langkah | Hasil |
|---|---|
| Project baru | kosong sebelum migrasi: 0 tabel `public`, tanpa schema `kamartha` |
| Owner login | lolos lewat shared pooler, `current_user = postgres` |
| Role runtime | `kamartha_runtime` dibuat, login lewat `kamartha_runtime.<ref>` lolos |
| Migrasi | `0006_seed_permissions`, 22 tabel |
| Least privilege | runtime tidak bisa `CREATE` schema dan tidak bisa `DELETE` lampiran |
| `anon`/`authenticated` | tanpa akses schema `kamartha` |
| Bucket | `kamartha-files` dibuat privat, batas 2 MB, MIME JPG/PNG/PDF |
| Smoke | health, database runtime, storage tulis/baca, bucket privat, storage hapus: lolos |
| Akun pengelola | `pengelola` dibuat lewat `/auth/setup`; mode `PREPARATION` |
| Auth smoke | csrf, setup, login, `/auth/me`, logout, sesi ditolak setelah logout: lolos |
| Unit test | 110 lolos, 38 subtest lolos |
| Sisa objek uji | 0 |

Temuan saat smoke: CDN Supabase menyajikan ulang objek yang sudah dihapus
(`cf-cache-status: HIT`). Adapter sekarang menambahkan nonce `?v=<uuid>` pada
setiap `GET` dan memetakan bodi `400 not_found` Supabase menjadi `404`.

## Ruang lingkup

Supabase dipakai hanya untuk:

- PostgreSQL terkelola.
- Storage privat (bucket `kamartha-files`).

Tidak dipakai: Supabase Auth, Data API/PostgREST, Realtime, Edge Functions.
Flutter tidak pernah memegang kredensial database atau service key.

## Profil

Semua konfigurasi ada di satu berkas, `backend/.env`, dibagi menjadi blok
bertag. Satu baris `APP_PROFILE` memilih blok yang aktif.

| Profil | Database | Storage | Aktif saat |
|---|---|---|---|
| `local` | PostgreSQL lokal `kamartha_dev` | `FakeStorage` (hilang saat restart) | `APP_PROFILE=local` |
| `supabase` | Supabase session pooler | bucket privat | `APP_PROFILE=supabase` |

Tidak ada fallback otomatis. Tag:

| Tag | Isi |
|---|---|
| 1 | `APP_PROFILE` |
| 2 | `LOCAL_*` |
| 3 | `SUPABASE_*` (database, origin, rahasia, kode setup) |
| 4 | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `STORAGE_BUCKET` |
| 5 | contoh URL, hanya komentar |

Profil `local` tidak pernah membaca blok Storage Supabase, jadi demo offline
tetap berjalan walau service key sudah terisi.

## Berkas

- `backend/.env` — gitignored, diisi manual. Jangan kirim isinya ke chat,
  screenshot, atau commit.
- `ops/supabase_setup.py` — provisioning role, migrasi, grant, bucket.
- `ops/supabase_smoke.py` — verifikasi health, database runtime, dan Storage.
- `ops/grant_runtime.sql` — grant/revoke role runtime.

## Langkah

1. Isi blok `SUPABASE_*` di `backend/.env`. Nilai yang wajib:

   | Key | Keterangan |
   |---|---|
   | `SUPABASE_MIGRATION_DATABASE_URL` | URL PostgreSQL pooler dengan role migrasi, kata sandi dari konfigurasi privat, dan `sslmode=require` |
   | `SUPABASE_DATABASE_URL` | role `kamartha_runtime.<REF>`, host pooler sama, `sslmode=require` |
   | `SUPABASE_SERVICE_KEY` | service role key, hanya di backend |

   Nilai berikut sudah dibuat: `SUPABASE_ENVIRONMENT`, `SUPABASE_APP_ORIGIN`,
   `SUPABASE_URL`, `SUPABASE_SETUP_CODE_HASH`, `SUPABASE_IP_HASH_SECRET`,
   `SUPABASE_SETUP_CODE`, dan `STORAGE_BUCKET`.

   Password dengan `@ : / ? #` harus di-URL-encode. Kode setup Supabase berbeda
   dari kode demo lokal; baca `SUPABASE_SETUP_CODE` saat mendaftarkan pengelola
   pertama.

2. Pastikan project Supabase masih kosong. Skrip berhenti sendiri bila schema
   `kamartha` sudah ada, kecuali dijalankan dengan `--allow-existing`.

3. Provisioning:

   ```powershell
   backend\.venv\Scripts\python.exe ops\supabase_setup.py
   ```

   Skrip akan:
   - membuat atau memperbarui role runtime dan password-nya;
   - menjalankan Alembic sampai `head`;
   - menjalankan `ops/grant_runtime.sql` (termasuk `CONNECT`);
   - memeriksa runtime tidak bisa `CREATE` dan tidak bisa `DELETE` lampiran;
   - memastikan `anon`/`authenticated` tidak punya akses schema `kamartha`;
   - membuat bucket privat dengan batas 2 MB dan MIME JPG/PNG/PDF.

4. Smoke test:

   ```powershell
   backend\.venv\Scripts\python.exe ops\supabase_smoke.py
   ```

   Objek uji `smoke/<uuid>.png` dibuat lalu dihapus. Tidak ada data bisnis yang
   ditulis. Smoke memaksa profil Supabase tanpa mengubah `APP_PROFILE`.

5. Akun pengelola pertama (sekali saja):

   ```powershell
   backend\.venv\Scripts\python.exe ops\supabase_auth_smoke.py --dry-run
   backend\.venv\Scripts\python.exe ops\supabase_auth_smoke.py
   ```

   Pada terminal interaktif skrip meminta username dan password lewat prompt.
   Pada eksekusi non-interaktif password dibuat acak dan disimpan di
   `backend/.env.manager.local` (gitignored); password tidak dicetak. `--dry-run`
   hanya memeriksa koneksi, hash kode setup, dan ketersediaan setup. Smoke
   memakai TestClient dengan origin HTTPS, jadi cookie `Secure` ikut diuji.
   Setelah akun pertama ada, `/auth/setup` tertutup otomatis.

6. Untuk memakai profil Supabase pada aplikasi, ubah satu baris:

   ```env
   APP_PROFILE=supabase
   ```

   Kembalikan ke `local` untuk demo offline.

## Yang belum diverifikasi

- Login dan registrasi lewat **browser** pada profil Supabase. Alur API sudah
  lolos lewat TestClient dengan origin HTTPS, tetapi cookie `Secure` belum diuji
  di browser sungguhan; uji penuh menunggu origin HTTPS.
- Alur bisnis penuh di atas database Supabase (baru health, auth, dan query
  runtime).
- Backup/restore, retensi paket gratis, dan perilaku project saat pause.

## Catatan keamanan

- `SUPABASE_SERVICE_KEY` melewati RLS; hanya boleh ada di backend.
- `backend/.env.manager.local` berisi password pengelola pertama dan sudah
  tertutup pola `.env.*` di `.gitignore`. Jangan commit atau unggah.
- Setelah akun pertama dibuat, `/auth/setup` tertutup. `SUPABASE_SETUP_CODE`
  tidak diperlukan lagi dan boleh dihapus dari `.env`.
- Password database owner sempat tercetak pada satu pemeriksaan terminal.
  Rotasi password database lalu perbarui kedua URL sebelum deploy publik.
- Runtime memakai `kamartha_runtime`, bukan `postgres`. Backend menolak username
  `postgres` saat `ENVIRONMENT=production`.
- Backend menolak `ENVIRONMENT=production` bila `APP_PROFILE` bukan `supabase`.
- Session pooler port `5432`. Transaction pooler port `6543` tidak dipakai karena
  mengubah semantik sesi dan advisory lock.
- Jangan menambahkan schema `kamartha` ke exposed schemas Supabase.
- `.gitignore` sudah menutup `.env` dan `.env.*` kecuali `.env.example`.
