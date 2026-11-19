import 'package:file_picker/file_picker.dart';
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

String categoryLabel(Object? value) => switch ('$value') {
  'ELECTRICITY' => 'Listrik',
  'WATER' => 'Air',
  'INTERNET' => 'Internet/Wi-Fi',
  'REPAIR' => 'Perbaikan',
  'SALARY' => 'Gaji',
  _ => 'Lainnya',
};

String longDate(Object? value) {
  final date = DateTime.tryParse('$value');
  if (date == null) return value == null ? '—' : '$value';
  const months = [
    'Januari',
    'Februari',
    'Maret',
    'April',
    'Mei',
    'Juni',
    'Juli',
    'Agustus',
    'September',
    'Oktober',
    'November',
    'Desember',
  ];
  return '${date.day} ${months[date.month - 1]} ${date.year}';
}

class ExpensesPage extends ConsumerStatefulWidget {
  const ExpensesPage({super.key});
  @override
  ConsumerState<ExpensesPage> createState() => _ExpensesPageState();
}

class _ExpensesPageState extends ConsumerState<ExpensesPage> {
  List<Map<String, dynamic>> _items = [];
  bool _busy = true, _more = false;
  String _status = '';
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool append = false}) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final data = await ref.read(businessProvider).get('/expenses', {
        'status': _status,
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
      });
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _edit([Map<String, dynamic>? item]) async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (_) => _ExpenseForm(item: item),
    );
    if (saved == true && mounted) await _load();
  }

  Future<void> _open(Map<String, dynamic> item) async {
    await context.push('/expenses/${item['id']}');
    if (mounted) await _load();
  }

  Future<void> _cancel(Map<String, dynamic> item) async {
    var reason = '';
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Batalkan pengeluaran?'),
        content: TextField(
          onChanged: (value) => reason = value,
          decoration: const InputDecoration(labelText: 'Alasan pembatalan'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Batalkan pengeluaran'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        await ref.read(businessProvider).write(
          'POST',
          '/expenses/${item['id']}/cancel',
          {'expected_version': item['version'], 'reason': reason.trim()},
          key: newRequestKey(),
        );
        await _load();
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
  }

  IconData _icon(Object? category) => switch ('$category') {
    'ELECTRICITY' => Icons.bolt_outlined,
    'WATER' => Icons.water_drop_outlined,
    'INTERNET' => Icons.wifi,
    'REPAIR' => Icons.build_outlined,
    'SALARY' => Icons.payments_outlined,
    _ => Icons.receipt_long_outlined,
  };

  String _longDate(String value) => longDate(value);

  @override
  Widget build(BuildContext context) {
    final horizontal = pagePadding(context).left;
    final total = _items
        .where((item) => item['status'] == 'VALID')
        .fold<int>(0, (sum, item) => sum + (item['amount'] as int? ?? 0));
    final dates = _items.map((item) => '${item['expense_on']}').toSet().toList()
      ..sort((a, b) => b.compareTo(a));
    return BusinessPage(
      title: 'Pengeluaran',
      subtitle: 'Dari Menu',
      preparation: false,
      child: Column(
        children: [
          Expanded(
            child: ListView(
              padding: EdgeInsets.fromLTRB(horizontal, 16, horizontal, 8),
              children: [
                Text(
                  _more ? 'Total data dimuat' : 'Total pengeluaran',
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.2,
                    color: KamarthaColors.secondary,
                  ),
                ),
                const SizedBox(height: 8),
                if (!_busy && _error == null)
                  Text(
                    formatRupiah(total),
                    style: const TextStyle(
                      fontSize: 30,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final entry in [
                      ('Semua', ''),
                      ('Valid', 'VALID'),
                      ('Batal', 'CANCELLED'),
                    ])
                      _pill(entry.$1, entry.$2),
                  ],
                ),
                const SizedBox(height: 16),
                if (_busy) const LinearProgressIndicator(),
                if (_error != null) ...[
                  Text(_error!),
                  TextButton(
                    onPressed: () => _load(),
                    child: const Text('Coba lagi'),
                  ),
                ],
                if (!_busy && _error == null && _items.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(24),
                    child: Text('Belum ada pengeluaran pada filter ini.'),
                  ),
                for (final date in dates) ...[
                  Padding(
                    padding: const EdgeInsets.only(top: 8, bottom: 12),
                    child: Text(
                      _longDate(date),
                      style: const TextStyle(
                        fontSize: 16,
                        height: 1.2,
                        fontWeight: FontWeight.w600,
                        color: KamarthaColors.secondary,
                      ),
                    ),
                  ),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: KamarthaColors.border),
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: Column(
                      children: [
                        for (
                          var i = 0;
                          i <
                              _items
                                  .where((item) => item['expense_on'] == date)
                                  .length;
                          i++
                        ) ...[
                          if (i > 0) const Divider(),
                          _row(
                            _items
                                .where((item) => item['expense_on'] == date)
                                .elementAt(i),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
                if (_more)
                  TextButton(
                    onPressed: _busy ? null : () => _load(append: true),
                    child: const Text('Muat berikutnya'),
                  ),
              ],
            ),
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(horizontal, 8, horizontal, 8),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _busy ? null : () => _edit(),
                child: const Text('Catat pengeluaran'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _pill(String label, String value) {
    final selected = _status == value;
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
      onPressed: _busy
          ? null
          : () {
              setState(() => _status = value);
              _load();
            },
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

  Widget _row(Map<String, dynamic> item) => LayoutBuilder(
    builder: (context, box) {
      final money = formatRupiah(item['amount']);
      final inline =
          MediaQuery.textScalerOf(context).scale(16) <= 20 &&
          box.maxWidth >= 300;
      return Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: KamarthaColors.chip,
                shape: BoxShape.circle,
              ),
              child: Icon(
                _icon(item['category']),
                size: 24,
                color: KamarthaColors.secondary,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Semantics(
                container: true,
                button: true,
                label:
                    'Buka detail pengeluaran ${categoryLabel(item['category'])}, ${item['description']}, $money',
                onTap: () => _open(item),
                excludeSemantics: true,
                child: InkWell(
                  onTap: () => _open(item),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        categoryLabel(item['category']),
                        style: const TextStyle(
                          fontSize: 16,
                          height: 1.2,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${item['description']}',
                        style: const TextStyle(
                          fontSize: 14,
                          height: 1.2,
                          color: KamarthaColors.secondary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item['status'] == 'VALID' ? 'Valid' : 'Batal',
                        style: TextStyle(
                          fontSize: 14,
                          height: 1.2,
                          fontWeight: FontWeight.w600,
                          color: item['status'] == 'VALID'
                              ? KamarthaColors.success
                              : KamarthaColors.secondary,
                        ),
                      ),
                      if (!inline) ...[
                        const SizedBox(height: 8),
                        Text(
                          money,
                          style: const TextStyle(
                            fontSize: 16,
                            height: 1.2,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            if (inline)
              Text(
                money,
                style: const TextStyle(
                  fontSize: 16,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                ),
              ),
            if (item['status'] == 'VALID')
              PopupMenuButton<String>(
                tooltip: 'Tindakan pengeluaran',
                icon: const Icon(
                  Icons.more_vert,
                  size: 18,
                  color: KamarthaColors.secondary,
                ),
                onSelected: (value) =>
                    value == 'edit' ? _edit(item) : _cancel(item),
                itemBuilder: (context) => const [
                  PopupMenuItem(value: 'edit', child: Text('Koreksi')),
                  PopupMenuItem(value: 'cancel', child: Text('Batalkan')),
                ],
              )
            else
              const Icon(
                Icons.chevron_right,
                size: 18,
                color: KamarthaColors.secondary,
              ),
          ],
        ),
      );
    },
  );
}

class ExpenseDetailPage extends ConsumerStatefulWidget {
  const ExpenseDetailPage({super.key, required this.id});
  final String id;
  @override
  ConsumerState<ExpenseDetailPage> createState() => _ExpenseDetailPageState();
}

class _ExpenseDetailPageState extends ConsumerState<ExpenseDetailPage> {
  Map<String, dynamic>? _item;
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
      final data = await ref
          .read(businessProvider)
          .get('/expenses/${widget.id}');
      if (mounted) setState(() => _item = data);
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _edit() async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (_) => _ExpenseForm(item: _item),
    );
    if (saved == true && mounted) await _load();
  }

  Future<void> _cancel() async {
    final item = _item!;
    var reason = '';
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Batalkan pengeluaran?'),
        content: TextField(
          onChanged: (value) => reason = value,
          decoration: const InputDecoration(labelText: 'Alasan pembatalan'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Batalkan pengeluaran'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      setState(() => _busy = true);
      try {
        await ref.read(businessProvider).write(
          'POST',
          '/expenses/${item['id']}/cancel',
          {'expected_version': item['version'], 'reason': reason.trim()},
          key: newRequestKey(),
        );
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
  }

  @override
  Widget build(BuildContext context) {
    final item = _item;
    final cancelled = item?['status'] == 'CANCELLED';
    final audits = (item?['audits'] as List? ?? []);
    return BusinessPage(
      title: 'Detail pengeluaran',
      subtitle: 'Dari Menu',
      preparation: false,
      child: Column(
        children: [
          Expanded(
            child: ListView(
              padding: pagePadding(context),
              children: [
                if (_busy) const LinearProgressIndicator(),
                if (_error != null) ...[
                  Text(_error!),
                  TextButton(onPressed: _load, child: const Text('Coba lagi')),
                ],
                if (item != null) ...[
                  Text(
                    formatRupiah(item['amount']),
                    style: const TextStyle(
                      fontSize: 30,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${categoryLabel(item['category'])} · ${longDate(item['expense_on'])}',
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.2,
                      color: KamarthaColors.secondary,
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Data pengeluaran',
                    style: TextStyle(
                      fontSize: 20,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _infoTable([
                    ('Kategori', categoryLabel(item['category'])),
                    ('Tanggal', longDate(item['expense_on'])),
                    ('Keterangan', '${item['description']}'),
                    (
                      'Bukti',
                      item['attachment'] == null ? 'Tidak ada' : 'Terlampir',
                    ),
                    if (cancelled) ('Status', 'Batal'),
                    if (cancelled &&
                        '${item['cancellation_reason'] ?? ''}'
                            .trim()
                            .isNotEmpty)
                      (
                        'Alasan pembatalan',
                        '${item['cancellation_reason']}'.trim(),
                      ),
                  ]),
                  const SizedBox(height: 24),
                  const Text(
                    'Riwayat perubahan',
                    style: TextStyle(
                      fontSize: 20,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (audits.isEmpty)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: KamarthaColors.border),
                      ),
                      child: const Text(
                        'Belum ada koreksi.',
                        style: TextStyle(
                          fontSize: 16,
                          height: 1.2,
                          color: KamarthaColors.secondary,
                        ),
                      ),
                    )
                  else
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: KamarthaColors.border),
                      ),
                      clipBehavior: Clip.antiAlias,
                      child: Column(
                        children: [
                          for (var i = 0; i < audits.length; i++) ...[
                            if (i > 0) const Divider(height: 1),
                            _auditRow(
                              Map<String, dynamic>.from(audits[i] as Map),
                            ),
                          ],
                        ],
                      ),
                    ),
                  const SizedBox(height: 16),
                  const Text(
                    'Biaya ini tidak menambah tagihan penghuni.',
                    style: TextStyle(
                      fontSize: 14,
                      height: 1.2,
                      color: KamarthaColors.secondary,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (item != null && !_busy)
            DecoratedBox(
              decoration: const BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: KamarthaColors.border)),
              ),
              child: SafeArea(
                top: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
                  child: Row(
                    children: [
                      Expanded(
                        child: SizedBox(
                          height: 48,
                          child: FilledButton(
                            style: FilledButton.styleFrom(
                              backgroundColor: KamarthaColors.warningBackground,
                              foregroundColor: KamarthaColors.warningText,
                            ),
                            onPressed: cancelled ? null : _edit,
                            child: const Text('Koreksi'),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: SizedBox(
                          height: 48,
                          child: OutlinedButton(
                            style: OutlinedButton.styleFrom(
                              foregroundColor: KamarthaColors.dangerText,
                              side: const BorderSide(
                                color: KamarthaColors.danger,
                              ),
                            ),
                            onPressed: cancelled ? null : _cancel,
                            child: const Text('Batalkan'),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
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

  Widget _auditRow(Map<String, dynamic> audit) {
    final label = audit['action'] == 'CANCEL' ? 'Dibatalkan' : 'Dikoreksi';
    final reason = '${audit['reason'] ?? ''}'.trim();
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$label · ${shortDate(audit['recorded_at'])}',
            style: const TextStyle(
              fontSize: 14,
              height: 1.2,
              color: KamarthaColors.secondary,
            ),
          ),
          if (reason.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(reason, style: const TextStyle(fontSize: 16, height: 1.2)),
          ],
        ],
      ),
    );
  }
}

class _ExpenseForm extends ConsumerStatefulWidget {
  const _ExpenseForm({this.item});
  final Map<String, dynamic>? item;
  @override
  ConsumerState<_ExpenseForm> createState() => _ExpenseFormState();
}

class _ExpenseFormState extends ConsumerState<_ExpenseForm> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _date;
  late final TextEditingController _amount;
  late final TextEditingController _description;
  late final TextEditingController _reason;
  String _category = 'OTHER';
  bool _busy = false, _uploading = false;
  String? _error, _attachmentId, _attachmentName;

  Future<void> _pickAttachment() async {
    final file = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'pdf'],
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();
    final extension = file.extension?.toLowerCase() ?? '';
    final mime = switch (extension) {
      'pdf' => 'application/pdf',
      'png' => 'image/png',
      _ => 'image/jpeg',
    };
    setState(() {
      _uploading = true;
      _error = null;
    });
    try {
      final data = await ref
          .read(businessProvider)
          .upload('/attachments', file.name, bytes, mime, key: newRequestKey());
      if (mounted) {
        setState(() {
          _attachmentId = data['id'] as String;
          _attachmentName = file.name;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _date = TextEditingController(
      text:
          '${widget.item?['expense_on'] ?? DateTime.now().toIso8601String().substring(0, 10)}',
    );
    _amount = TextEditingController(text: '${widget.item?['amount'] ?? ''}');
    _description = TextEditingController(
      text: '${widget.item?['description'] ?? ''}',
    );
    _reason = TextEditingController();
    _category = widget.item?['category'] ?? 'OTHER';
  }

  @override
  void dispose() {
    _date.dispose();
    _amount.dispose();
    _description.dispose();
    _reason.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final data = <String, dynamic>{
      'expense_on': _date.text.trim(),
      'amount': int.parse(_amount.text.trim()),
      'category': _category,
      'description': _description.text.trim(),
      if (_attachmentId != null) 'attachment_id': _attachmentId,
      if (widget.item != null) ...{
        'expected_version': widget.item!['version'],
        'reason': _reason.text.trim(),
      },
    };
    try {
      await ref
          .read(businessProvider)
          .write(
            widget.item == null ? 'POST' : 'PATCH',
            widget.item == null
                ? '/expenses'
                : '/expenses/${widget.item!['id']}',
            data,
            key: newRequestKey(),
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
    canPop: !_busy && !_uploading,
    child: Dialog.fullscreen(
      child: Scaffold(
        resizeToAvoidBottomInset: true,
        appBar: AppBar(
          toolbarHeight: 104,
          automaticallyImplyLeading: false,
          leading: IconButton(
            tooltip: 'Kembali',
            onPressed: _busy || _uploading
                ? null
                : () => Navigator.pop(context),
            icon: const Icon(Icons.arrow_back),
          ),
          title: Text(
            widget.item == null ? 'Catat pengeluaran' : 'Koreksi pengeluaran',
            maxLines: 2,
            softWrap: true,
            overflow: TextOverflow.visible,
            textScaler: MediaQuery.textScalerOf(context)
                .clamp(maxScaleFactor: 1.3),
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
          ),
        ),
        body: SafeArea(
          child: Center(
            child: SizedBox(
              width: 640,
              child: Form(
                key: _form,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (_error != null) Text(_error!),
                      TextFormField(
                        controller: _date,
                        enabled: !_busy && !_uploading,
                        decoration: const InputDecoration(
                          labelText: 'Tanggal (YYYY-MM-DD)',
                        ),
                        validator: (value) => (value ?? '').trim().isEmpty
                            ? 'Wajib diisi.'
                            : null,
                      ),
                      const SizedBox(height: 20),
                      DropdownButtonFormField<String>(
                        isExpanded: true,
                        initialValue: _category,
                        decoration: const InputDecoration(
                          labelText: 'Kategori',
                        ),
                        items: const [
                          DropdownMenuItem(
                            value: 'ELECTRICITY',
                            child: Text('Listrik'),
                          ),
                          DropdownMenuItem(value: 'WATER', child: Text('Air')),
                          DropdownMenuItem(
                            value: 'INTERNET',
                            child: Text('Internet/Wi-Fi'),
                          ),
                          DropdownMenuItem(
                            value: 'REPAIR',
                            child: Text('Perbaikan'),
                          ),
                          DropdownMenuItem(
                            value: 'SALARY',
                            child: Text('Gaji'),
                          ),
                          DropdownMenuItem(
                            value: 'OTHER',
                            child: Text('Lainnya'),
                          ),
                        ],
                        onChanged: _busy || _uploading
                            ? null
                            : (value) =>
                                  setState(() => _category = value ?? 'OTHER'),
                      ),
                      const SizedBox(height: 20),
                      TextFormField(
                        controller: _amount,
                        enabled: !_busy && !_uploading,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Nominal (rupiah)',
                        ),
                        validator: (value) {
                          final parsed = int.tryParse((value ?? '').trim());
                          return parsed == null || parsed < 1
                              ? 'Isi rupiah bulat lebih dari 0.'
                              : null;
                        },
                      ),
                      const SizedBox(height: 20),
                      TextFormField(
                        controller: _description,
                        enabled: !_busy && !_uploading,
                        maxLines: 2,
                        decoration: const InputDecoration(
                          labelText: 'Keterangan',
                        ),
                        validator: (value) => (value ?? '').trim().isEmpty
                            ? 'Keterangan wajib diisi.'
                            : null,
                      ),
                      const SizedBox(height: 20),
                      OutlinedButton.icon(
                        onPressed: _busy || _uploading ? null : _pickAttachment,
                        icon: const Icon(Icons.attach_file),
                        label: Text(
                          _uploading
                              ? 'Mengunggah…'
                              : _attachmentName == null
                              ? 'Pilih bukti (opsional)'
                              : 'Bukti: $_attachmentName',
                        ),
                      ),
                      if (widget.item != null) ...[
                        const SizedBox(height: 20),
                        TextFormField(
                          controller: _reason,
                          enabled: !_busy && !_uploading,
                          decoration: const InputDecoration(
                            labelText: 'Alasan koreksi',
                          ),
                          validator: (value) => (value ?? '').trim().length < 3
                              ? 'Alasan minimal 3 karakter.'
                              : null,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
            child: Row(
              children: [
                TextButton(
                  onPressed: _busy || _uploading
                      ? null
                      : () => Navigator.pop(context),
                  child: const Text('Batal'),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _busy || _uploading ? null : _save,
                    child: Text(_busy ? 'Menyimpan…' : 'Simpan'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
