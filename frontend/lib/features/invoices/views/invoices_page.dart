import 'package:file_picker/file_picker.dart';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/dates.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';
import '../../../app/theme/kamartha_theme.dart';

String statusLabel(Object? value) => switch ('$value') {
  'PAID' => 'Lunas',
  'PARTIALLY_PAID' => 'Dibayar sebagian',
  'OVERDUE' => 'Menunggak',
  'UNPAID' => 'Belum dibayar',
  'CANCELLED' => 'Batal',
  _ => '—',
};

String dateLabel(Object? value) => value == null ? '—' : '$value';

String methodLabel(Object? value) => switch ('$value') {
  'CASH' => 'Cash',
  'TRANSFER' => 'Transfer',
  'QRIS' => 'QRIS',
  _ => '$value',
};

class InvoicesPage extends ConsumerStatefulWidget {
  const InvoicesPage({super.key});
  @override
  ConsumerState<InvoicesPage> createState() => _InvoicesPageState();
}

class _InvoicesPageState extends ConsumerState<InvoicesPage> {
  final _search = TextEditingController();
  List<Map<String, dynamic>> _items = [];
  bool _busy = true, _more = false;
  String _status = '';
  String? _error;
  int _totalRemaining = 0;
  bool _showFilters = false;

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
      await repository.write(
        'POST',
        '/billing/synchronize',
        {},
        key: newRequestKey(),
      );
      final data = await repository.get('/invoices', {
        'q': _search.text,
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
        _totalRemaining = data['summary']['total_remaining'] as int;
      });
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final horizontal = pagePadding(context).left;
    return BusinessPage(
      title: 'Tagihan',
      preparation: false,
      actions: [
        IconButton(
          tooltip: 'Filter tagihan',
          onPressed: () => setState(() => _showFilters = !_showFilters),
          icon: const Icon(
            Icons.filter_alt_outlined,
            color: KamarthaColors.primary,
          ),
        ),
      ],
      child: ListView(
        padding: EdgeInsets.fromLTRB(horizontal, 8, horizontal, 24),
        children: [
          TextField(
            controller: _search,
            style: const TextStyle(fontSize: 16),
            decoration: const InputDecoration(
              hintText: 'Cari kamar atau penghuni',
              prefixIcon: Icon(Icons.search, size: 24),
              prefixIconConstraints: BoxConstraints(minWidth: 48),
              border: InputBorder.none,
              enabledBorder: InputBorder.none,
              focusedBorder: InputBorder.none,
              filled: false,
              contentPadding: EdgeInsets.symmetric(vertical: 14),
            ),
            onSubmitted: (_) => _load(),
          ),
          const SizedBox(height: 8),
          if (_showFilters) ...[
            DropdownButtonFormField<String>(
              initialValue: _status,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Status'),
              items: const [
                DropdownMenuItem(value: '', child: Text('Semua')),
                DropdownMenuItem(value: 'UNPAID', child: Text('Belum dibayar')),
                DropdownMenuItem(
                  value: 'PARTIALLY_PAID',
                  child: Text('Dibayar sebagian'),
                ),
                DropdownMenuItem(value: 'OVERDUE', child: Text('Menunggak')),
                DropdownMenuItem(value: 'PAID', child: Text('Lunas')),
                DropdownMenuItem(value: 'CANCELLED', child: Text('Batal')),
              ],
              onChanged: _busy
                  ? null
                  : (value) {
                      setState(() => _status = value ?? '');
                      _load();
                    },
            ),
            const SizedBox(height: 12),
          ],
          Text(
            'Sisa tagihan aktif',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 8),
          if (!_busy && _error == null)
            Text(
              formatRupiah(_totalRemaining),
              style: Theme.of(context).textTheme.displaySmall,
            ),
          const SizedBox(height: 8),
          Text(
            'Termasuk yang belum jatuh tempo.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          LayoutBuilder(builder: (context, box) => Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final entry in [
                ('Menunggak', 'OVERDUE'),
                ('Lunas', 'PAID'),
                ('Semua', ''),
              ])
                SizedBox(width: MediaQuery.textScalerOf(context).scale(16) > 20
                    ? box.maxWidth : (box.maxWidth - 16) / 3,
                  child: _pill(entry.$1, entry.$2)),
            ],
          )),
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
              child: Text('Belum ada tagihan pada filter ini.'),
            ),
          for (final group in const [
            ('OVERDUE', 'Menunggak'),
            ('UNPAID', 'Belum lunas'),
            ('PARTIALLY_PAID', 'Dibayar sebagian'),
            ('PAID', 'Lunas'),
            ('CANCELLED', 'Batal'),
          ])
            if (_items.any((item) => item['payment_status'] == group.$1))
              _group(
                group.$2,
                _items
                    .where((item) => item['payment_status'] == group.$1)
                    .toList(),
                group.$1 == 'OVERDUE',
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

  Widget _group(String title, List<Map<String, dynamic>> items, bool urgent) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 20,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Text(
                  '${items.length} tagihan',
                  style: TextStyle(
                    fontSize: 14,
                    height: 1.2,
                    fontWeight: FontWeight.w600,
                    color: urgent
                        ? KamarthaColors.danger
                        : KamarthaColors.secondary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: KamarthaColors.border),
              ),
              clipBehavior: Clip.antiAlias,
              child: Column(
                children: [
                  for (var i = 0; i < items.length; i++) ...[
                    if (i > 0) const Divider(),
                    _row(items[i]),
                  ],
                ],
              ),
            ),
          ],
        ),
      );

  Widget _row(Map<String, dynamic> item) => InkWell(
    onTap: () => context.push('/invoices/${item['id']}'),
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: LayoutBuilder(
        builder: (context, box) {
          final money = formatRupiah(item['remaining']);
          final inline =
              MediaQuery.textScalerOf(context).scale(16) <= 20 &&
              box.maxWidth >= 280;
          final details = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${item['resident_names'] ?? 'Tanpa penghuni tinggal'}',
                style: const TextStyle(
                  fontSize: 16,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                rangeLabel(item['period_start'], item['period_end']),
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.2,
                  color: KamarthaColors.secondary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Tempo ${shortDate(item['due_on'])}',
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                  color: KamarthaColors.warning,
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
          );
          return Row(
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
                    '${item['room_number']}',
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
              Expanded(child: details),
              if (inline) ...[
                const SizedBox(width: 8),
                Text(
                  money,
                  textAlign: TextAlign.end,
                  style: const TextStyle(
                    fontSize: 16,
                    height: 1.2,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
              const SizedBox(width: 8),
              const Icon(
                Icons.chevron_right,
                size: 18,
                color: KamarthaColors.secondary,
              ),
            ],
          );
        },
      ),
    ),
  );
}

