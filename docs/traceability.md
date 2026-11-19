# Keterlacakan Kamartha

| Metadata | Nilai |
| --- | --- |
| Versi | 1.0 |
| Tanggal | 31 Oktober 2026, WITA |
| Acuan | PRD/architecture/database/uml/design/test-plan versi 1.0 |
| Status | Pemetaan rancangan; implementasi dan bukti pengujian belum diverifikasi |

Simpan sebagai `docs/traceability.md`. Gunakan ID KF/UC/BR/AC yang sama dalam issue, test, PR dan laporan. Modul/tabel/route di bawah adalah calon tanggung jawab dari rancangan; bukan klaim kode sudah ada. Isi path dan bukti aktual setelah memeriksa repo OpenCode. Mockup raster bukan bukti fitur selesai dan sumber diagram UML belum otomatis merevisi proposal Word.

## 1. Peta fitur, use case dan layar

| KF | UC utama | Modul | Layar | Tabel inti |
| --- | --- | --- | --- | --- |
| KF-01 | UC-02 | rooms | ROOM-01/02 | rooms, leases, occupancies |
| KF-02 | UC-03 | residents | RES-01/02 | residents, occupancies |
| KF-03 | UC-04 | leases | LEASE-01/02, ROOM-02 | leases, packages, occupancies, responsible_history |
| KF-04 | UC-05 | billing | HOME-01, INV-01/02 | invoices, leases |
| KF-05 | UC-05 | payments, attachments | PAY-01/02/03, INV-02 | payments, payment_allocations, attachments |
| KF-06 | UC-06 | expenses, attachments | EXP-01/02 | expenses, expense_audits, attachments |
| KF-07 | UC-08 | reports | REPORT-01 | payments, payment_allocations, expenses |
| KF-08 | UC-01 | auth | AUTH-01/03, MENU-01 | managers, sessions, login_windows |
| KF-09 | UC-07 | dashboard, billing | HOME-01 | rooms, occupancies, leases, invoices |
| KF-10 | UC-09 | messaging | WA-01 | residents, responsible_history, payments, invoices |
| KF-11 | UC-10 | initialization | INIT-01 | initialization_records/finalizations, app_settings, data OPENING |
| KF-12 | UC-11 | auth | AUTH-02 | managers, app_settings |

## 2. Setiap AC ke skenario dan calon implementasi

BB-xx adalah keluarga skenario di test-plan.md, bukan satu assertion tunggal. Acuan KF/UC diambil dari PRD; AC-36 tidak menyebut UC eksplisit dan dieksekusi pada alur pembayaran/pengeluaran yang memakai lampiran.

