import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/dates.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';
import '../../../app/theme/kamartha_theme.dart';

class MasterPage extends ConsumerStatefulWidget {
  const MasterPage({
    super.key,
    required this.rooms,
    this.id,
    this.initialQuery = '',
  });
  final bool rooms;
  final String? id;
  final String initialQuery;
  @override
  ConsumerState<MasterPage> createState() => _MasterPageState();
}

class _MasterPageState extends ConsumerState<MasterPage> {
  List<Map<String, dynamic>> _items = [];
  bool _busy = true, _preparation = true, _more = false;
  String? _error;
  String _filter = 'ALL';
  int _total = 0;
  final _search = TextEditingController();
  String get _path => widget.rooms ? '/rooms' : '/residents';

  @override
  void initState() {
    super.initState();
    _search.text = widget.initialQuery;
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
      if (widget.id != null) {
        final item = await repository.get('$_path/${widget.id}');
        if (mounted) {
          setState(() {
            _items = [item];
            _preparation = settings['mode'] == 'PREPARATION';
          });
        }
      } else {
        final data = await repository.get(_path, {
          'q': _search.text,
          'limit': 20,
          'offset': append ? _items.length : 0,
        });
        if (mounted) {
          setState(() {
            final items = (data['items'] as List)
                .map((e) => Map<String, dynamic>.from(e))
                .toList();
            _items = append ? [..._items, ...items] : items;
            _more = data['pagination']['has_more'] == true;
            _total = data['pagination']['total'] as int? ?? _items.length;
            _preparation = settings['mode'] == 'PREPARATION';
          });
        }
      }
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _edit([Map<String, dynamic>? item]) async {
    final saved = widget.rooms
        ? await Navigator.of(context).push<bool>(
            MaterialPageRoute(
              builder: (_) => _MasterForm(rooms: true, item: item),
            ),
          )
        : await showDialog<bool>(
            context: context,
            builder: (_) => _MasterForm(rooms: false, item: item),
          );
    if (saved == true && mounted) await _load();
  }

  Future<void> _selectFilter(String value) async {
    setState(() => _filter = value);
    while (_more && _items.length < _total && mounted) {
      await _load(append: true);
    }
  }

  Color _statusColor(dynamic status) => switch (status) {
    'OCCUPIED' => KamarthaColors.success,
    'NEEDS_CONFIRMATION' => KamarthaColors.warning,
    _ => KamarthaColors.secondary,
  };

  @override
  Widget build(BuildContext context) {
    if (widget.id != null) return _detailPage();
    final horizontal = pagePadding(context).left;
    final visible = widget.rooms && _filter != 'ALL'
        ? _items.where((item) => item['occupancy_status'] == _filter).toList()
        : _items;
    final occupied = _items
        .where((i) => i['occupancy_status'] == 'OCCUPIED')
        .length;
    final empty = _items.where((i) => i['occupancy_status'] == 'EMPTY').length;
    final confirmation = _items
        .where((i) => i['occupancy_status'] == 'NEEDS_CONFIRMATION')
        .length;
    final allLoaded = _items.length >= _total;
    return BusinessPage(
      title: widget.rooms ? 'Kamar' : 'Penghuni',
      preparation: _preparation,
      actions: [
        TextButton(
          onPressed: _busy ? null : () => _edit(),
          child: const Text(
            '+ Tambah',
            style: TextStyle(
              color: KamarthaColors.brand,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
      child: ListView(
        padding: EdgeInsets.fromLTRB(horizontal, 8, horizontal, 24),
        children: [
          TextField(
            controller: _search,
            style: const TextStyle(fontSize: 16),
            decoration: InputDecoration(
              hintText: widget.rooms
                  ? 'Cari nomor kamar'
                  : 'Cari nama penghuni',
              prefixIcon: const Icon(Icons.search, size: 24),
              prefixIconConstraints: const BoxConstraints(minWidth: 48),
              border: InputBorder.none,
              enabledBorder: InputBorder.none,
              focusedBorder: InputBorder.none,
              filled: false,
              contentPadding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onSubmitted: (_) => _load(),
          ),
          if (widget.rooms) ...[
            const SizedBox(height: 8),
            Text(
              allLoaded
                  ? '$_total kamar · $occupied dihuni · $empty kosong · $confirmation konfirmasi'
                  : '$_total kamar · ${_items.length} dimuat',
              style: const TextStyle(
                fontSize: 14,
                height: 1.2,
                color: KamarthaColors.secondary,
              ),
            ),
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, box) {
                final stacked =
                    box.maxWidth < 280 ||
                    MediaQuery.textScalerOf(context).scale(16) > 20;
                return Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final entry in [
                      ('Semua', 'ALL'),
                      ('Dihuni', 'OCCUPIED'),
                      ('Kosong', 'EMPTY'),
                      ('Perlu konfirmasi', 'NEEDS_CONFIRMATION'),
                    ])
                      SizedBox(
                        width: stacked || entry.$2 == 'NEEDS_CONFIRMATION'
                            ? box.maxWidth
                            : (box.maxWidth - 16) / 3,
                        child: _pill(entry.$1, entry.$2),
                      ),
                  ],
                );
              },
            ),
            const SizedBox(height: 16),
          ] else
            const SizedBox(height: 12),
          if (_busy) const LinearProgressIndicator(),
          if (_error != null) ...[
            Text(_error!),
            TextButton(
              onPressed: () => _load(),
              child: const Text('Coba lagi'),
            ),
          ],
          if (!_busy && _error == null && visible.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Text('Belum ada data yang cocok.'),
            ),
          if (visible.isNotEmpty)
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: KamarthaColors.border),
              ),
              clipBehavior: Clip.antiAlias,
              child: Column(
                children: [
                  for (var i = 0; i < visible.length; i++) ...[
                    if (i > 0) const Divider(),
                    _row(visible[i]),
                  ],
                ],
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

  Widget _pill(String label, String value) {
    final selected = _filter == value;
    return TextButton(
      style: TextButton.styleFrom(
        minimumSize: const Size(0, 48),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: StadiumBorder(
          side: BorderSide(
            color: selected ? KamarthaColors.activeTab : KamarthaColors.border,
          ),
        ),
        backgroundColor: selected ? KamarthaColors.activeTab : Colors.white,
        foregroundColor: selected ? Colors.white : KamarthaColors.secondary,
      ),
      onPressed: _busy ? null : () => _selectFilter(value),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 16,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _row(Map<String, dynamic> item) {
    final rooms = widget.rooms;
    final name = '${item['name'] ?? ''}';
    return InkWell(
      onTap: () => context.push('$_path/${item['id']}'),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 52,
              constraints: const BoxConstraints(minHeight: 48),
              padding: const EdgeInsets.all(4),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: KamarthaColors.chip,
                borderRadius: BorderRadius.circular(10),
              ),
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  rooms
                      ? '${item['number']}'
                      : (name.trim().isEmpty
                            ? '?'
                            : name.trim()[0].toUpperCase()),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.2,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    rooms ? 'Kamar ${item['number']}' : name,
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 6),
                  if (rooms) ...[
                    Text(
                      '${item['room_type']} · kapasitas ${item['supported_occupants']}',
                      style: const TextStyle(
                        fontSize: 14,
                        height: 1.2,
                        color: KamarthaColors.secondary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: _statusColor(item['occupancy_status']),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            _status(item['occupancy_status']),
                            style: TextStyle(
                              fontSize: 14,
                              height: 1.2,
                              fontWeight: FontWeight.w600,
                              color: _statusColor(item['occupancy_status']),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ] else ...[
                    Text(
                      '${item['identity_type']}: ${item['identity_number']}',
                      style: const TextStyle(
                        fontSize: 14,
                        height: 1.2,
                        color: KamarthaColors.secondary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'WhatsApp: ${item['whatsapp_number'] ?? 'Belum diisi'}',
                      style: const TextStyle(
                        fontSize: 14,
                        height: 1.2,
                        color: KamarthaColors.secondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(
              Icons.chevron_right,
              size: 18,
              color: KamarthaColors.secondary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _detailPage() {
    final item = _items.isEmpty ? null : _items.first;
    final rooms = widget.rooms;
    final info = item == null
        ? const <(String, String)>[]
        : rooms
        ? <(String, String)>[
            ('Tipe kamar', '${item['room_type']}'),
            ('Harga referensi', formatRupiah(item['reference_price'])),
            (
              'Untuk kontrak baru',
              item['is_available_for_new_lease'] == true ? 'Ya' : 'Tidak',
            ),
          ]
        : <(String, String)>[
            (
              'Identitas',
              '${item['identity_type']}: ${item['identity_number']}',
            ),
            ('WhatsApp', '${item['whatsapp_number'] ?? 'Belum diisi'}'),
            ('Catatan', '${item['notes'] ?? '—'}'),
          ];
    return BusinessPage(
      title: rooms ? 'Detail kamar' : 'Detail penghuni',
      preparation: _preparation,
      actions: item == null
          ? []
          : [
              IconButton(
                tooltip: 'Ubah',
                onPressed: _busy ? null : () => _edit(item),
                icon: const Icon(
                  Icons.edit_outlined,
                  color: KamarthaColors.primary,
                ),
              ),
            ],
      child: ListView(
        padding: pagePadding(context),
        children: [
          if (_busy) const LinearProgressIndicator(),
          if (_error != null) ...[
            Text(_error!),
            TextButton(
              onPressed: () => _load(),
              child: const Text('Coba lagi'),
            ),
          ],
          if (item != null) ...[
            Text(
              rooms ? '${item['number']}' : '${item['name']}',
              style: const TextStyle(
                fontSize: 30,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (rooms) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _statusColor(item['occupancy_status']),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '${_status(item['occupancy_status'])} · kapasitas ${item['supported_occupants']}',
                    style: TextStyle(
                      fontSize: 16,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                      color: _statusColor(item['occupancy_status']),
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 24),
            _infoTable(info),
            if (rooms) ...[
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
              for (final lease in (item['leases'] as List? ?? [])) ...[
                _infoTable([
                  (
                    'Paket',
                    '${lease['occupant_type_snapshot']} orang · ${lease['period_months_snapshot']} bulan',
                  ),
                  (
                    'Kontrak',
                    rangeLabel(lease['starts_on'], lease['effective_ends_on']),
                  ),
                  (
                    'Harga per periode',
                    formatRupiah(lease['period_price_snapshot']),
                  ),
                ]),
                const SizedBox(height: 12),
              ],
              if ((item['leases'] as List? ?? []).isEmpty)
                const Text('Belum ada kontrak tercatat.'),
            ],
            if (!rooms) ...[
              const SizedBox(height: 24),
              const Text(
                'Riwayat penghunian',
                style: TextStyle(
                  fontSize: 20,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 12),
              if ((item['history'] as List? ?? []).isEmpty)
                const Text('Belum ada riwayat penghunian.'),
              for (final history in (item['history'] as List? ?? [])) ...[
                _infoTable([
                  ('Kamar', '${history['room_number']}'),
                  (
                    'Keadaan',
                    history['state'] == 'STAYING'
                        ? 'Masih tinggal'
                        : 'Sudah keluar',
                  ),
                  ('Tanggal masuk', shortDate(history['entered_on'])),
                  if (history['state'] != 'STAYING')
                    (
                      'Tanggal keluar',
                      history['exited_on'] == null
                          ? 'Tanggal tidak diketahui'
                          : shortDate(history['exited_on']),
                    ),
                  (
                    'Kontrak',
                    rangeLabel(
                      history['starts_on'],
                      history['effective_ends_on'],
                    ),
                  ),
                ]),
                if (history['lease_id'] != null)
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: () =>
                          context.push('/leases/${history['lease_id']}'),
                      child: const Text('Lihat kontrak'),
                    ),
                  ),
                const SizedBox(height: 12),
              ],
            ],
            const SizedBox(height: 24),
            TextButton(
              onPressed: () => context.go(_path),
              child: const Text('Kembali ke daftar'),
            ),
          ],
        ],
      ),
    );
  }

  Widget _infoTable(List<(String, String)> rows) => Container(
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: KamarthaColors.border),
    ),
    child: Column(
      children: [
        for (var i = 0; i < rows.length; i++) ...[
          if (i > 0) const Divider(),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
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

  String _status(dynamic status) => switch (status) {
    'OCCUPIED' => 'Dihuni',
    'NEEDS_CONFIRMATION' => 'Perlu konfirmasi',
    _ => 'Kosong',
  };
}

class _MasterForm extends ConsumerStatefulWidget {
  const _MasterForm({required this.rooms, this.item});
  final bool rooms;
  final Map<String, dynamic>? item;
  @override
  ConsumerState<_MasterForm> createState() => _MasterFormState();
}

class _MasterFormState extends ConsumerState<_MasterForm> {
  String? _key;
  Map<String, dynamic>? _lastPayload;
  final _form = GlobalKey<FormState>();
  final _fields = <String, TextEditingController>{};
  bool _busy = false, _available = true;
  int _capacity = 1;
  String? _error;
  @override
  void initState() {
    super.initState();
    for (final key
        in widget.rooms
            ? ['number', 'room_type', 'reference_price']
            : [
                'name',
                'identity_type',
                'identity_number',
                'whatsapp_number',
                'notes',
              ]) {
      final value = key == 'room_type'
          ? 'Standar'
          : widget.item?[key] ?? (key == 'reference_price' ? 700000 : '');
      _fields[key] = TextEditingController(text: '$value');
    }
    _capacity = widget.item?['supported_occupants'] ?? 2;
    _available = widget.item?['is_available_for_new_lease'] ?? true;
  }

  @override
  void dispose() {
    for (final field in _fields.values) {
      field.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final data = <String, dynamic>{
      for (final e in _fields.entries) e.key: e.value.text.trim(),
    };
    if (widget.rooms) {
      data['reference_price'] = int.parse(data['reference_price']);
      data['supported_occupants'] = _capacity;
      data['is_available_for_new_lease'] = _available;
    } else {
      if (data['whatsapp_number'] == '') data['whatsapp_number'] = null;
      if (data['notes'] == '') data['notes'] = null;
    }
    try {
      if (_lastPayload == null ||
          data.entries.any((e) => _lastPayload![e.key] != e.value)) {
        _key = newRequestKey();
        _lastPayload = Map.of(data);
      }
      final path = widget.rooms ? '/rooms' : '/residents';
      await ref
          .read(businessProvider)
          .write(
            widget.item == null ? 'POST' : 'PATCH',
            widget.item == null ? path : '$path/${widget.item!['id']}',
            data,
            key: _key,
          );
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

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: widget.rooms
        ? _roomPage(context)
        : AlertDialog(
            scrollable: true,
            insetPadding: const EdgeInsets.all(16),
            title: Text(
              '${widget.item == null ? 'Tambah' : 'Ubah'} ${widget.rooms ? 'kamar' : 'penghuni'}',
            ),
            content: SizedBox(
              width: 480,
              child: SingleChildScrollView(
                child: Form(
                  key: _form,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (_error != null) Text(_error!),
                      for (final e in _fields.entries)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: TextFormField(
                            controller: e.value,
                            enabled: !_busy,
                            maxLines: e.key == 'notes' ? 3 : 1,
                            decoration: InputDecoration(
                              labelText: _labels[e.key],
                            ),
                            validator: (value) {
                              if ([
                                'notes',
                                'whatsapp_number',
                              ].contains(e.key)) {
                                return null;
                              }
                              if ((value ?? '').trim().isEmpty) {
                                return 'Wajib diisi.';
                              }
                              if (e.key == 'reference_price') {
                                final money = int.tryParse(value!);
                                if (money == null ||
                                    money <= 0 ||
                                    money > 1000000000000) {
                                  return 'Masukkan rupiah bulat 1–1.000.000.000.000.';
                                }
                              }
                              return null;
                            },
                          ),
                        ),
                      if (widget.rooms) ...[
                        DropdownButtonFormField<int>(
                          initialValue: _capacity,
                          isExpanded: true,
                          decoration: const InputDecoration(
                            labelText: 'Dukungan penghuni',
                          ),
                          items: [1, 2]
                              .map(
                                (n) => DropdownMenuItem(
                                  value: n,
                                  child: Text('$n orang'),
                                ),
                              )
                              .toList(),
                          onChanged: _busy
                              ? null
                              : (n) => setState(() => _capacity = n!),
                        ),
                        SwitchListTile(
                          title: const Text('Boleh untuk kontrak baru'),
                          value: _available,
                          onChanged: _busy
                              ? null
                              : (v) => setState(() => _available = v),
                        ),
                        const Text(
                          'Harga referensi bukan harga kontrak. Harga kesepakatan tetap diisi pada berkas.',
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
            actions: [
              TextButton(
                onPressed: _busy ? null : () => Navigator.pop(context),
                child: const Text('Batal'),
              ),
              FilledButton(
                onPressed: _busy ? null : _save,
                child: Text(_busy ? 'Menyimpan…' : 'Simpan'),
              ),
            ],
          ),
  );

  Widget _roomField(String key) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          _labels[key]!,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 8),
        Semantics(
          label: _labels[key],
          child: TextFormField(
            key: ValueKey('room-$key'),
            controller: _fields[key],
            enabled: !_busy,
            readOnly: key == 'room_type',
            keyboardType: key == 'reference_price'
                ? TextInputType.number
                : TextInputType.text,
            decoration: const InputDecoration(),
            validator: (value) {
              if ((value ?? '').trim().isEmpty) return 'Wajib diisi.';
              if (key == 'reference_price') {
                final amount = int.tryParse(value!);
                if (amount == null || amount <= 0 || amount > 1000000000000) {
                  return 'Masukkan rupiah bulat 1–1.000.000.000.000.';
                }
              }
              return null;
            },
          ),
        ),
      ],
    ),
  );

  Widget _roomPage(BuildContext context) => Scaffold(
    resizeToAvoidBottomInset: true,
    appBar: AppBar(
      toolbarHeight: 104,
      leading: IconButton(
        tooltip: 'Kembali',
        onPressed: _busy ? null : () => Navigator.pop(context),
        icon: const Icon(Icons.arrow_back),
      ),
      title: MediaQuery.withClampedTextScaling(
        maxScaleFactor: 1.3,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              widget.item == null ? 'Tambah kamar' : 'Ubah kamar',
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
            ),
            const Text(
              'Data kamar',
              style: TextStyle(fontSize: 14, color: KamarthaColors.secondary),
            ),
          ],
        ),
      ),
    ),
    body: SafeArea(
      child: Center(
        child: SizedBox(
          width: 640,
          child: Form(
            key: _form,
            child: ListView(
              padding: pagePadding(context),
              children: [
                if (_error != null)
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                _roomField('number'),
                if (widget.item?['room_type'] != null &&
                    widget.item?['room_type'] != 'Standar')
                  Text(
                    'Tipe lama: ${widget.item!['room_type']}. Menyimpan formulir akan mengubah tipe ke Standar.',
                  ),
                _roomField('room_type'),
                const Text(
                  'Dukungan penghuni',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final capacity in [1, 2])
                      ChoiceChip(
                        label: Text('$capacity orang'),
                        selected: _capacity == capacity,
                        onSelected: _busy
                            ? null
                            : (_) => setState(() => _capacity = capacity),
                      ),
                  ],
                ),
                const SizedBox(height: 20),
                _roomField('reference_price'),
                const Text('Bukan harga kontrak. Harga disepakati saat sewa.'),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Boleh untuk kontrak baru'),
                  value: _available,
                  onChanged: _busy
                      ? null
                      : (value) => setState(() => _available = value),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
    bottomNavigationBar: SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: FilledButton(
          onPressed: _busy ? null : _save,
          child: Text(_busy ? 'Menyimpan…' : 'Simpan kamar'),
        ),
      ),
    ),
  );

  static const _labels = {
    'number': 'Nomor kamar',
    'room_type': 'Tipe kamar',
    'reference_price': 'Harga referensi (rupiah)',
    'name': 'Nama penghuni',
    'identity_type': 'Jenis identitas',
    'identity_number': 'Nomor identitas',
    'whatsapp_number': 'WhatsApp (opsional)',
    'notes': 'Catatan (opsional)',
  };
}
