# Hosting demo

Belum ada akun hosting/domain yang disediakan. Berkas ini menyiapkan deployment,
bukan bukti aplikasi sudah tersedia di internet. Gunakan VPS/server yang selalu
aktif; layanan yang tidur dapat melewatkan pengingat dan memutus sesi WhatsApp.
Tidak ada pembelian layanan atau publikasi data yang dilakukan oleh setup ini.

1. Sediakan domain dengan DNS ke server, port 80/443 terbuka, Docker Compose.
2. Salin `.env.example` menjadi `.env`, isi rahasia melalui akses privat.
   Gunakan Supabase demo terpisah dan role runtime terbatas, bukan akun postgres.
3. Verifikasi backup dan minta persetujuan target/migrasi. Setelah disetujui,
   terapkan `0008_whatsapp_reminders` sebagai migration owner. Terapkan
   `ops/grant_runtime.sql`, termasuk setelah restore yang tidak memuat ACL.
   Jangan menyimpan kredensial owner di env container API/worker.
4. Dari `frontend`, build khusus hosting:
   `flutter build web --release --no-web-resources-cdn --dart-define=API_URL=/api/v1`.
   Jangan memakai build dengan URL localhost:8001 untuk hosting.
5. Dari folder ini: `docker compose up -d --build`.
6. Setelah nomor pengirim/tujuan uji disetujui, isi konfigurasi WA. Aktifkan
   `WHATSAPP_ENABLED=true` dan jalankan
   `docker compose --profile whatsapp up -d --build`.
7. Login melalui HTTPS, buka Menu → WA otomatis (uji), scan QR dan lihat riwayat.
   Scan memakai WhatsApp nomor pengirim, bukan membagikan QR di chat.

Caddy menyediakan HTTPS dan satu origin: `/api/*` menuju FastAPI, sisanya Flutter.
Port API dan bridge tidak dipublikasikan. Data/berkas disimpan melalui FastAPI ke
PostgreSQL/Storage privat Supabase. Auth tetap milik aplikasi, bukan Supabase Auth.
API mempercayai header proxy dari IP Caddy pada jaringan edge. Periksa subnet
tersebut terhadap jaringan server sebelum menjalankan Compose. Chromium memakai
sandbox secara default. Startup container bridge perlu dibuktikan pada host tujuan.
Volume sesi WA harus privat; kehilangan ledger tidak boleh dijadikan alasan
mengirim ulang status UNKNOWN. Jangan menjalankan dua worker aktif sekaligus.
`WHATSAPP_ALLOW_DEMO_DATE` default false. Pakai hanya untuk uji terisolasi.

Verifikasi sebelum presentasi: login, Data awal/import, tagihan/pembayaran,
QR terhubung, H-3 dan hari jatuh tempo pada nomor uji, lalu refresh/restart dan
pastikan tidak ada pesan ganda. Konfirmasi pesan pada HP penerima sendiri.

Keterbatasan: konfigurasi container/HTTPS belum terbukti di server nyata sampai
akun/domain tersedia. Bot WA tidak resmi tetap berisiko dibatasi. Blocker
produksi, termasuk konfigurasi dashboard Supabase dan pemulihan backup, tidak
otomatis selesai hanya karena memakai HTTPS. Jangan unggah dummy ke DB utama.
