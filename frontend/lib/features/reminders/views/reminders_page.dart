import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/theme/kamartha_theme.dart';
import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';

class RemindersPage extends ConsumerStatefulWidget {
  const RemindersPage({super.key});
  @override
  ConsumerState<RemindersPage> createState() => _RemindersPageState();
}

class _RemindersPageState extends ConsumerState<RemindersPage> {
  Map<String, dynamic>? _status, _result;
  List<dynamic> _history = [];
  String? _error;
  bool _busy = false, _sending = false;
  final _date = TextEditingController();
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _load();
    _timer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (!_sending && !_busy) _load();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _date.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final repo = ref.read(businessProvider);
      final status = await repo.get('/reminders/status');
      final history = await repo.get('/reminders/history');
      if (!mounted) return;
      setState(() {
        _status = status;
        _history = history['items'] as List;
        _error = null;
        if (_date.text.isEmpty) _date.text = status['today'] as String? ?? '';
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _status = null;
          _error = apiError(error);
        });
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _run() async {
    final payload = <String, dynamic>{};
    if (_status?['allow_demo_date'] == true) {
      final date = _date.text.trim();
      final parsed = DateTime.tryParse(date);
      if (parsed == null ||
          !RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(date) ||
          !parsed.toIso8601String().startsWith('${date}T')) {
        setState(
          () => _error = 'Masukkan tanggal yang sah dalam format YYYY-MM-DD.',
        );
        return;
      }
      payload['demo_date'] = date;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final data = await ref
          .read(businessProvider)
          .write('POST', '/reminders/run', payload, key: newRequestKey());
      if (!mounted) return;
      setState(() => _result = data);
      await _load();
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final qr = _status?['qr'];
    final enabled = _status?['enabled'] == true;
    final ready = enabled && _status?['ready'] == true;
    final allowDemoDate = enabled && _status?['allow_demo_date'] == true;
    final qrBytes =
        !ready &&
            enabled &&
            qr is String &&
            qr.startsWith('data:image/png;base64,') &&
            qr.length < 100000
        ? Uri.tryParse(qr)?.data?.contentAsBytes()
        : null;
    return PopScope(
      canPop: !_sending,
      child: BusinessPage(
        title: 'WA otomatis',
        subtitle: 'Prototipe uji',
        preparation: false,
        child: SizedBox(
          width: 640,
          child: ListView(
            padding: pagePadding(context),
            children: [
              const Text(
                'Hanya nomor dan tagihan uji yang disetujui. Bot WhatsApp Web tidak resmi dapat terputus atau dibatasi. Bukan untuk operasional.',
              ),
              const SizedBox(height: 16),
              if (_busy || _sending) const LinearProgressIndicator(),
              if (_error != null)
                Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              Text(
                ready
                    ? 'Sesi WhatsApp siap'
                    : _status != null && !enabled
                    ? 'WA otomatis nonaktif'
                    : 'Sesi WhatsApp belum siap',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              if (_status != null) ...[
                Text(_status!['note'] as String? ?? ''),
                Text(
                  'Jadwal otomatis: H-3 dan hari jatuh tempo, pukul ${_status!['hour_wita']}.00 WITA. Worker harus tetap menyala.',
                ),
                Text(
                  'Tujuan uji: ${(_status!['allowed_numbers'] as List? ?? []).join(', ')}',
                ),
                Text(
                  '${_status!['invoice_count'] ?? 0} tagihan uji diizinkan.',
                ),
              ],
              if (qrBytes != null) ...[
                const SizedBox(height: 16),
                const Text(
                  'WhatsApp nomor pengirim uji → Perangkat tertaut → Tautkan perangkat. Scan QR berikut; jangan bagikan QR atau folder sesi.',
                ),
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 280),
                    child: Image.memory(
                      qrBytes,
                      semanticLabel:
                          'QR untuk menautkan nomor WhatsApp pengirim uji',
                      errorBuilder: (_, _, _) => const Text(
                        'QR tidak dapat ditampilkan. Perbarui status.',
                      ),
                    ),
                  ),
                ),
              ],
              TextButton(
                onPressed: _busy || _sending ? null : _load,
                child: const Text('Perbarui status dan QR'),
              ),
              const SizedBox(height: 24),
              if (allowDemoDate) ...[
                const Text(
                  'Demonstrasi tanggal',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
                ),
                const Text(
                  'Tanggal simulasi dipakai untuk memilih tahap pengingat.',
                ),
                TextField(
                  controller: _date,
                  enabled: ready && !_sending && !_busy,
                  onChanged: (_) {
                    if (_error != null) setState(() => _error = null);
                  },
                  decoration: const InputDecoration(
                    labelText: 'Tanggal uji YYYY-MM-DD',
                  ),
                ),
              ],
              if (enabled)
                const Text(
                  'Tindakan ini mengirim pesan ke nomor uji yang diizinkan.',
                ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: ready && !_sending && !_busy ? _run : null,
                child: Text(
                  _sending
                      ? 'Memeriksa pengiriman…'
                      : allowDemoDate
                      ? 'Jalankan pengingat tanggal uji'
                      : 'Jalankan pengingat hari ini',
                ),
              ),
              if (_result != null)
                Text(
                  'Server WA menerima: ${_result!['sent']}. Belum pasti: ${_result!['unknown']}. Dilewati: ${_result!['skipped']}. Sudah pernah diproses: ${_result!['existing']}.',
                ),
              const SizedBox(height: 24),
              const Text(
                'Riwayat pengingat',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
              ),
              const Text(
                'Terkirim berarti server WhatsApp menerima, bukan bukti penghuni membaca. Status belum pasti tidak dikirim ulang otomatis.',
              ),
              if (_history.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Text('Belum ada pengiriman tercatat.'),
                ),
              for (final item in _history)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Kamar ${item['room_number']} · ${item['stage'] == 'H3' ? 'H-3' : 'Jatuh tempo'}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        Text(
                          '${item['recipient_mask']} · ${formatRupiah(item['amount'])}',
                        ),
                        Text(
                          'Jatuh tempo ${item['due_on']} · Uji ${item['reminder_date']}',
                        ),
                        Text(switch (item['status']) {
                          'SENT' => 'Terkirim, server WhatsApp menerima',
                          'FAILED' => 'Gagal',
                          _ => 'Belum pasti, perlu pemeriksaan',
                        }),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