class InvoiceDetailPage extends ConsumerStatefulWidget {
  const InvoiceDetailPage({super.key, required this.id});
  final String id;
  @override
  ConsumerState<InvoiceDetailPage> createState() => _InvoiceDetailPageState();
}

class _InvoiceDetailPageState extends ConsumerState<InvoiceDetailPage> {
  Map<String, dynamic>? _invoice;
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
          .get('/invoices/${widget.id}');
      if (mounted) setState(() => _invoice = data);
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pay() async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => PaymentFormPage(invoice: _invoice!)),
    );
    if (saved == true && mounted) await _load();
  }

  Future<void> _cancelPayment(Map<String, dynamic> allocation) async {
    final reason = TextEditingController();
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Batalkan pembayaran?'),
        content: TextField(
          controller: reason,
          decoration: const InputDecoration(labelText: 'Alasan pembatalan'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Batalkan pembayaran'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      try {
        await ref.read(businessProvider).write(
          'POST',
          '/payments/${allocation['payment_id']}/cancel',
          {'reason': reason.text.trim()},
          key: newRequestKey(),
        );
        await _load();
      } catch (error) {
        if (mounted) setState(() => _error = apiError(error));
      }
    }
    reason.dispose();
  }

  Future<void> _whatsapp() async {
    try {
      final preview = await ref.read(businessProvider).write(
        'POST',
        '/messages/preview',
        {'context_type': 'INVOICE', 'context_id': widget.id},
        key: newRequestKey(),
      );
      if (!mounted) return;
      final opened = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Pesan untuk ${preview['recipient']}'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Nomor: ${preview['whatsapp_number']}'),
                const SizedBox(height: 8),
                Text('${preview['message']}'),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Tutup'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Buka WhatsApp'),
            ),
          ],
        ),
      );
      if (opened == true) {
        await launchUrl(
          Uri.parse('${preview['whatsapp_url']}'),
          webOnlyWindowName: '_blank',
        );
      }
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    }
  }

  @override
  Widget build(BuildContext context) {
    final invoice = _invoice;
    final payable =
        invoice != null &&
        invoice['status'] == 'ACTIVE' &&
        (invoice['remaining'] as int) > 0;
    final statusColor = invoice?['payment_status'] == 'PAID'
        ? KamarthaColors.success
        : invoice?['payment_status'] == 'OVERDUE'
        ? KamarthaColors.danger
        : KamarthaColors.secondary;
    return BusinessPage(
      title: 'Tagihan',
      subtitle: invoice == null
          ? null
          : 'Kamar ${invoice['room_number']} · ${rangeLabel(invoice['period_start'], invoice['period_end'])}',
      preparation: false,
      child: ListView(
        padding: pagePadding(context),
        children: [
          if (_busy) const LinearProgressIndicator(),
          if (_error != null) ...[
            Text(_error!),
            TextButton(onPressed: _load, child: const Text('Muat ulang')),
          ],
          if (invoice != null) ...[
            const Text(
              'Sisa tagihan',
              style: TextStyle(fontSize: 14, color: KamarthaColors.secondary),
            ),
            const SizedBox(height: 8),
            Text(
              formatRupiah(invoice['remaining']),
              style: const TextStyle(
                fontSize: 30,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Dari ${formatRupiah(invoice['amount'])} · dibayar ${formatRupiah(invoice['paid_total'])}',
              style: const TextStyle(
                fontSize: 14,
                height: 1.2,
                color: KamarthaColors.secondary,
              ),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerLeft,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  statusLabel(invoice['payment_status']),
                  style: TextStyle(
                    fontSize: 14,
                    height: 1.2,
                    fontWeight: FontWeight.w600,
                    color: statusColor,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: KamarthaColors.border),
              ),
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Container(
                    width: 52,
                    constraints: const BoxConstraints(minHeight: 52),
                    padding: const EdgeInsets.all(4),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: KamarthaColors.chip,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        '${invoice['room_number']}',
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
                          '${invoice['resident_names'] ?? 'Tanpa penghuni tinggal'}',
                          style: const TextStyle(
                            fontSize: 16,
                            height: 1.2,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Jatuh tempo ${shortDate(invoice['due_on'])}',
                          style: const TextStyle(
                            fontSize: 14,
                            height: 1.2,
                            color: KamarthaColors.secondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Rincian tagihan',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            _infoTable([
              ('Nominal tagihan', formatRupiah(invoice['amount'])),
              ('Sudah dibayar', formatRupiah(invoice['paid_total'])),
              ('Sisa tagihan', formatRupiah(invoice['remaining'])),
            ]),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _busy || !payable ? null : _pay,
                child: const Text('Catat pembayaran'),
              ),
            ),
            TextButton(
              onPressed: _busy ? null : _whatsapp,
              child: const Text('Siapkan pesan WhatsApp'),
            ),
            const SizedBox(height: 24),
            const Text(
              'Pembayaran',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            if ((invoice['allocations'] as List).isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: KamarthaColors.border),
                ),
                child: const Text(
                  'Belum ada pembayaran baru untuk tagihan ini.',
                  style: TextStyle(color: KamarthaColors.secondary),
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
                    for (
                      var i = 0;
                      i < (invoice['allocations'] as List).length;
                      i++
                    ) ...[
                      if (i > 0) const Divider(),
                      _allocationRow(
                        (invoice['allocations'] as List)[i]
                            as Map<String, dynamic>,
                      ),
                    ],
                  ],
                ),
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

  Widget _allocationRow(Map<String, dynamic> allocation) => Padding(
    padding: const EdgeInsets.all(12),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                formatRupiah(allocation['amount']),
                style: const TextStyle(
                  fontSize: 16,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${methodLabel(allocation['method'])} · ${shortDate(allocation['received_on'])} · ${allocation['status'] == 'VALID' ? 'Valid' : 'Batal'}',
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.2,
                  color: KamarthaColors.secondary,
                ),
              ),
            ],
          ),
        ),
        if (allocation['status'] == 'VALID')
          TextButton(
            onPressed: _busy
                ? null
                : () => _cancelPayment(Map<String, dynamic>.from(allocation)),
            child: const Text('Batalkan'),
          ),
      ],
    ),
  );
}