| AC | Acuan PRD | Black box | Modul; layar; diagram; data | Path/test/bukti aktual |
| --- | --- | --- | --- | --- |
| AC-01 | KF-12, UC-11 | BB-01 beserta variannya | auth; AUTH-02; A-01/ST-03; managers/app_settings | Belum diverifikasi |
| AC-02 | KF-08, UC-01 | BB-02 beserta variannya | auth; AUTH-01; A-01; sessions/login_windows | Belum diverifikasi |
| AC-03 | KF-08, UC-01 | BB-03 beserta variannya | auth; AUTH-03/MENU-01; C-04; managers/sessions | Belum diverifikasi |
| AC-04 | KF-01, UC-02 | BB-04 beserta variannya | rooms; ROOM-01/02; C-01; rooms | Belum diverifikasi |
| AC-05 | KF-02, UC-03 | BB-05 beserta variannya | residents/messaging; RES-01/02; C-01/S-04; residents | Belum diverifikasi |
| AC-06 | KF-03, UC-04 | BB-06 beserta variannya | leases/billing; LEASE-01; A-02/C-01; packages/leases | Belum diverifikasi |
| AC-07 | KF-03, UC-04 | BB-07 beserta variannya | leases; LEASE-01; A-02/S-01; occupancies/responsible_history | Belum diverifikasi |
| AC-08 | KF-03, UC-04 | BB-08 beserta variannya | leases/billing; LEASE-01; A-02/S-01; leases/occupancies/invoices | Belum diverifikasi |
| AC-09 | KF-03, UC-04 | BB-09 beserta variannya | leases; LEASE-01/02; A-02/C-01; leases/occupancies | Belum diverifikasi |
| AC-10 | KF-03, UC-04 | BB-10 beserta variannya | leases; LEASE-02/ROOM-02; A-03; occupancies | Belum diverifikasi |
| AC-11 | KF-03, UC-04 | BB-11 beserta variannya | leases/messaging; LEASE-02/WA-01; A-03/S-04; responsible_history | Belum diverifikasi |
| AC-12 | KF-03, UC-04 | BB-12 beserta variannya | rooms/leases; ROOM-02/HOME-01; A-03/ST-01; leases/occupancies | Belum diverifikasi |
| AC-13 | KF-03, UC-04 | BB-13 beserta variannya | leases/rooms; LEASE-02; A-03; occupancies/leases/invoices | Belum diverifikasi |
| AC-14 | KF-03, UC-04 | BB-14 beserta variannya | leases; LEASE-02; A-03/C-01; leases/business_events | Belum diverifikasi |
| AC-15 | KF-04, UC-05 | BB-15 beserta variannya | billing; HOME-01/INV-01; A-04; invoices | Belum diverifikasi |
| AC-16 | KF-04, UC-05 | BB-16 beserta variannya | billing/dashboard; HOME-01/INV-01; A-04; leases/invoices | Belum diverifikasi |
| AC-17 | KF-04, UC-05 | BB-17 beserta variannya | billing; LEASE-01/INV-02; A-04; leases/invoices | Belum diverifikasi |
| AC-18 | KF-04/05, UC-04/05 | BB-18 beserta variannya | leases/billing; LEASE-02; A-03/A-04; leases/invoices/payments | Belum diverifikasi |
| AC-19 | KF-05, UC-05 | BB-19 beserta variannya | payments/reports; PAY-01/03; A-05/S-02; payments/payment_allocations | Belum diverifikasi |
| AC-20 | KF-05, UC-05 | BB-20 beserta variannya | payments; PAY-01/02; A-05/S-02; payments/invoices | Belum diverifikasi |
| AC-21 | KF-05, UC-05 | BB-21 beserta variannya | billing; INV-02; ST-01; invoices/payment_allocations | Belum diverifikasi |
| AC-22 | KF-05, UC-05 | BB-22 beserta variannya | payments; PAY-01/03; A-05/S-02; idempotency_records/payments | Belum diverifikasi |
| AC-23 | KF-05/07, UC-05/08 | BB-23 beserta variannya | payments/reports; PAY-03; ST-02/S-02; payments | Belum diverifikasi |
| AC-24 | KF-05, UC-05 | BB-24 beserta variannya | payments/leases; PAY-03/LEASE-02; A-05; payments/occupancies | Belum diverifikasi |
| AC-25 | KF-11, UC-10 | BB-25 beserta variannya | initialization/payments; INIT-01/PAY-03; A-01/A-05; invoices/payments | Belum diverifikasi |
| AC-26 | KF-11, UC-10 | BB-26 beserta variannya | initialization/billing; INIT-01; A-01/A-04; occupancies/invoices | Belum diverifikasi |
| AC-27 | KF-11, UC-10 | BB-27 beserta variannya | initialization; INIT-01; A-01; initialization_records | Belum diverifikasi |
| AC-28 | KF-11, UC-10 | BB-28 beserta variannya | initialization; INIT-01; A-01/ST-03; app_settings/initialization_finalizations | Belum diverifikasi |
| AC-29 | KF-06/07, UC-06/08 | BB-29 beserta variannya | expenses/reports; EXP-01/02; A-06/C-03; expenses | Belum diverifikasi |
| AC-30 | KF-07, UC-08 | BB-30 beserta variannya | reports; REPORT-01; A-06; payments/expenses | Belum diverifikasi |
| AC-31 | KF-09, UC-07 | BB-31 beserta variannya | dashboard/billing; HOME-01; A-04/ST-01; invoices/leases | Belum diverifikasi |
| AC-32 | KF-09, UC-07 | BB-32 beserta variannya | dashboard/rooms; HOME-01/ROOM-01; C-01; occupancies/rooms | Belum diverifikasi |
| AC-33 | KF-10, UC-09 | BB-33 beserta variannya | messaging; WA-01; S-04; payments/payment_allocations | Belum diverifikasi |
| AC-34 | KF-10, UC-09 | BB-34 beserta variannya | messaging; WA-01; S-04; residents/responsible_history | Belum diverifikasi |
| AC-35 | KF-10, UC-09 | BB-35 beserta variannya | messaging/payments; WA-01/PAY-03; S-04; payments | Belum diverifikasi |
| AC-36 | KF-05/06 | BB-36 beserta variannya | attachments; PAY-01/EXP-02; S-03; attachments | Belum diverifikasi |
| AC-37 | KF-02/03, UC-03/04 | BB-37 beserta variannya | leases; LEASE-02; A-03/C-01; occupancies | Belum diverifikasi |
| AC-38 | KF-03, UC-04 | BB-38 beserta variannya | leases; LEASE-02; A-03; occupancies | Belum diverifikasi |
| AC-39 | KF-03/10, UC-04/09 | BB-39 beserta variannya | leases/messaging; LEASE-02/WA-01; A-03/S-04; responsible_history | Belum diverifikasi |
| AC-40 | KF-03, UC-04 | BB-40 beserta variannya | leases; LEASE-02; A-03; occupancies/idempotency_records | Belum diverifikasi |
| AC-41 | KF-05/07, UC-05/08 | BB-41 beserta variannya | payments/reports; PAY-03/REPORT-01; A-05/ST-01; payments | Belum diverifikasi |
| AC-42 | KF-05/09, UC-05/07 | BB-42 beserta variannya | payments/billing; PAY-03/INV-02; ST-01; payments/invoices | Belum diverifikasi |
| AC-43 | KF-04/05, UC-05 | BB-43 beserta variannya | billing/payments; PAY-01/03; A-04/S-02; invoices/payments | Belum diverifikasi |
| AC-44 | KF-05/11, UC-05/10 | BB-44 beserta variannya | payments/initialization; PAY-01/INIT-01; A-01/A-05; app_settings/payments | Belum diverifikasi |
| AC-45 | KF-05/07, UC-05/08 | BB-45 beserta variannya | payments/reports; PAY-01/03; S-02/C-02; payment_allocations | Belum diverifikasi |
| AC-46 | KF-05, UC-05 | BB-46 beserta variannya | payments; PAY-01/02; A-05/S-02; payment_allocations | Belum diverifikasi |
| AC-47 | KF-05/07, UC-05/08 | BB-47 beserta variannya | payments/reports; PAY-03; S-02/ST-02; payments/payment_allocations | Belum diverifikasi |
| AC-48 | KF-10, UC-09 | BB-48 beserta variannya | messaging; WA-01; S-04/C-02; payment_allocations | Belum diverifikasi |
| AC-49 | KF-06/07, UC-06/08 | BB-49 beserta variannya | expenses/reports; EXP-02/REPORT-01; A-06/C-03; expenses/expense_audits | Belum diverifikasi |
| AC-50 | KF-06/07, UC-06/08 | BB-50 beserta variannya | expenses/reports; EXP-02/REPORT-01; A-06/C-03; expenses/expense_audits | Belum diverifikasi |

