import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';
import '../../../core/dates.dart' as dates;
import '../../../app/theme/kamartha_theme.dart';

String leaseStatus(Object? value) => switch ('$value') {
  'ACTIVE' => 'Aktif',
  'SCHEDULED' => 'Terjadwal',
  'ENDED' => 'Berakhir',
  _ => '—',
};

String invoiceStatus(Object? value) => switch ('$value') {
  'PAID' => 'Lunas',
  'PARTIALLY_PAID' => 'Dibayar sebagian',
  'OVERDUE' => 'Menunggak',
  'UNPAID' => 'Belum dibayar',
  'CANCELLED' => 'Batal',
  _ => '—',
};

String shortDate(Object? value) => dates.shortDate(value);

class LeasesPage extends ConsumerStatefulWidget {
  const LeasesPage({super.key});
  @override
  ConsumerState<LeasesPage> createState() => _LeasesPageState();
}

class _LeasesPageState extends ConsumerState<LeasesPage> {
  final _search = TextEditingController();
  List<Map<String, dynamic>> _items = [];
  bool _busy = true, _preparation = true, _more = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load({bool append = false}) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repository = ref.read(businessProvider);
      final settings = await repository.get('/initialization/settings');
      final data = await repository.get('/leases', {
        'q': _search.text,
        'limit': 20,
        'offset': append ? _items.length : 0,
      });
      if (!mounted) return;
      setState(() {
        final items = (data['items'] as List)
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
        _items = append ? [..._items, ...items] : items;
        _more = data['pagination']['has_more'] == true;
        _preparation = settings['mode'] == 'PREPARATION';
      });
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _create() async {
    final saved = await Navigator.of(context)
        .push<bool>(MaterialPageRoute(builder: (_) => const LeaseCreatePage()));
    if (saved == true && mounted) await _load();
  }