class PaymentFormPage extends ConsumerStatefulWidget {
  const PaymentFormPage({super.key, required this.invoice});
  final Map<String, dynamic> invoice;
  @override
  ConsumerState<PaymentFormPage> createState() => _PaymentFormPageState();
}

class _PaymentFormPageState extends ConsumerState<PaymentFormPage> {
  final _date = TextEditingController(
    text: DateTime.now().toIso8601String().substring(0, 10),
  );
  final _amount = TextEditingController();
  final _reference = TextEditingController();
  String _method = 'CASH';
  bool _busy = false,
      _uploading = false,
      _reviewing = false,
      _confirmed = false;
  String? _error, _key, _attachmentId, _attachmentName;
  String? _lastPayload;

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
  void dispose() {
    _date.dispose();
    _amount.dispose();
    _reference.dispose();
    super.dispose();
  }

  void _review() {
    if (_busy || _uploading) return;
    final amount = int.tryParse(_amount.text.trim());
    final remaining = widget.invoice['remaining'] as int;
    if (amount == null || amount < 1 || amount > remaining) {
      setState(
        () =>
            _error = 'Nominal harus 1 sampai sisa ${formatRupiah(remaining)}.',
      );
      return;
    }
    if (DateTime.tryParse(_date.text.trim()) == null) {
      setState(() => _error = 'Tanggal diterima harus berformat YYYY-MM-DD.');
      return;
    }
    setState(() {
      _error = null;
      _confirmed = false;
      _reviewing = true;
    });
    FocusManager.instance.primaryFocus?.unfocus();
  }