## 3. Semua aturan bisnis ke acceptance criteria

Relasi tidak harus satu-ke-satu. Jika suatu aturan memerlukan varian tambahan di luar redaksi AC, tambahkan varian BB/Q dan tautkan ke BR-nya; jangan menganggap pemetaan berarti otomatis sudah teruji. Teks BR asli tetap pada PRD.

| BR | AC terkait | Keluarga black box |
| --- | --- | --- |
| BR-01 | AC-06 | BB-06 |
| BR-02 | AC-06, AC-07 | BB-06, BB-07 |
| BR-03 | AC-06 | BB-06 |
| BR-04 | AC-04, AC-29 | BB-04, BB-29 |
| BR-05 | AC-06, AC-14 | BB-06, BB-14 |
| BR-06 | AC-07, AC-09 | BB-07, BB-09 |
| BR-07 | AC-07, AC-11 | BB-07, BB-11 |
| BR-08 | AC-10, AC-13 | BB-10, BB-13 |
| BR-09 | AC-11, AC-39 | BB-11, BB-39 |
| BR-10 | AC-13, AC-24, AC-34 | BB-13, BB-24, BB-34 |
| BR-11 | AC-10, AC-14 | BB-10, BB-14 |
| BR-12 | AC-37, AC-38, AC-39, AC-40 | BB-37, BB-38, BB-39, BB-40 |
| BR-13 | AC-09, AC-14, AC-16, AC-38 | BB-09, BB-14, BB-16, BB-38 |
| BR-14 | AC-09, AC-38 | BB-09, BB-38 |
| BR-15 | AC-14, AC-16 | BB-14, BB-16 |
| BR-16 | AC-09, AC-12, AC-13 | BB-09, BB-12, BB-13 |
| BR-17 | AC-14, AC-32 | BB-14, BB-32 |
| BR-18 | AC-10, AC-13, AC-26 | BB-10, BB-13, BB-26 |
| BR-19 | AC-08, AC-15 | BB-08, BB-15 |
| BR-20 | AC-15, AC-16, AC-43 | BB-15, BB-16, BB-43 |
| BR-21 | AC-16 | BB-16 |
| BR-22 | AC-17 | BB-17 |
| BR-23 | AC-15, AC-20, AC-43 | BB-15, BB-20, BB-43 |
| BR-24 | AC-15, AC-26, AC-27 | BB-15, BB-26, BB-27 |
| BR-25 | AC-18 | BB-18 |
| BR-26 | AC-19, AC-20, AC-35 | BB-19, BB-20, BB-35 |
| BR-27 | AC-20, AC-41, AC-42, AC-43, AC-44 | BB-20, BB-41, BB-42, BB-43, BB-44 |
| BR-28 | AC-45, AC-46, AC-47, AC-48 | BB-45, BB-46, BB-47, BB-48 |
| BR-29 | AC-19, AC-23, AC-25, AC-45 | BB-19, BB-23, BB-25, BB-45 |
| BR-30 | AC-21, AC-42 | BB-21, BB-42 |
| BR-31 | AC-23, AC-47 | BB-23, BB-47 |
| BR-32 | AC-24 | BB-24 |
| BR-33 | AC-22, AC-40, AC-47 | BB-22, BB-40, BB-47 |
| BR-34 | AC-25, AC-27, AC-44 | BB-25, BB-27, BB-44 |
| BR-35 | AC-25, AC-26, AC-27 | BB-25, BB-26, BB-27 |
| BR-36 | AC-26, AC-27 | BB-26, BB-27 |
| BR-37 | AC-25, AC-26 | BB-25, BB-26 |
| BR-38 | AC-25, AC-28, AC-44 | BB-25, BB-28, BB-44 |
| BR-39 | AC-27, AC-28 | BB-27, BB-28 |
| BR-40 | AC-29, AC-49, AC-50 | BB-29, BB-49, BB-50 |
| BR-41 | AC-25, AC-30, AC-41, AC-45, AC-47, AC-49, AC-50 | BB-25, BB-30, BB-41, BB-45, BB-47, BB-49, BB-50 |
| BR-42 | AC-30 | BB-30 |
| BR-43 | AC-23, AC-49, AC-50 | BB-23, BB-49, BB-50 |
| BR-44 | AC-31 | BB-31 |
| BR-45 | AC-12, AC-16, AC-31 | BB-12, BB-16, BB-31 |
| BR-46 | AC-05, AC-34, AC-39 | BB-05, BB-34, BB-39 |
| BR-47 | AC-33, AC-48 | BB-33, BB-48 |
| BR-48 | AC-34, AC-35 | BB-34, BB-35 |
| BR-49 | AC-24, AC-34 | BB-24, BB-34 |

