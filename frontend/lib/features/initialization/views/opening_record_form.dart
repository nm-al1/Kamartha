import 'package:flutter/material.dart';

import '../../../core/api.dart';
import '../../../core/money.dart';

class OpeningRecordForm extends StatefulWidget {
  const OpeningRecordForm({
    super.key,
    required this.rooms,
    required this.residents,
    required this.packages,
    required this.onSave,
    this.initial = const {},
  });
  final List<Map<String, dynamic>> rooms, residents, packages;
  final Map<String, dynamic> initial;
  final Future<void> Function(Map<String, dynamic>) onSave;
  @override
  State<OpeningRecordForm> createState() => _OpeningRecordFormState();
}

class _OpeningRecordFormState extends State<OpeningRecordForm> {
  final _fields = <String, TextEditingController>{};
  final _occupancies = <_RowFields>[];
  final _invoices = <_RowFields>[];
  final _errors = <Object, String>{};
  final _focusNodes = <Object, FocusNode>{};
  final _bannerKey = GlobalKey();
  String? _room, _package, _responsible;
  bool _busy = false;
  String? _error;

  FocusNode _focusNode(Object key) =>
      _focusNodes.putIfAbsent(key, FocusNode.new);

  bool _validDate(String text) {
    final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(text);
    if (match == null) return false;
    final year = int.parse(match.group(1)!);
    final month = int.parse(match.group(2)!);
    final day = int.parse(match.group(3)!);
    final date = DateTime.utc(year, month, day);
    return date.year == year && date.month == month && date.day == day;
  }

  int? _integer(String text) =>
      RegExp(r'^\d+$').hasMatch(text) ? int.tryParse(text) : null;

  Map<Object, String> _validate() {
    final errors = <Object, String>{};
    void checkDate(TextEditingController field) {
      final text = field.text.trim();
      if (text.isNotEmpty && !_validDate(text)) {
        errors[field] = 'Gunakan tanggal YYYY-MM-DD yang sah.';
      }
    }

    checkDate(_fields['starts_on']!);
    checkDate(_fields['ends_on']!);
    final price = _fields['price']!;
    final priceText = price.text.trim();
    if (priceText.isNotEmpty) {
      final value = _integer(priceText);
      if (value == null || value <= 0) {
        errors[price] = 'Isi nominal rupiah bulat lebih dari 0.';
      }
    }
    for (final row in _occupancies) {
      checkDate(row.fields['entered_on']!);
      checkDate(row.fields['exited_on']!);
    }
    for (final row in _invoices) {
      checkDate(row.fields['period_start']!);
      checkDate(row.fields['due_on']!);
      final amount = row.fields['amount']!;
      final amountText = amount.text.trim();
      final amountValue = amountText.isEmpty ? null : _integer(amountText);
      if (amountText.isNotEmpty && (amountValue == null || amountValue <= 0)) {
        errors[amount] = 'Isi nominal rupiah bulat lebih dari 0.';
      }
      final paid = row.fields['opening_paid']!;
      final paidText = paid.text.trim();
      final paidValue = paidText.isEmpty ? null : _integer(paidText);
      if (paidText.isNotEmpty && (paidValue == null || paidValue < 0)) {
        errors[paid] = 'Isi nominal rupiah bulat, minimal 0.';
      } else if (amountValue != null &&
          paidValue != null &&
          paidValue > amountValue) {
        errors[paid] = 'Dibayar tidak boleh melebihi nominal.';
      }
    }
    return errors;
  }

