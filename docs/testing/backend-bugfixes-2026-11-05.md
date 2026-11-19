# Regresi backend: lanjutan, saldo awal, dan Storage produksi

Tanggal: 5 November 2026. Acuan: `PRD.md` BR-17, BR-25, BR-39; `database.md` perlindungan data awal; kebijakan pengujian `agent.md`.

## Perubahan

- Eksekusi kontrak lanjutan dengan tanggal mulai di masa depan ditolak sebelum perubahan hunian/kontak. Ini bukan implementasi penjadwalan lanjutan. Kasus lanjutan yang berhasil diuji saat tanggal mulai tiba, dengan login ulang setelah jam uji dimajukan.
- Keluar terakhir yang akan membatalkan invoice `OPENING` ditolak atomik. Guard mencakup pembayaran lama nol, sebagian, dan penuh. Kontrak lama tetap dapat ditutup tanpa mengubah invoice saldo awal yang periodenya sudah dimulai.
- Produksi gagal dibuat jika URL atau service key Supabase Storage tidak lengkap. Penggunaan `FakeStorage` tetap tersedia hanya di development/test ketika Storage belum dikonfigurasi.

## Bukti RED

Delapan kasus regresi baru dieksekusi sebelum perubahan kode produksi: empat konfigurasi Storage tidak lengkap, satu lanjutan masa depan, dan tiga kasus pembatalan invoice saldo awal. Hasil: **8 gagal, 13 deselected** karena perilaku yang dituju, bukan kesalahan fixture.

- Produksi sebelumnya tidak menolak konfigurasi Storage tidak lengkap.
- Lanjutan masa depan sebelumnya merespons 201, bukan 422.
- Pembatalan invoice `OPENING` sebelumnya merespons 200, bukan 409.

Pengujian dipanggil melalui `.venv/Scripts/python.exe -` dan `pytest.main` dengan argumen:

```text
tests/unit/test_plumbing.py tests/integration/test_stage_c.py
-k "production_rejects_missing_durable_storage or future_continuation_leaves_current_occupancy or last_exit_cannot_cancel_finalized_opening_invoice"
-q --tb=short -p no:cacheprovider
```

## Verifikasi akhir

Satu kelompok verifikasi terarah dijalankan setelah perbaikan kode:

```text
tests/unit/test_plumbing.py
tests/unit/test_foundation.py::test_production_documentation_is_not_public
tests/integration/test_stage_c.py
tests/integration/test_stage_d.py::test_payment_allocates_exact_amount_replays_and_cancel_restores_balance
tests/integration/test_stage_d.py::test_attachment_validation_and_payment_link
-q --tb=short -p no:cacheprovider
--cov=app.main --cov=app.modules.leases.router --cov-report=term
```

Hasil: **24 passed, 1 warning**, 16,05 detik. Coverage gabungan dua modul yang diukur **81%** (`app.main` 90%, `leases.router` 79%), bukan coverage seluruh backend.

| Jaminan yang diperiksa | Bukti |
| --- | --- |
| Lanjutan masa depan ditolak tanpa mengubah hunian, kontak, invoice, jumlah kontrak, atau event lanjutan | Regresi PostgreSQL dalam `test_stage_c.py` |
| Lanjutan pada tanggal mulai tetap berhasil, termasuk riwayat pengganti dan tagihan pertama | Kasus lanjutan yang sudah ada, diperbarui tanggal eksekusinya |
| Invoice OPENING nol/sebagian/lunas tidak dapat dibatalkan lewat keluar terakhir; penolakan mengembalikan seluruh keadaan semula | Tiga parameter regresi PostgreSQL |
| Penutupan kontrak lama tidak diblokir jika invoice OPENING tetap aktif | Kasus positif PostgreSQL; saldo lama 200.000 dan sisa 500.000 tetap |
| Tagihan operasional mendatang tanpa pembayaran tetap dibatalkan; pembayaran Valid tetap menghalangi pengakhiran | Kasus keluar terakhir yang sudah ada |
| Produksi menolak konfigurasi Storage tidak lengkap; konfigurasi lengkap memilih adapter Supabase | Tes konfigurasi tanpa koneksi Storage |
| FakeStorage development/test, upload/link lampiran, pembayaran, replay idempotency, dan pembatalan pembayaran tetap bekerja | Tes plumbing dan dua kasus Stage D terarah |

Integrasi memakai PostgreSQL lokal `kamartha_test`, bukan SQLite. URL diambil dari konfigurasi lokal tanpa mencetak kredensial. Fixture menolak schema aplikasi yang sudah ada dan menggulung balik transaksi. Setelah tes, pemeriksaan baca mengonfirmasi schema `kamartha` dan tabel `public.alembic_version` tidak tersisa.

## Batas dan risiko

- Tidak menjalankan suite penuh, tes konkurensi baru, browser E2E, backup/restore, atau koneksi Supabase nyata.
- Pemilihan adapter pada tes konfigurasi bukan bukti bucket, kredensial, atau konektivitas Storage sudah valid.
- Kontrak yang telanjur dilanjutkan terlalu dini dan lampiran yang sudah hilang dari FakeStorage tidak diperbaiki otomatis. Data semacam itu memerlukan pemeriksaan terpisah.
- Produksi kini memerlukan konfigurasi Storage lengkap untuk startup. Development masih memakai penyimpanan sementara jika belum dikonfigurasi.
- Ada warning deprecation penggunaan `httpx` oleh Starlette TestClient; dependency tidak diganti dalam tugas ini.
- Frontend, desain, migrasi, dan database operasional tidak diubah. Tidak ada commit; Git tetap ditangani pengguna.