## 4. Kualitas dan white box

| Acuan | Rencana bukti | Kapan dilengkapi |
| --- | --- | --- |
| KNF-01 kinerja | Q-01; dataset dan pengukuran aktual lokal, hosting dan HP dibedakan | Setelah query dan halaman berjalan |
| KNF-02 integritas | BB-08/22/27/28/40/46/47/49; Q-06/07/08/09 | Implementasi transaksi, audit, lampiran dan restore |
| KNF-03 akses/HP | BB-01–05/34/36; Q-02/03/04/05/10 | Setelah sesi, UI, Storage dan privilege tersedia |
| WB-01–12 | CFG aktual, perhitungan V(G), jalur/data, pytest dan coverage aktual | Setelah fungsi tersedia pada commit yang dicatat |

Path kandidat seperti app/modules/payments/service.py dapat berbeda di repo. Pemetaan final harus memakai path/simbol nyata, tidak membuat file/test dummy hanya agar tabel tampak lengkap.

## 5. Status sinkronisasi artefak

| Artefak | Status berdasarkan pekerjaan saat dokumen ini disusun | Tindakan |
| --- | --- | --- |
| PRD.md 1.0 | Baseline kebutuhan disepakati pengguna | Ubah versi bila perilaku produk berubah |
| architecture.md 1.0 | Rancangan stack/keamanan/transaksi tersedia | Cocokkan dependency, deployment dan kode aktual |
| database.md 1.0 | Kamus tabel/FK/indeks dan migration plan tersedia | Cocokkan migration serta schema PostgreSQL aktual |
| uml.md 1.0 | Sumber use case/activity/sequence/class/status tersedia | Periksa diagram terhadap kode dan proposal |
| design.md 1.0 | Spesifikasi UI dan state tersedia | Cocokkan widget/route dan pengujian HP |
| test-plan.md 1.0 | Skenario dan template hasil tersedia | Isi hasil hanya setelah eksekusi |
| Proposal Word versi 6 / PNG class sebelumnya | Belum disinkronkan dengan seluruh keputusan PRD terbaru | Revisi dua penghuni, Penghunian, AlokasiPembayaran, audit dan tanggal pencatatan sebelum penilaian final |
| Frame Figma | Mockup yang ditampilkan berupa raster; frame editable belum dibuat oleh asisten ini | Tambah node link per layar setelah frame tersedia |
| Repo OpenCode | Pengguna menyebut sedang dikerjakan; kode belum diakses/diperiksa di sesi ini | Review repo, isi path, commit dan status aktual |