  @override
  Widget build(BuildContext context) => BusinessPage(
    title: 'Masa sewa',
    subtitle: 'Dari Menu',
    preparation: _preparation,
    child: ListView(
      padding: pagePadding(context),
      children: [
        TextField(
          controller: _search,
          decoration: InputDecoration(
            labelText: 'Cari kamar atau nama penghuni',
            suffixIcon: IconButton(
              tooltip: 'Cari',
              onPressed: _busy ? null : () => _load(),
              icon: const Icon(Icons.search),
            ),
          ),
          onSubmitted: (_) => _load(),
        ),
        const SizedBox(height: 16),
        if (!_busy && _error == null)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(
              _more
                  ? '${_items.length} kontrak dimuat'
                  : '${_items.length} kontrak tercatat',
              style: const TextStyle(
                fontSize: 14,
                color: KamarthaColors.secondary,
              ),
            ),
          ),
        FilledButton(
          onPressed: _busy || _preparation ? null : _create,
          child: const Text('Kontrak baru'),
        ),
        if (_preparation)
          const Padding(
            padding: EdgeInsets.only(top: 12),
            child: Text(
              'Kontrak operasional tersedia setelah data awal difinalisasi.',
            ),
          ),
        if (_busy) const LinearProgressIndicator(),
        if (_error != null) ...[
          Text(_error!),
          TextButton(onPressed: () => _load(), child: const Text('Coba lagi')),
        ],
        if (!_busy && _error == null && _items.isEmpty)
          const Padding(
            padding: EdgeInsets.all(24),
            child: Text('Belum ada kontrak yang cocok.'),
          ),
        const SizedBox(height: 16),
        if (_items.isNotEmpty)
          Card(
            clipBehavior: Clip.antiAlias,
            child: Column(
              children: [
                for (var i = 0; i < _items.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  InkWell(
                    onTap: () => context.push('/leases/${_items[i]['id']}'),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Kamar ${_items[i]['room_number']}',
                                  style: const TextStyle(
                                    fontSize: 16,
                                    height: 1.2,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  '${_items[i]['resident_names'] ?? 'Belum ada penghuni tinggal'}',
                                  style: const TextStyle(
                                    fontSize: 16,
                                    height: 1.2,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  dates.rangeLabel(
                                    _items[i]['starts_on'],
                                    _items[i]['effective_ends_on'],
                                  ),
                                  style: const TextStyle(
                                    fontSize: 14,
                                    height: 1.2,
                                    color: KamarthaColors.secondary,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  '${_items[i]['occupant_type_snapshot']} orang · ${_items[i]['period_months_snapshot']} bulan · ${leaseStatus(_items[i]['status'])}',
                                  style: const TextStyle(
                                    fontSize: 14,
                                    height: 1.2,
                                    color: KamarthaColors.secondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 12),
                          const Icon(
                            Icons.chevron_right,
                            color: KamarthaColors.secondary,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        const Padding(
          padding: EdgeInsets.only(top: 16),
          child: Text(
            'Kontrak selesai tetap menyimpan riwayat dan piutang.',
            style: TextStyle(fontSize: 14, color: KamarthaColors.secondary),
          ),
        ),
        if (_more)
          TextButton(
            onPressed: _busy ? null : () => _load(append: true),
            child: const Text('Muat berikutnya'),
          ),
      ],
    ),
  );
}

class LeaseCreatePage extends ConsumerStatefulWidget {
  const LeaseCreatePage({super.key});
  @override
  ConsumerState<LeaseCreatePage> createState() => _LeaseCreatePageState();
}

class _LeaseCreatePageState extends ConsumerState<LeaseCreatePage> {
  final _form = GlobalKey<FormState>();
  final _start = TextEditingController(
    text: DateTime.now().toIso8601String().substring(0, 10),
  );
  final _periods = TextEditingController(text: '1');
  final _price = TextEditingController();
  List<Map<String, dynamic>> _rooms = [], _residents = [], _packages = [];
  String? _roomId, _packageId, _first, _second, _responsible;
  bool _busy = true;
  String? _error, _key;
  String? _lastPayload;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _start.dispose();
    _periods.dispose();
    _price.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final repository = ref.read(businessProvider);
      final rooms = await repository.all('/rooms');
      final residents = await repository.all('/residents');
      final settings = await repository.get('/initialization/settings');
      if (!mounted) return;
      setState(() {
        _rooms = rooms;
        _residents = residents;
        _packages = (settings['packages'] as List)
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
        _busy = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = apiError(error);
          _busy = false;
        });
      }
    }
  }

  Map<String, dynamic>? get _package =>
      _packages.where((item) => item['id'] == _packageId).firstOrNull;

  Map<String, dynamic>? get _room =>
      _rooms.where((item) => item['id'] == _roomId).firstOrNull;

  bool _validDate(String text) {
    final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})$').firstMatch(text);
    if (match == null) return false;
    final date = DateTime.utc(
      int.parse(match.group(1)!),
      int.parse(match.group(2)!),
      int.parse(match.group(3)!),
    );
    return date.year == int.parse(match.group(1)!) &&
        date.month == int.parse(match.group(2)!) &&
        date.day == int.parse(match.group(3)!);
  }

  Future<void> _review() async {
    if (!_form.currentState!.validate()) return;
    final package = _package!;
    final residents = [_first!, if (package['occupant_type'] == 2) _second!];
    if (residents.toSet().length != residents.length) {
      setState(() => _error = 'Dua penghuni dalam kontrak harus berbeda.');
      return;
    }
    if (!residents.contains(_responsible)) {
      setState(
        () => _error = 'Penanggung jawab harus salah satu penghuni kontrak.',
      );
      return;
    }
    final names = residents
        .map((id) => _residents.firstWhere((item) => item['id'] == id)['name'])
        .join(' dan ');
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Tinjau kontrak baru'),
        content: Text(
          'Kamar ${_room!['number']}\n'
          'Paket ${package['occupant_type']} orang / ${package['period_months']} bulan\n'
          'Mulai ${_start.text.trim()} selama ${_periods.text.trim()} periode\n'
          'Harga ${formatRupiah(int.tryParse(_price.text.trim()))} per periode\n'
          'Penghuni: $names\n'
          'Penanggung jawab: ${_residents.firstWhere((item) => item['id'] == _responsible)['name']}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Periksa lagi'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan kontrak'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) await _save(residents);
  }

  Future<void> _save(List<String> residents) async {
    final payload = <String, dynamic>{
      'room_id': _roomId,
      'package_id': _packageId,
      'starts_on': _start.text.trim(),
      'periods': int.parse(_periods.text.trim()),
      'price': int.parse(_price.text.trim()),
      'resident_ids': residents,
      'responsible_resident_id': _responsible,
    };
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_lastPayload != jsonEncode(payload)) {
        _key = newRequestKey();
        _lastPayload = jsonEncode(payload);
      }
      await ref
          .read(businessProvider)
          .write('POST', '/leases', payload, key: _key);
      if (mounted) Navigator.pop(context, true);
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = apiError(error);
          _busy = false;
        });
      }
    }
  }

  Widget _residentField(
    String label,
    String? value,
    void Function(String?) change,
  ) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: DropdownButtonFormField<String>(
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(labelText: label),
      items: _residents
          .map(
            (item) => DropdownMenuItem(
              value: item['id'] as String,
              child: Text(
                '${item['name']} (${item['identity_number']})',
                overflow: TextOverflow.ellipsis,
              ),
            ),
          )
          .toList(),
      onChanged: _busy
          ? null
          : (selected) => setState(() {
              change(selected);
              if (![_first, _second].contains(_responsible)) {
                _responsible = null;
              }
            }),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final occupants = _package?['occupant_type'] ?? 1;
    return PopScope(
      canPop: !_busy,
      child: Scaffold(
        resizeToAvoidBottomInset: true,
        appBar: AppBar(
          toolbarHeight: 104,
          leading: IconButton(
            tooltip: 'Kembali',
            icon: const Icon(Icons.arrow_back, size: 28),
            onPressed: _busy ? null : () => Navigator.maybePop(context),
          ),
          title: Text(
            'Kontrak baru',
            textScaler: MediaQuery.textScalerOf(context)
                .clamp(maxScaleFactor: 1.3),
            maxLines: 2,
            overflow: TextOverflow.visible,
          ),
        ),
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: Form(
              key: _form,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_busy) const LinearProgressIndicator(),
                  if (_error != null) ...[
                    Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                    TextButton(
                      onPressed: _load,
                      child: const Text('Muat ulang'),
                    ),
                    const SizedBox(height: 12),
                  ],
                  const Text(
                    '1. Kamar dan paket',
                    style: TextStyle(
                      fontSize: 20,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _roomId,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Kamar'),
                    items: _rooms
                        .map(
                          (item) => DropdownMenuItem(
                            value: item['id'] as String,
                            child: Text(
                              '${item['number']} • ${item['room_type']} • maks ${item['supported_occupants']} orang',
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: _busy
                        ? null
                        : (value) => setState(() {
                            _roomId = value;
                            if ((_room?['supported_occupants'] ?? 0) <
                                (_package?['occupant_type'] ?? 1)) {
                              _packageId = null;
                            }
                          }),
                    validator: (value) => value == null ? 'Pilih kamar.' : null,
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    initialValue: _packageId,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Paket'),
                    items: _packages
                        .where(
                          (item) =>
                              item['occupant_type'] <=
                              (_room?['supported_occupants'] ?? 2),
                        )
                        .map(
                          (item) => DropdownMenuItem(
                            value: item['id'] as String,
                            child: Text(
                              '${item['occupant_type']} orang / ${item['period_months']} bulan',
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: _busy
                        ? null
                        : (value) => setState(() {
                            _packageId = value;
                            if ((_package?['occupant_type'] ?? 1) == 1) {
                              _second = null;
                            }
                            if (![_first, _second].contains(_responsible)) {
                              _responsible = null;
                            }
                          }),
                    validator: (value) => value == null ? 'Pilih paket.' : null,
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    '2. Tanggal dan harga',
                    style: TextStyle(
                      fontSize: 20,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _start,
                    enabled: !_busy,
                    decoration: const InputDecoration(
                      label: Text('Tanggal mulai (YYYY-MM-DD)', maxLines: 3),
                      errorMaxLines: 3,
                    ),
                    validator: (value) => _validDate((value ?? '').trim())
                        ? null
                        : 'Gunakan tanggal YYYY-MM-DD yang sah.',
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _periods,
                    enabled: !_busy,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Jumlah periode penuh',
                    ),
                    validator: (value) {
                      final parsed = int.tryParse((value ?? '').trim());
                      return parsed == null || parsed < 1 || parsed > 120
                          ? 'Isi 1 sampai 120 periode.'
                          : null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _price,
                    enabled: !_busy,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      label: Text(
                        'Harga total per periode (rupiah)',
                        maxLines: 3,
                      ),
                      errorMaxLines: 3,
                    ),
                    validator: (value) {
                      final parsed = int.tryParse((value ?? '').trim());
                      return parsed == null || parsed < 1
                          ? 'Isi nominal rupiah bulat lebih dari 0.'
                          : null;
                    },
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    '3. Penghuni dan penanggung jawab',
                    style: TextStyle(
                      fontSize: 20,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  _residentField(
                    'Penghuni pertama',
                    _first,
                    (value) => _first = value,
                  ),
                  if (occupants == 2)
                    _residentField(
                      'Penghuni kedua',
                      _second,
                      (value) => _second = value,
                    ),
                  DropdownButtonFormField<String>(
                    initialValue: _responsible,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Penanggung jawab',
                    ),
                    items: [_first, _second]
                        .whereType<String>()
                        .toSet()
                        .map(
                          (id) => DropdownMenuItem(
                            value: id,
                            child: Text(
                              '${_residents.firstWhere((item) => item['id'] == id)['name']}',
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: _busy
                        ? null
                        : (value) => setState(() => _responsible = value),
                    validator: (value) =>
                        value == null ? 'Pilih penanggung jawab.' : null,
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Dua nama harus berbeda. Harga dua orang bukan dua kali harga satu orang.',
                    style: TextStyle(
                      fontSize: 14,
                      height: 1.4,
                      color: KamarthaColors.secondary,
                    ),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _busy ? null : _review,
                    child: Text(_busy ? 'Menyimpan…' : 'Tinjau kontrak'),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class LeaseDetailPage extends ConsumerStatefulWidget {
  const LeaseDetailPage({super.key, required this.id});
  final String id;
  @override
  ConsumerState<LeaseDetailPage> createState() => _LeaseDetailPageState();
}

class _LeaseDetailPageState extends ConsumerState<LeaseDetailPage> {
  final _pendingRequestKeys = <String, String>{};
  Map<String, dynamic>? _lease;
  List<Map<String, dynamic>> _residents = [], _packages = [];
  bool _busy = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repository = ref.read(businessProvider);
      final lease = await repository.get('/leases/${widget.id}');
      final residents = await repository.all('/residents');
      final settings = await repository.get('/initialization/settings');
      if (!mounted) return;
      setState(() {
        _lease = lease;
        _residents = residents;
        _packages = (settings['packages'] as List)
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
      });
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  List<Map<String, dynamic>> get _staying =>
      (_lease?['occupancies'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e))
          .where((item) => item['state'] == 'STAYING')
          .toList();

  Map<String, dynamic>? get _responsibleOccupancy =>
      _staying.where((item) => item['responsible'] == true).firstOrNull;

  Future<Map<String, dynamic>> _write(
    String method,
    String path,
    Map<String, dynamic> data,
  ) async {
    final signature = jsonEncode([method, path, data]);
    final key = _pendingRequestKeys.putIfAbsent(signature, newRequestKey);
    final result = await ref
        .read(businessProvider)
        .write(method, path, data, key: key);
    _pendingRequestKeys.remove(signature);
    return result;
  }

  Future<bool?> _actionDialog({
    required BuildContext context,
    required WidgetBuilder builder,
  }) async {
    final route = DialogRoute<bool>(
      context: context,
      builder: (dialogContext) => CallbackShortcuts(
        bindings: {
          const SingleActivator(LogicalKeyboardKey.escape):
              () => Navigator.of(dialogContext).pop(false),
        },
        child: builder(dialogContext),
      ),
    );
    final result = await Navigator.of(context, rootNavigator: true).push(route);
    // Keep local controllers alive until the closing transition removes the dialog.
    await route.completed;
    return result;
  }

  Future<void> _exit(Map<String, dynamic> occupancy) async {
    final date = TextEditingController(
      text: DateTime.now().toIso8601String().substring(0, 10),
    );
    final reason = TextEditingController();
    final successor = ValueNotifier<String?>(null);
    final others = _staying
        .where((item) => item['id'] != occupancy['id'])
        .toList();
    final needsSuccessor =
        occupancy['responsible'] == true && others.isNotEmpty;
    final accepted = await _actionDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Keluarkan ${occupancy['name']}'),
        scrollable: true,
        insetPadding: const EdgeInsets.all(16),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: date,
                decoration: const InputDecoration(
                  labelText: 'Tanggal keluar sebenarnya (YYYY-MM-DD)',
                ),
              ),
              if (needsSuccessor)
                ValueListenableBuilder<String?>(
                  valueListenable: successor,
                  builder: (context, value, child) =>
                      DropdownButtonFormField<String>(
                        initialValue: value,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Penanggung jawab berikutnya',
                        ),
                        items: others
                            .map(
                              (item) => DropdownMenuItem(
                                value: item['resident_id'] as String,
                                child: Text('${item['name']}'),
                              ),
                            )
                            .toList(),
                        onChanged: (value) => successor.value = value,
                      ),
                ),
              TextField(
                controller: reason,
                decoration: const InputDecoration(labelText: 'Alasan'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan keluar'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        await _write(
          'POST',
          '/leases/${widget.id}/occupancies/${occupancy['id']}/exit',
          {
            'exited_on': date.text.trim(),
            'successor_resident_id': successor.value,
            'reason': reason.text.trim(),
          },
        );
        await _load();
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
    date.dispose();
    reason.dispose();
    successor.dispose();
  }

  Future<void> _extend() async {
    var periods = '1';
    final accepted = await _actionDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Perpanjang kontrak'),
        scrollable: true,
        insetPadding: const EdgeInsets.all(16),
        content: TextFormField(
          initialValue: periods,
          onChanged: (value) => periods = value,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Jumlah periode penuh'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Perpanjang'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        await _write('POST', '/leases/${widget.id}/extend', {
          'periods': int.parse(periods.trim()),
          'expected_version': _lease!['version'],
        });
        await _load();
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
  }

  Future<void> _changeResponsible() async {
    final current = _responsibleOccupancy;
    final options = _staying
        .where((item) => item['id'] != current?['id'])
        .toList();
    if (options.isEmpty) return;
    final selected = ValueNotifier<String?>(options.first['id'] as String);
    final reason = TextEditingController();
    final accepted = await _actionDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Ganti penanggung jawab'),
        scrollable: true,
        insetPadding: const EdgeInsets.all(16),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ValueListenableBuilder<String?>(
              valueListenable: selected,
              builder: (context, value, child) =>
                  DropdownButtonFormField<String>(
                    initialValue: value,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Penghuni'),
                    items: options
                        .map(
                          (item) => DropdownMenuItem(
                            value: item['id'] as String,
                            child: Text('${item['name']}'),
                          ),
                        )
                        .toList(),
                    onChanged: (value) => selected.value = value,
                  ),
            ),
            TextField(
              controller: reason,
              decoration: const InputDecoration(labelText: 'Alasan'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        await _write('POST', '/leases/${widget.id}/responsible', {
          'occupancy_id': selected.value,
          'reason': reason.text.trim(),
        });
        await _load();
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
    reason.dispose();
    selected.dispose();
  }

  Future<void> _replace() async {
    final departed = (_lease!['occupancies'] as List)
        .map((e) => Map<String, dynamic>.from(e))
        .where((item) => item['state'] == 'EXITED')
        .toList();
    if (departed.isEmpty) return;
    final currentIds = _staying.map((item) => item['resident_id']).toSet();
    final choices = _residents
        .where((item) => !currentIds.contains(item['id']))
        .toList();
    if (choices.isEmpty) return;
    final predecessor = ValueNotifier<String?>(departed.last['id'] as String);
    final resident = ValueNotifier<String?>(choices.first['id'] as String);
    final date = TextEditingController(
      text: DateTime.now().toIso8601String().substring(0, 10),
    );
    final reason = TextEditingController();
    final accepted = await _actionDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Tambah penghuni pengganti'),
        scrollable: true,
        insetPadding: const EdgeInsets.all(16),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ValueListenableBuilder<String?>(
                valueListenable: predecessor,
                builder: (context, value, child) => DropdownButtonFormField<String>(
                  initialValue: value,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Menggantikan'),
                  items: departed
                      .map(
                        (item) => DropdownMenuItem(
                          value: item['id'] as String,
                          child: Text(
                            '${item['name']} • keluar ${shortDate(item['exited_on'])}',
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (value) => predecessor.value = value,
                ),
              ),
              ValueListenableBuilder<String?>(
                valueListenable: resident,
                builder: (context, value, child) =>
                    DropdownButtonFormField<String>(
                      initialValue: value,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Penghuni baru',
                      ),
                      items: choices
                          .map(
                            (item) => DropdownMenuItem(
                              value: item['id'] as String,
                              child: Text('${item['name']}'),
                            ),
                          )
                          .toList(),
                      onChanged: (value) => resident.value = value,
                    ),
              ),
              TextField(
                controller: date,
                decoration: const InputDecoration(
                  labelText: 'Tanggal masuk (YYYY-MM-DD)',
                ),
              ),
              TextField(
                controller: reason,
                decoration: const InputDecoration(labelText: 'Alasan'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan pengganti'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        await _write('POST', '/leases/${widget.id}/occupancies', {
          'resident_id': resident.value,
          'entered_on': date.text.trim(),
          'predecessor_occupancy_id': predecessor.value,
          'reason': reason.text.trim(),
        });
        await _load();
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
    predecessor.dispose();
    resident.dispose();
    date.dispose();
    reason.dispose();
  }

  Future<void> _continue() async {
    final staying = _staying;
    final package = ValueNotifier<String?>(_lease!['package_id'] as String);
    final start = TextEditingController(
      text: '${_lease!['effective_ends_on']}',
    );
    final periods = TextEditingController(text: '1');
    final price = TextEditingController(
      text: '${_lease!['period_price_snapshot']}',
    );
    final responsible = ValueNotifier<String?>(
      staying.firstWhere(
            (item) => item['responsible'] == true,
            orElse: () => staying.first,
          )['resident_id']
          as String,
    );
    final reason = TextEditingController();
    final accepted = await _actionDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Kontrak lanjutan'),
        scrollable: true,
        insetPadding: const EdgeInsets.all(16),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ValueListenableBuilder<String?>(
                valueListenable: package,
                builder: (context, value, child) => DropdownButtonFormField<String>(
                  initialValue: value,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Paket baru'),
                  items: _packages
                      .map(
                        (item) => DropdownMenuItem(
                          value: item['id'] as String,
                          child: Text(
                            '${item['occupant_type']} orang / ${item['period_months']} bulan',
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (value) => package.value = value,
                ),
              ),
              TextField(
                controller: start,
                decoration: const InputDecoration(
                  labelText: 'Tanggal mulai (YYYY-MM-DD)',
                ),
              ),
              TextField(
                controller: periods,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Jumlah periode'),
              ),
              TextField(
                controller: price,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Harga per periode',
                ),
              ),
              ValueListenableBuilder<String?>(
                valueListenable: responsible,
                builder: (context, value, child) =>
                    DropdownButtonFormField<String>(
                      initialValue: value,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Penanggung jawab',
                      ),
                      items: staying
                          .map(
                            (item) => DropdownMenuItem(
                              value: item['resident_id'] as String,
                              child: Text('${item['name']}'),
                            ),
                          )
                          .toList(),
                      onChanged: (value) => responsible.value = value,
                    ),
              ),
              TextField(
                controller: reason,
                decoration: const InputDecoration(labelText: 'Alasan'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Simpan lanjutan'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        final created = await _write('POST', '/leases/${widget.id}/continue', {
          'package_id': package.value,
          'starts_on': start.text.trim(),
          'periods': int.parse(periods.text.trim()),
          'price': int.parse(price.text.trim()),
          'resident_ids': staying.map((item) => item['resident_id']).toList(),
          'responsible_resident_id': responsible.value,
          'reason': reason.text.trim(),
        });
        if (mounted) context.go('/leases/${created['id']}');
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
    package.dispose();
    start.dispose();
    periods.dispose();
    price.dispose();
    responsible.dispose();
    reason.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final lease = _lease;
    final ended = lease?['status'] == 'ENDED';
    return BusinessPage(
      title: 'Detail kontrak',
      subtitle: lease == null ? null : 'Kamar ${lease['room_number']}',
      preparation: false,
      child: ListView(
        padding: pagePadding(context),
        children: [
          if (_busy) const LinearProgressIndicator(),
          if (_error != null) ...[
            Text(_error!),
            TextButton(onPressed: _load, child: const Text('Muat ulang')),
          ],
          if (lease != null) ...[
            Text(
              'Kontrak ${leaseStatus(lease['status'])}',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 24),
            const Text(
              'Masa sewa',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            _facts([
              (
                'Paket',
                '${lease['occupant_type_snapshot']} orang · ${lease['period_months_snapshot']} bulan',
              ),
              (
                'Kontrak',
                dates.rangeLabel(
                  lease['starts_on'],
                  lease['effective_ends_on'],
                ),
              ),
              (
                'Harga per periode',
                formatRupiah(lease['period_price_snapshot']),
              ),
            ]),
            if (lease['early_end_reason'] != null)
              Text('Akhir lebih awal: ${lease['early_end_reason']}'),
            const SizedBox(height: 24),
            const Text(
              'Tindakan kontrak',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.tonal(
                  onPressed: _busy || ended ? null : _extend,
                  child: const Text('Perpanjang'),
                ),
                FilledButton.tonal(
                  onPressed: _busy || _staying.length < 2
                      ? null
                      : _changeResponsible,
                  child: const Text('Ganti penanggung jawab'),
                ),
                FilledButton.tonal(
                  onPressed: _busy || ended ? null : _replace,
                  child: const Text('Tambah pengganti'),
                ),
                FilledButton.tonal(
                  onPressed: _busy || !ended || _staying.isEmpty
                      ? null
                      : _continue,
                  child: const Text('Kontrak lanjutan'),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Text('Penghuni', style: Theme.of(context).textTheme.titleMedium),
            if ((lease['occupancies'] as List).isEmpty)
              const Text('Belum ada penghuni tercatat.'),
            for (final occupancy in (lease['occupancies'] as List))
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        '${occupancy['name']}',
                        style: const TextStyle(
                          fontSize: 16,
                          height: 1.2,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '${occupancy['responsible'] == true ? 'Penanggung jawab · ' : ''}${occupancy['state'] == 'STAYING' ? 'Masih tinggal' : 'Keluar'}',
                        style: const TextStyle(
                          fontSize: 14,
                          color: KamarthaColors.secondary,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Masuk ${shortDate(occupancy['entered_on'])}'
                        '${occupancy['exited_on'] != null ? ' · keluar ${shortDate(occupancy['exited_on'])}' : ''}',
                        style: const TextStyle(
                          fontSize: 14,
                          color: KamarthaColors.secondary,
                        ),
                      ),
                      if (occupancy['state'] == 'STAYING')
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: _busy
                                ? null
                                : () => _exit(
                                    Map<String, dynamic>.from(occupancy),
                                  ),
                            child: const Text('Keluar'),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 20),
            Text('Tagihan', style: Theme.of(context).textTheme.titleMedium),
            if ((lease['invoices'] as List).isEmpty)
              const Text('Belum ada tagihan tercatat.'),
            for (final invoice in (lease['invoices'] as List))
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: _facts([
                  (
                    'Periode',
                    dates.rangeLabel(
                      invoice['period_start'],
                      invoice['period_end'],
                    ),
                  ),
                  ('Nominal', formatRupiah(invoice['amount'])),
                  ('Dibayar', formatRupiah(invoice['paid_total'])),
                  ('Sisa', formatRupiah(invoice['remaining'])),
                  ('Status', invoiceStatus(invoice['payment_status'])),
                ]),
              ),
          ],
        ],
      ),
    );
  }

  Widget _facts(List<(String, String)> rows) => Card(
    clipBehavior: Clip.antiAlias,
    child: Column(
      children: [
        for (var i = 0; i < rows.length; i++) ...[
          if (i > 0) const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    rows[i].$1,
                    style: const TextStyle(
                      fontSize: 14,
                      color: KamarthaColors.secondary,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Flexible(
                  child: Text(
                    rows[i].$2,
                    textAlign: TextAlign.end,
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    ),
  );
}
