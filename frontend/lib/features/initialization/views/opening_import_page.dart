import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/theme/kamartha_theme.dart';
import '../../../core/api.dart';
import '../../../core/business_repository.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';

class OpeningImportPage extends ConsumerStatefulWidget {
  const OpeningImportPage({super.key});

  @override
  ConsumerState<OpeningImportPage> createState() => _OpeningImportPageState();
}

class _OpeningImportPageState extends ConsumerState<OpeningImportPage> {
  Map<String, dynamic>? _preview;
  String? _filename, _error;
  bool _loading = false, _saving = false;

  Future<void> _choose() async {
    setState(() {
      _loading = true;
      _preview = null;
      _error = null;
    });
    try {
      final file = await FilePicker.pickFile(
        type: FileType.custom,
        allowedExtensions: const ['xlsx'],
      );
      if (file == null) return;
      if ((file.lengthSync() ?? 0) > 2 * 1024 * 1024) {
        throw const FormatException('Berkas Excel maksimal 2 MB.');
      }
      final buffer = BytesBuilder(copy: false);
      await for (final chunk in file.readAsByteStream()) {
        if (buffer.length + chunk.length > 2 * 1024 * 1024) {
          throw const FormatException('Berkas Excel maksimal 2 MB.');
        }
        buffer.add(chunk);
      }
      final bytes = buffer.takeBytes();
      if (!mounted) return;
      final result = await ref
          .read(businessProvider)
          .upload(
            '/initialization/import/preview',
            file.name,
            bytes,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          );
      if (mounted) {
        setState(() {
          _preview = result;
          _filename = file.name;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(
          () => _error = error is FormatException
              ? error.message
              : apiError(error),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_loading && !_saving,
    child: Scaffold(
      appBar: AppBar(
        toolbarHeight: 104,
        leading: IconButton(
          tooltip: 'Kembali',
          onPressed: _loading || _saving ? null : () => Navigator.pop(context),
          icon: const Icon(Icons.arrow_back),
        ),
        title: Text(
          'Impor Excel',
          textScaler: MediaQuery.textScalerOf(context)
              .clamp(maxScaleFactor: 1.3),
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SizedBox(
            width: 640,
            child: ListView(
              padding: pagePadding(context),
              children: [
                const Text(
                  'Gunakan template data lama KAMARTHA (.xlsx), maksimal 2 MB dan 200 baris per sheet.',
                ),
                const SizedBox(height: 12),
                const Text(
                  'Pratinjau tidak menyimpan data. Tagihan periode berjalan wajib dicatat meskipun lunas (sisa 0). Harga dihitung ulang oleh server.',
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: _loading || _saving ? null : _choose,
                  icon: const Icon(Icons.upload_file),
                  label: Text(
                    _loading ? 'Membaca berkas…' : 'Pilih berkas Excel',
                  ),
                ),
                if (_loading) const LinearProgressIndicator(),
                if (_error != null)
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                if (_preview != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    _filename!,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  OpeningImportReview(
                    key: ValueKey(_preview!['preview_hash']),
                    preview: _preview!,
                    onBusyChanged: (value) => setState(() => _saving = value),
                    onSaved: () => Navigator.pop(context, true),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class OpeningImportReview extends ConsumerStatefulWidget {
  const OpeningImportReview({
    super.key,
    required this.preview,
    required this.onSaved,
    required this.onBusyChanged,
  });
  final Map<String, dynamic> preview;
  final VoidCallback onSaved;
  final ValueChanged<bool> onBusyChanged;

  @override
  ConsumerState<OpeningImportReview> createState() =>
      _OpeningImportReviewState();
}

class _OpeningImportReviewState extends ConsumerState<OpeningImportReview> {
  bool _confirmed = false, _saving = false;
  String? _error;
  final _key = newRequestKey();

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    widget.onBusyChanged(true);
    try {
      await ref.read(businessProvider).write(
        'POST',
        '/initialization/import/confirm',
        {
          'tables': widget.preview['tables'],
          'preview_hash': widget.preview['preview_hash'],
          'confirmed': true,
        },
        key: _key,
      );
      if (mounted) widget.onSaved();
    } catch (error) {
      if (mounted) {
        setState(
          () => _error =
              '${apiError(error)} Jika data berubah, pilih berkas lagi untuk pratinjau baru.',
        );
      }
    } finally {
      if (mounted) {
        setState(() => _saving = false);
        widget.onBusyChanged(false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final preview = widget.preview;
    final allowed = preview['can_import'] == true;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 16),
        Text(
          'Pratinjau data awal',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        Text('Tanggal batas: ${preview['cutover_date'] ?? 'belum disimpan'}'),
        Text(
          '${preview['new_rooms']} kamar baru, ${preview['new_residents']} penghuni baru, ${preview['new_records']} draft baru.',
        ),
        Text(
          'Piutang berkas valid, termasuk draft yang sudah ada: ${formatRupiah(preview['total_receivable'])}',
        ),
        const SizedBox(height: 12),
        const Text(
          'Data yang sudah ada hanya digunakan bila cocok. Impor tidak menimpa catatan lama dan tidak melakukan finalisasi.',
        ),
        for (final error in preview['errors'] as List)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              '${error['sheet']} · ${error['row'] == null ? 'catatan yang sudah ada' : 'baris ${error['row']}'}: ${error['message']}',
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        const SizedBox(height: 12),
        for (final item in preview['items'] as List)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    '${item['sheet']} · ${item['label']}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Text(
                    item['status'] == 'NEW'
                        ? 'Data baru'
                        : 'Sudah ada, tidak ditimpa',
                  ),
                  if (item['sheet'] == 'Kontrak') ...[
                    Text(
                      'Kamar ${item['room_number']} · ${(item['residents'] as List).join(', ')}',
                    ),
                    Text(
                      '${item['data']['starts_on']} sampai ${item['data']['ends_on']} (akhir eksklusif)',
                    ),
                    Text(
                      'Harga paket ${formatRupiah(item['price'])} · Sisa ${formatRupiah(item['remaining'])}',
                    ),
                    for (final occupancy in item['occupants'] as List)
                      Text(
                        '${occupancy['name']}: masuk ${occupancy['entered_on']} · ${occupancy['state'] == 'STAYING' ? 'Masih tinggal' : 'Keluar ${occupancy['exited_on'] ?? 'tanggal tidak diketahui'}'}${occupancy['resident_id'] == item['data']['responsible_resident_id'] ? ' · Penanggung jawab' : ''}',
                      ),
                    for (final invoice in item['data']['invoices'] as List)
                      Text(
                        'Periode ${invoice['period_start']}, tempo ${invoice['due_on']}: ${formatRupiah(invoice['amount'])} − dibayar ${formatRupiah(invoice['opening_paid'])} = sisa ${formatRupiah((invoice['amount'] as int) - (invoice['opening_paid'] as int))}',
                      ),
                  ],
                ],
              ),
            ),
          ),
        if (_error != null)
          Text(
            _error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        if (!allowed)
          const Text(
            'Impor diblokir. Perbaiki baris bermasalah di Excel lalu pilih berkas kembali.',
          ),
        CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text(
            'Saya sudah memeriksa penghuni, kamar, tanggal dan saldo. Simpan sebagai draft data awal.',
          ),
          value: _confirmed,
          onChanged: allowed && !_saving
              ? (value) => setState(() => _confirmed = value!)
              : null,
        ),
        FilledButton(
          onPressed: allowed && _confirmed && !_saving ? _save : null,
          child: Text(_saving ? 'Menyimpan draft…' : 'Konfirmasi impor draft'),
        ),
        if (_saving) const LinearProgressIndicator(),
      ],
    );
  }
}