Jangan mengganti status belum diverifikasi menjadi selesai hanya karena agent lain mengatakan telah mengimplementasikan; cek hasil di repo dan jalankan pengujian yang relevan.

## 6. Template implementasi dan hasil aktual

| Kebutuhan/AC | Commit | Path/simbol/route aktual | Test/run aktual | Hasil | Bukti/defect |
| --- | --- | --- | --- | --- | --- |
| Belum diisi | Belum diisi | Belum diverifikasi | Belum dijalankan | Not Run | Belum ada |
| KF-01 / UC-02 | Belum commit; Git dikelola pengguna | `backend/app/modules/rooms/router.py`; Flutter `/rooms`, `/rooms/:id` | `tests/integration/test_stage_b.py`; `frontend/test/stage_b_test.dart` | Pemeriksaan terpilih lulus; bukan seluruh keluarga BB | `testing/stage-b.md` |
| KF-02 / penghuni | Belum commit | `backend/app/modules/residents/router.py`; Flutter `/residents`, `/residents/:id` | `tests/unit/test_residents.py`; integrasi PostgreSQL foundation/stage B | Pemeriksaan terpilih lulus; riwayat keluar operasional tahap C | `testing/stage-b.md` |
| KF-11 / UC-10 / AC-26–28 | Belum commit | `backend/app/modules/initialization/{rules,service,router}.py`; Flutter `/initialization` | `tests/unit/test_initialization.py`; `tests/integration/test_stage_b.py`; `frontend/test/initialization_flow_test.dart` | Finalisasi/replay/rollback terpilih lulus; balapan multi-koneksi dan BB lengkap belum diverifikasi | `testing/stage-b.md` |

Alur pembaruan: identifikasi KF/UC/BR/AC terdampak → ubah dokumen kebutuhan/rancangan yang relevan → implementasikan pada commit → tambah/perbarui test → catat aktual/defect → retest → isi bukti. Perubahan tampilan tanpa perubahan perilaku tidak memerlukan mengarang UC baru; perubahan aturan saldo/tanggal tetap perlu ditelusuri sampai PRD.

## 7. Pemeriksaan kelengkapan dokumen

Pada pembuatan versi ini dicek secara struktural: 12 KF dan 11 UC masuk peta, 49 BR punya AC terkait, seluruh 50 AC memiliki BB sepadan, dan seluruh ID rujukan berada pada rentang yang tersedia. Ini pemeriksaan konsistensi dokumen, bukan bukti aplikasi lolos black box atau white box.

## 8. Riwayat perubahan

| Versi | Perubahan |
| --- | --- |
| 1.0 | Matriks KF/UC, seluruh AC ke 50 keluarga BB, semua BR ke AC, kebutuhan kualitas, status sinkronisasi dan template bukti aktual. Kode/hasil uji belum diverifikasi |