  Future<void> _save() async {
    final amount = int.tryParse(_amount.text.trim());
    final remaining = widget.invoice['remaining'] as int;
    if (amount == null || amount < 1 || amount > remaining) {
      setState(
        () =>
            _error = 'Nominal harus 1 sampai sisa ${formatRupiah(remaining)}.',
      );
      return;
    }
    final payload = <String, dynamic>{
      'lease_id': widget.invoice['lease_id'],
      'received_on': _date.text.trim(),
      'total_amount': amount,
      'method': _method,
      if (_reference.text.trim().isNotEmpty)
        'reference': _reference.text.trim(),
      'allocations': [
        {'invoice_id': widget.invoice['id'], 'amount': amount},
      ],
      if (_attachmentId != null) 'attachment_id': _attachmentId,
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
          .write('POST', '/payments', payload, key: _key);
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

  String get _methodLabel => switch (_method) {
    'TRANSFER' => 'Transfer',
    'QRIS' => 'QRIS',
    _ => 'Cash',
  };

  @override
  Widget build(BuildContext context) {
    final remaining = widget.invoice['remaining'] as int;
    final amount = int.tryParse(_amount.text.trim()) ?? 0;
    return PopScope(
      canPop: !_busy && !_uploading && !_reviewing,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop && _reviewing && !_busy) {
          setState(() => _reviewing = false);
        }
      },
      child: Scaffold(
        appBar: AppBar(
          automaticallyImplyLeading: false,
          toolbarHeight: 104,
          leading: IconButton(
            tooltip: 'Kembali',
            icon: const Icon(Icons.arrow_back, size: 28),
            onPressed: _busy || _uploading
                ? null
                : () {
                    if (_reviewing) {
                      setState(() => _reviewing = false);
                    } else {
                      Navigator.pop(context);
                    }
                  },
          ),
          title: MediaQuery.withClampedTextScaling(
            maxScaleFactor: 1.3,
            child: _reviewing
                ? Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerLeft,
                        child: Text('Tinjau pembayaran'),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Pastikan data sesuai uang diterima',
                        style: TextStyle(
                          fontSize: 14,
                          height: 1.2,
                          fontWeight: FontWeight.w400,
                          color: KamarthaColors.secondary,
                        ),
                      ),
                    ],
                  )
                : const FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text('Catat pembayaran'),
                  ),
          ),
        ),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 640),
              child: _reviewing ? _reviewBody(remaining, amount) : _formBody(),
            ),
          ),
        ),
        bottomNavigationBar: DecoratedBox(
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(top: BorderSide(color: KamarthaColors.border)),
          ),
          child: SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
              child: ConstrainedBox(
                constraints: const BoxConstraints(minHeight: 48),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed:
                        _busy || _uploading || (_reviewing && !_confirmed)
                        ? null
                        : _reviewing
                        ? _save
                        : _review,
                    child: Text(
                      _busy
                          ? 'Menyimpan…'
                          : _reviewing
                          ? 'Simpan pembayaran'
                          : 'Tinjau pembayaran',
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _formBody() => ListView(
    key: const ValueKey('payment-form'),
    padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
    children: [
      const Text(
        'Kamar dan penghuni',
        style: TextStyle(
          fontSize: 20,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
      const SizedBox(height: 12),
      _reviewTable([
        ('Kamar', '${widget.invoice['room_number']}'),
        (
          'Penghuni',
          '${widget.invoice['resident_names'] ?? 'Tanpa penghuni tinggal'}',
        ),
        (
          'Periode',
          rangeLabel(
            widget.invoice['period_start'],
            widget.invoice['period_end'],
          ),
        ),
        ('Sisa tagihan', formatRupiah(widget.invoice['remaining'])),
      ]),
      const SizedBox(height: 24),
      const Text(
        'Rincian penerimaan',
        style: TextStyle(
          fontSize: 20,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
      const SizedBox(height: 20),
      if (_error != null) ...[
        Text(
          _error!,
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
        const SizedBox(height: 12),
      ],
      TextField(
        controller: _date,
        enabled: !_busy && !_uploading,
        decoration: const InputDecoration(
          label: Text('Tanggal uang diterima (YYYY-MM-DD)', maxLines: 3),
        ),
      ),
      const SizedBox(height: 16),
      TextField(
        controller: _amount,
        key: const ValueKey('payment-amount'),
        enabled: !_busy && !_uploading,
        keyboardType: TextInputType.number,
        decoration: InputDecoration(
          label: const Text('Nominal diterima (rupiah)', maxLines: 2),
          helperText:
              'Sisa tagihan ${formatRupiah(widget.invoice['remaining'])}',
          helperMaxLines: 3,
        ),
      ),
      const SizedBox(height: 16),
      DropdownButtonFormField<String>(
        isExpanded: true,
        initialValue: _method,
        decoration: const InputDecoration(labelText: 'Metode'),
        items: const [
          DropdownMenuItem(value: 'CASH', child: Text('Cash')),
          DropdownMenuItem(value: 'TRANSFER', child: Text('Transfer')),
          DropdownMenuItem(value: 'QRIS', child: Text('QRIS')),
        ],
        onChanged: _busy || _uploading
            ? null
            : (value) => setState(() => _method = value ?? 'CASH'),
      ),
      const SizedBox(height: 16),
      TextField(
        controller: _reference,
        enabled: !_busy && !_uploading,
        decoration: const InputDecoration(labelText: 'Referensi (opsional)'),
      ),
      const SizedBox(height: 12),
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
      const SizedBox(height: 16),
      const Text(
        'Data belum disimpan',
        textAlign: TextAlign.center,
        style: TextStyle(fontSize: 14, color: KamarthaColors.secondary),
      ),
    ],
  );

  Widget _reviewBody(int remaining, int amount) => ListView(
    key: const ValueKey('payment-review'),
    padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
    children: [
      if (_error != null) ...[
        Text(
          _error!,
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
        const SizedBox(height: 12),
      ],
      const Text(
        'Kamar dan penghuni',
        style: TextStyle(
          fontSize: 20,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
      const SizedBox(height: 12),
      Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: KamarthaColors.border),
        ),
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Container(
              width: 52,
              constraints: const BoxConstraints(minHeight: 52),
              padding: const EdgeInsets.all(4),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: KamarthaColors.chip,
                borderRadius: BorderRadius.circular(10),
              ),
              child: FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  '${widget.invoice['room_number']}',
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
                    '${widget.invoice['resident_names'] ?? 'Tanpa penghuni tinggal'}',
                    style: const TextStyle(
                      fontSize: 16,
                      height: 1.2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${rangeLabel(widget.invoice['period_start'], widget.invoice['period_end'])} · ${statusLabel(widget.invoice['payment_status'])}',
                    style: const TextStyle(
                      fontSize: 14,
                      height: 1.2,
                      color: KamarthaColors.secondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 24),
      Row(
        children: [
          const Expanded(
            child: Text(
              'Rincian penerimaan',
              style: TextStyle(
                fontSize: 20,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          TextButton(
            onPressed: _busy ? null : () => setState(() => _reviewing = false),
            child: const Text('Ubah'),
          ),
        ],
      ),
      const SizedBox(height: 12),
      _reviewTable([
        ('Tanggal diterima', shortDate(_date.text.trim())),
        ('Metode', _methodLabel),
        if (_reference.text.trim().isNotEmpty)
          ('Referensi', _reference.text.trim()),
        ('Bukti pembayaran', _attachmentName ?? 'Belum dilampirkan'),
      ]),
      const SizedBox(height: 24),
      const Text(
        'Alokasi tagihan',
        style: TextStyle(
          fontSize: 20,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
      const SizedBox(height: 12),
      Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: KamarthaColors.border),
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          children: [
            Container(
              width: double.infinity,
              color: KamarthaColors.chip,
              padding: const EdgeInsets.all(12),
              child: Text(
                rangeLabel(
                  widget.invoice['period_start'],
                  widget.invoice['period_end'],
                ),
                style: const TextStyle(
                  fontSize: 16,
                  height: 1.2,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const Divider(height: 1),
            for (final row in [
              ('Sisa sebelum bayar', formatRupiah(remaining)),
              ('Dialokasikan', formatRupiah(amount)),
              ('Sisa setelah bayar', formatRupiah(remaining - amount)),
            ]) ...[
              Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        row.$1,
                        style: const TextStyle(
                          fontSize: 14,
                          color: KamarthaColors.secondary,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Flexible(
                      child: Text(
                        row.$2,
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
              if (row.$1 != 'Sisa setelah bayar') const Divider(height: 1),
            ],
          ],
        ),
      ),
      const SizedBox(height: 24),
      const Text(
        'Total uang diterima',
        style: TextStyle(
          fontSize: 16,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
      const SizedBox(height: 8),
      Align(
        alignment: Alignment.centerRight,
        child: Text(
          formatRupiah(amount),
          style: const TextStyle(
            fontSize: 30,
            height: 1.2,
            fontWeight: FontWeight.w600,
            color: KamarthaColors.primary,
          ),
        ),
      ),
      const SizedBox(height: 12),
      Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Checkbox(
            value: _confirmed,
            onChanged: _busy
                ? null
                : (value) => setState(() => _confirmed = value ?? false),
          ),
          const Expanded(
            child: Padding(
              padding: EdgeInsets.only(top: 10),
              child: Text(
                'Saya sudah memastikan uang diterima',
                style: TextStyle(fontSize: 16, height: 1.2),
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      const Center(
        child: Text(
          'Data belum disimpan',
          style: TextStyle(fontSize: 14, color: KamarthaColors.secondary),
        ),
      ),
    ],
  );

  Widget _reviewTable(List<(String, String)> rows) => Container(
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: KamarthaColors.border),
    ),
    child: Column(
      children: [
        for (var i = 0; i < rows.length; i++) ...[
          if (i > 0) const Divider(height: 1),
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
}