  void _focusFirst(Map<Object, String> errors) {
    if (errors.isEmpty) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _focusNode(errors.keys.first).requestFocus();
    });
  }

  void _revealGeneralError() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final banner = _bannerKey.currentContext;
      if (mounted && banner != null) {
        Scrollable.ensureVisible(
          banner,
          duration: const Duration(milliseconds: 200),
        );
      }
    });
  }

  @override
  void initState() {
    super.initState();
    _room = widget.initial['room_id'];
    _package = widget.initial['package_id'];
    _responsible = widget.initial['responsible_resident_id'];
    for (final key in ['starts_on', 'ends_on', 'price']) {
      _fields[key] = TextEditingController(
        text: '${widget.initial[key] ?? ''}',
      );
    }
    for (final value in widget.initial['occupancies'] ?? []) {
      _occupancies.add(
        _RowFields(Map<String, dynamic>.from(value), [
          'entered_on',
          'exited_on',
        ]),
      );
    }
    for (final value in widget.initial['invoices'] ?? []) {
      _invoices.add(
        _RowFields(Map<String, dynamic>.from(value), [
          'period_start',
          'due_on',
          'amount',
          'opening_paid',
        ]),
      );
    }
  }

  @override
  void dispose() {
    for (final field in _fields.values) {
      field.dispose();
    }
    for (final row in [..._occupancies, ..._invoices]) {
      row.dispose();
    }
    for (final node in _focusNodes.values) {
      node.dispose();
    }
    super.dispose();
  }

  Map<String, dynamic> _serialize() => {
    if (_room != null) 'room_id': _room,
    if (_package != null) 'package_id': _package,
    if (_responsible != null) 'responsible_resident_id': _responsible,
    for (final e in _fields.entries)
      if (e.value.text.trim().isNotEmpty)
        e.key: e.key == 'price'
            ? int.parse(e.value.text.trim())
            : e.value.text.trim(),
    'occupancies': _occupancies
        .map(
          (row) => {
            if (row.values['resident_id'] != null)
              'resident_id': row.values['resident_id'],
            'state': row.values['state'] ?? 'STAYING',
            'exit_date_unknown': row.values['exit_date_unknown'] ?? false,
            for (final e in row.fields.entries)
              if (e.value.text.trim().isNotEmpty) e.key: e.value.text.trim(),
          },
        )
        .toList(),
    'invoices': _invoices
        .map(
          (row) => {
            for (final e in row.fields.entries)
              if (e.value.text.trim().isNotEmpty)
                e.key: ['amount', 'opening_paid'].contains(e.key)
                    ? int.parse(e.value.text.trim())
                    : e.value.text.trim(),
          },
        )
        .toList(),
  };

  Future<void> _save() async {
    final errors = _validate();
    if (errors.isNotEmpty) {
      setState(() {
        _errors
          ..clear()
          ..addAll(errors);
        _error = null;
      });
      _focusFirst(errors);
      return;
    }
    setState(() {
      _busy = true;
      _errors.clear();
      _error = null;
    });
    try {
      await widget.onSave(_serialize());
    } on FormatException {
      if (mounted) {
        setState(
          () => _error = 'Nominal harus rupiah bulat tanpa titik atau koma.',
        );
        _revealGeneralError();
      }
    } catch (error) {
      if (mounted) {
        final fields = apiFieldErrors(error);
        final mapped = <Object, String>{};
        const dropdowns = {
          'room_id': 'room',
          'package_id': 'package',
          'responsible_resident_id': 'responsible',
        };
        for (final entry in fields.entries) {
          final field = _fields[entry.key];
          if (field != null) {
            mapped[field] = entry.value;
          } else {
            final key = dropdowns[entry.key];
            if (key != null) mapped[key] = entry.value;
          }
        }
        setState(() {
          _errors
            ..clear()
            ..addAll(mapped);
          _error = apiError(error);
        });
        if (mapped.isEmpty) {
          _revealGeneralError();
        } else {
          _focusFirst(mapped);
        }
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _field(String label, TextEditingController field) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: TextField(
      controller: field,
      focusNode: _focusNode(field),
      enabled: !_busy,
      decoration: InputDecoration(
        label: Text(label, maxLines: 3),
        errorText: _errors[field],
        errorMaxLines: 3,
      ),
      onChanged: (_) {
        if (_errors.remove(field) != null) setState(() {});
      },
    ),
  );

  Widget _select(
    String label,
    String? value,
    List<Map<String, dynamic>> items,
    String Function(Map<String, dynamic>) title,
    void Function(String?) change, {
    Object? errorKey,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: DropdownButtonFormField<String>(
      initialValue: items.any((e) => e['id'] == value) ? value : null,
      isExpanded: true,
      focusNode: errorKey == null ? null : _focusNode(errorKey),
      decoration: InputDecoration(
        labelText: label,
        errorText: errorKey == null ? null : _errors[errorKey],
      ),
      items: items
          .map(
            (e) => DropdownMenuItem<String>(
              value: e['id'],
              child: Text(title(e), overflow: TextOverflow.ellipsis),
            ),
          )
          .toList(),
      onChanged: _busy
          ? null
          : (v) => setState(() {
              change(v);
              if (errorKey != null) _errors.remove(errorKey);
            }),
    ),
  );

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text(
          'Isian belum lengkap boleh disimpan sebagai Draft. Jangan mengarang identitas, tanggal atau nominal. Tanggal: YYYY-MM-DD.',
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Semantics(
            key: _bannerKey,
            liveRegion: true,
            child: Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        ],
        const SizedBox(height: 20),
        const Text(
          'Kamar dan kontrak',
          style: TextStyle(
            fontSize: 20,
            height: 1.2,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 16),
        _select(
          'Kamar',
          _room,
          widget.rooms,
          (r) => '${r['number']} (${r['room_type']})',
          (v) => _room = v,
          errorKey: 'room',
        ),
        _select(
          'Paket',
          _package,
          widget.packages,
          (p) => '${p['occupant_type']} orang • ${p['period_months']} bulan',
          (v) => _package = v,
          errorKey: 'package',
        ),
        _field('Tanggal mulai kontrak', _fields['starts_on']!),
        _field('Tanggal akhir kontrak (eksklusif)', _fields['ends_on']!),
        _field('Harga kesepakatan per periode (rupiah)', _fields['price']!),
        _select(
          'Penanggung jawab',
          _responsible,
          widget.residents,
          (r) => '${r['name']} (${r['identity_number']})',
          (v) => _responsible = v,
          errorKey: 'responsible',
        ),
        const SizedBox(height: 8),
        const Text(
          'Penghunian',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        const Text(
          'Catat satu/dua orang awal sesuai paket. Pengganti dicatat sebagai baris tambahan, bukan mengganti nama lama.',
        ),
        for (final row in _occupancies)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _select(
                    'Penghuni',
                    row.values['resident_id'],
                    widget.residents,
                    (r) => '${r['name']} (${r['identity_number']})',
                    (v) => row.values['resident_id'] = v,
                  ),
                  _field('Tanggal masuk', row.fields['entered_on']!),
                  _select(
                    'Keadaan',
                    row.values['state'] ?? 'STAYING',
                    const [
                      {'id': 'STAYING', 'name': 'Masih tinggal'},
                      {'id': 'EXITED', 'name': 'Sudah keluar'},
                    ],
                    (s) => '${s['name']}',
                    (v) {
                      row.values['state'] = v;
                      if (v == 'STAYING') {
                        row.fields['exited_on']!.clear();
                        row.values['exit_date_unknown'] = false;
                      }
                    },
                  ),
                  if (row.values['state'] == 'EXITED') ...[
                    CheckboxListTile(
                      title: const Text(
                        'Sudah diverifikasi keluar, tanggal tidak diketahui',
                      ),
                      value: row.values['exit_date_unknown'] == true,
                      onChanged: _busy
                          ? null
                          : (v) => setState(() {
                              row.values['exit_date_unknown'] = v;
                              if (v == true) row.fields['exited_on']!.clear();
                            }),
                    ),
                    if (row.values['exit_date_unknown'] != true)
                      _field(
                        'Tanggal keluar sebenarnya',
                        row.fields['exited_on']!,
                      ),
                  ],
                  TextButton(
                    onPressed: _busy
                        ? null
                        : () => setState(() {
                            _occupancies.remove(row);
                            row.dispose();
                          }),
                    child: const Text('Hapus baris penghuni'),
                  ),
                ],
              ),
            ),
          ),
        TextButton(
          onPressed: _busy
              ? null
              : () => setState(
                  () => _occupancies.add(
                    _RowFields({}, ['entered_on', 'exited_on']),
                  ),
                ),
          child: const Text('Tambah baris penghuni'),
        ),
        const SizedBox(height: 20),
        const Text(
          'Tagihan per periode',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        const Text(
          'Masukkan periode berjalan walau sudah lunas dan semua tunggakan lama. Ini bukan transaksi kas lama. Sisa dihitung otomatis.',
        ),
        for (final row in _invoices)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _field('Awal periode', row.fields['period_start']!),
                  _field('Jatuh tempo asli', row.fields['due_on']!),
                  _field('Nominal asli (rupiah)', row.fields['amount']!),
                  _field(
                    'Dibayar sebelum pencatatan (rupiah)',
                    row.fields['opening_paid']!,
                  ),
                  ValueListenableBuilder(
                    valueListenable: row.fields['amount']!,
                    builder: (context, value, child) => ValueListenableBuilder(
                      valueListenable: row.fields['opening_paid']!,
                      builder: (context, paid, child) {
                        final amount = int.tryParse(value.text),
                            opening = int.tryParse(paid.text);
                        return Text(
                          amount == null || opening == null
                              ? 'Sisa: isi nominal dan pembayaran'
                              : 'Sisa: ${formatRupiah(amount - opening)}',
                        );
                      },
                    ),
                  ),
                  TextButton(
                    onPressed: _busy
                        ? null
                        : () => setState(() {
                            _invoices.remove(row);
                            row.dispose();
                          }),
                    child: const Text('Hapus baris tagihan'),
                  ),
                ],
              ),
            ),
          ),
        TextButton(
          onPressed: _busy
              ? null
              : () => setState(
                  () => _invoices.add(
                    _RowFields({}, [
                      'period_start',
                      'due_on',
                      'amount',
                      'opening_paid',
                    ]),
                  ),
                ),
          child: const Text('Tambah baris tagihan'),
        ),
        FilledButton(
          onPressed: _busy ? null : _save,
          child: Text(_busy ? 'Menyimpan…' : 'Simpan draft'),
        ),
        const SizedBox(height: 24),
      ],
    ),
  );
}

class _RowFields {
  _RowFields(this.values, List<String> keys) {
    for (final key in keys) {
      fields[key] = TextEditingController(text: '${values[key] ?? ''}');
    }
  }
  final Map<String, dynamic> values;
  final fields = <String, TextEditingController>{};
  void dispose() {
    for (final field in fields.values) {
      field.dispose();
    }
  }
}
