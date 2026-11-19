## Kebijakan pengujian backend — hemat waktu dan token

- Jangan otomatis menjalankan seluruh test suite setelah setiap prompt,
  edit kecil, atau perubahan file.
- Kelompokkan perubahan dalam satu tugas sampai selesai, kemudian lakukan
  verifikasi yang relevan sekali pada akhir tugas.
- Jika pengguna hanya meminta penjelasan, review, rencana, dokumentasi,
  atau perubahan komentar/format, jangan menjalankan tes.

### Pilih cakupan tes
- Jalankan hanya tes modul/perilaku yang terdampak perubahan.
- Cari tes yang sudah ada sebelum menambahkan tes baru.
- Jangan membuat tes yang hanya meniru implementasi atau menguji ulang
  perilaku identik tanpa kebutuhan.
- Perubahan autentikasi, otorisasi, pembayaran, alokasi tagihan, pembatalan,
  transaksi database, idempotency, dan concurrency wajib mendapat
  pengujian terarah sebelum tugas dinyatakan selesai.
- Jalankan suite lengkap hanya ketika diminta pengguna, sebelum milestone
  integrasi/rilis, atau ketika perubahan lintas modul memang memerlukannya.

### Hindari pengulangan
- Jangan mengulang tes yang sudah lulus jika tidak ada perubahan relevan,
  kegagalan baru, atau masalah yang belum terjawab.
- Setelah tes gagal, fokus pada penyebab dan ulangi tes terdampak.
  Jangan langsung menjalankan semua tes.
- Jangan menjalankan ulang pengujian hanya untuk mendapatkan output laporan.

### Output
- Gunakan output ringkas; tampilkan detail hanya untuk kegagalan.
- Pada laporan akhir, sebutkan singkat apa yang diuji dan hasilnya.
- Jika pengujian tidak dijalankan, nyatakan alasannya.
- Jangan mengklaim lulus untuk pemeriksaan yang belum dilakukan.

## codegraph
Gunakan CodeGraph untuk memahami hubungan antarmodul, pemanggil fungsi,
dan dampak perubahan sebelum melakukan pencarian luas.

Untuk perubahan sederhana pada file yang sudah diketahui, baca langsung
bagian yang relevan. Jangan memanggil CodeGraph tanpa kebutuhan.

Ambil hasil yang terarah dan ringkas; jangan memuat seluruh graph.
Periksa kesegaran indeks sesuai mekanisme CodeGraph yang terpasang.
Jangan menyamakan indeks kode dengan memory keputusan proyek.