import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';
import 'opening_record_form.dart';
import 'opening_import_page.dart';

class InitializationPage extends ConsumerStatefulWidget {
  const InitializationPage({super.key});
  @override
  ConsumerState<InitializationPage> createState() => _InitializationPageState();
}

class _InitializationPageState extends ConsumerState<InitializationPage> {
  Map<String, dynamic>? _settings, _summary;
  List<Map<String, dynamic>> _records = [],
      _rooms = [],
      _residents = [],
      _packages = [];
  bool _busy = true, _matches = false, _settled = false;
  String? _error, _finalizeKey;
  Map<String, dynamic>? _finalizePayload;
  final _cutover = TextEditingController();
  String? _settingsKey, _settingsDate;
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _cutover.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repo = ref.read(businessProvider);
      final settings = await repo.get('/initialization/settings');
      if (!mounted) return;
      if (settings['mode'] == 'ACTIVE') {
        context.go('/home');
        return;
      }
      final rooms = await repo.all('/rooms');
      final residents = await repo.all('/residents');
      final records = await repo.all('/initialization/records');
      final summary = await repo.get('/initialization/reconciliation');
      if (!mounted) return;
      setState(() {
        _settings = settings;
        _summary = summary;
        _rooms = rooms;
        _residents = residents;
        _records = records;
        _packages = (settings['packages'] as List)
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
        _cutover.text = settings['cutover_date'] ?? '';
        _settingsKey = null;
        _settingsDate = null;
        _finalizeKey = null;
        _finalizePayload = null;
        _matches = false;
        _settled = false;
      });
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveSettings() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_settingsDate != _cutover.text.trim()) {
        _settingsKey = newRequestKey();
        _settingsDate = _cutover.text.trim();
      }
      await ref.read(businessProvider).write(
        'PUT',
        '/initialization/settings',
        {
          'cutover_date': _cutover.text.trim(),
          'expected_version': _settings!['version'],
        },
        key: _settingsKey,
      );
      _settingsKey = null;
      _settingsDate = null;
      await _load();
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = apiError(error);
          _busy = false;
        });
      }
    }
  }

  Future<void> _edit([Map<String, dynamic>? record]) async {
    final key = newRequestKey();
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => Scaffold(
          resizeToAvoidBottomInset: true,
          appBar: AppBar(
            toolbarHeight: 104,
            leading: IconButton(
              tooltip: 'Kembali',
              icon: const Icon(Icons.arrow_back, size: 28),
              onPressed: () => Navigator.maybePop(context),
            ),
            title: Text(
              'Berkas data awal',
              textScaler: MediaQuery.textScalerOf(context)
                  .clamp(maxScaleFactor: 1.3),
              maxLines: 2,
              overflow: TextOverflow.visible,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
            ),
          ),
          body: SafeArea(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 640),
                child: OpeningRecordForm(
                  rooms: _rooms,
                  residents: _residents,
                  packages: _packages,
                  initial: record == null
                      ? const {}
                      : Map<String, dynamic>.from(record['draft_data']),
                  onSave: (data) async {
                    await ref
                        .read(businessProvider)
                        .write(
                          record == null ? 'POST' : 'PATCH',
                          record == null
                              ? '/initialization/records'
                              : '/initialization/records/${record['id']}',
                          record == null
                              ? {'client_record_key': key, 'draft_data': data}
                              : {
                                  'expected_version': record['version'],
                                  'draft_data': data,
                                },
                          key: key,
                        );
                    if (context.mounted) Navigator.pop(context, true);
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
    if (saved == true && mounted) await _load();
  }

  Future<void> _finalize() async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Kunci data awal dan buka operasional?'),
        content: Text(
          'Tanggal batas ${_summary!['cutover_date']}, ${_summary!['invoice_count']} tagihan, piutang ${formatRupiah(_summary!['total_receivable'])}. '
          'Setelah finalisasi, tanggal batas dan saldo awal tidak dapat diedit dari aplikasi.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Tinjau lagi'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Finalisasi'),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted) return;
    _finalizeKey ??= newRequestKey();
    _finalizePayload ??= {
      'expected_version': _summary!['version'],
      'reconciliation_hash': _summary!['reconciliation_hash'],
      'confirmed_matches': true,
      'confirmed_old_periods_settled': true,
    };
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(businessProvider)
          .write(
            'POST',
            '/initialization/finalize',
            _finalizePayload!,
            key: _finalizeKey,
          );
      if (mounted) {
        context.go('/home');
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error =
              '${apiError(error)} Hasil finalisasi mungkin belum diketahui. Coba ulang dengan permintaan yang sama atau muat ulang status.';
          _busy = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) => BusinessPage(
    title: 'Data awal',
    subtitle: 'Persiapan',
    child: SizedBox(
      width: 640,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Persiapan pencatatan',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
          ),
          const Text(
            'Pembayaran dan pengeluaran operasional belum dibuka. Catat transaksi nyata sejak tanggal batas di catatan pendamping.',
            style: TextStyle(fontSize: 14, height: 1.4),
          ),
          const SizedBox(height: 20),
          if (_busy) const LinearProgressIndicator(),
          if (_error != null) ...[
            Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            TextButton(
              onPressed: _busy ? null : _load,
              child: const Text('Muat ulang status'),
            ),
          ],
          if (_settings != null) ...[
            const Text(
              '1. Tanggal mulai pencatatan',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _cutover,
              enabled: !_busy && _finalizeKey == null,
              decoration: const InputDecoration(labelText: 'YYYY-MM-DD'),
            ),
            TextButton(
              onPressed: _busy || _finalizeKey != null ? null : _saveSettings,
              child: const Text('Simpan tanggal batas'),
            ),
            const SizedBox(height: 20),
            const Text(
              '2. Berkas penghuni dan kontrak',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Impor Excel untuk menambahkan kamar, penghuni dan draft sekaligus. Untuk input manual, tambahkan kamar dan penghuni melalui menu terlebih dahulu.',
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed:
                  _busy ||
                      _settings!['cutover_date'] == null ||
                      _finalizeKey != null
                  ? null
                  : () async {
                      final saved = await Navigator.of(context).push<bool>(
                        MaterialPageRoute(
                          builder: (_) => const OpeningImportPage(),
                        ),
                      );
                      if (saved == true && mounted) await _load();
                    },
              icon: const Icon(Icons.upload_file),
              label: const Text('Impor Excel'),
            ),
            if (_records.isEmpty)
              const Text(
                'Belum ada berkas. Kos kosong boleh difinalisasi setelah rekap dikonfirmasi.',
              ),
            const SizedBox(height: 12),
            if (_records.isNotEmpty)
              Card(
                clipBehavior: Clip.antiAlias,
                child: Column(
                  children: [
                    for (var i = 0; i < _records.length; i++) ...[
                      if (i > 0) const Divider(height: 1),
                      ListTile(
                        title: Text(
                          'Berkas ${i + 1} • ${_records[i]['state']}',
                          style: const TextStyle(
                            fontSize: 16,
                            height: 1.2,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        subtitle: Text('Versi ${_records[i]['version']}'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: _busy || _finalizeKey != null
                            ? null
                            : () => _edit(_records[i]),
                      ),
                    ],
                  ],
                ),
              ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed:
                  _busy ||
                      _settings!['cutover_date'] == null ||
                      _finalizeKey != null
                  ? null
                  : () => _edit(),
              child: const Text('Tambah berkas'),
            ),
            const SizedBox(height: 24),
            const Text(
              '3. Rekap dan pemeriksaan',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            if (_summary != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        '${_summary!['record_count']} berkas • ${_summary!['resident_count']} penghuni • ${_summary!['occupied_room_count']} kamar dihuni',
                      ),
                      const SizedBox(height: 12),
                      const Divider(height: 1),
                      const SizedBox(height: 12),
                      Text(
                        '${_summary!['invoice_count']} tagihan • Total piutang ${formatRupiah(_summary!['total_receivable'])}',
                        style: const TextStyle(
                          fontSize: 16,
                          height: 1.4,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              for (final record in _summary!['records'] as List)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Kamar ${record['room_number']} • ${record['occupant_type']} orang / ${record['period_months']} bulan',
                        ),
                        Text(
                          '${record['starts_on']} sampai ${record['ends_on']} • ${formatRupiah(record['price'])} per periode',
                        ),
                        for (final occupancy in record['occupancies'] as List)
                          Text(
                            '${occupancy['name']}: ${occupancy['state'] == 'STAYING' ? 'Masih tinggal' : 'Keluar'}; '
                            'masuk ${occupancy['entered_on']}; keluar ${occupancy['exited_on'] ?? (occupancy['exit_date_unknown'] == true ? 'tanggal tidak diketahui' : 'belum keluar')}',
                          ),
                        for (final invoice in record['invoices'] as List)
                          Text(
                            'Periode ${invoice['period_start']}, jatuh tempo ${invoice['due_on']}: '
                            '${formatRupiah(invoice['amount'])} − dibayar ${formatRupiah(invoice['opening_paid'])} = sisa ${formatRupiah(invoice['remaining'])}',
                          ),
                      ],
                    ),
                  ),
                ),
              for (final error in _summary!['errors'] as List)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(
                    'Berkas ${error['record_id'] ?? 'pengaturan'}: ${(error['messages'] as List).join(' ')}',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ),
              TextButton(
                onPressed: _busy ? null : _load,
                child: const Text('Periksa ulang rekap'),
              ),
              const SizedBox(height: 24),
              const Text(
                '4. Tinjau dan finalisasi',
                style: TextStyle(
                  fontSize: 20,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                ),
              ),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text(
                  'Rekap penghuni, kontrak, tagihan dan piutang cocok dengan catatan mitra.',
                ),
                value: _matches,
                onChanged: _busy ? null : (v) => setState(() => _matches = v!),
              ),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text(
                  'Periode lama lainnya sudah diselesaikan dan seluruh tunggakan telah dimasukkan.',
                ),
                value: _settled,
                onChanged: _busy ? null : (v) => setState(() => _settled = v!),
              ),
              FilledButton(
                onPressed:
                    !_busy &&
                        ((_matches &&
                                _settled &&
                                _summary!['can_finalize'] == true) ||
                            _finalizeKey != null)
                    ? _finalize
                    : null,
                child: Text(
                  _finalizeKey == null
                      ? 'Tinjau finalisasi'
                      : 'Ulangi finalisasi yang sama',
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Finalisasi mengunci tanggal batas dan saldo awal.',
                style: TextStyle(fontSize: 14, height: 1.4),
              ),
            ],
          ],
        ],
      ),
    ),
  );
}
