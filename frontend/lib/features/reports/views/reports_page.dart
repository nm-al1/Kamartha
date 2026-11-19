import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/money.dart';
import '../../../core/dates.dart';
import '../../../app/theme/kamartha_theme.dart';
import '../../expenses/views/expenses_page.dart' show categoryLabel;
import '../../invoices/views/invoices_page.dart' show methodLabel;

class ReportsPage extends ConsumerStatefulWidget {
  const ReportsPage({super.key});
  @override
  ConsumerState<ReportsPage> createState() => _ReportsPageState();
}

class _ReportsPageState extends ConsumerState<ReportsPage> {
  final _from = TextEditingController();
  final _to = TextEditingController();
  Map<String, dynamic>? _report;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now().toIso8601String().substring(0, 10);
    _from.text = '${now.substring(0, 8)}01';
    _to.text = now;
  }

  @override
  void dispose() {
    _from.dispose();
    _to.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final data = await ref.read(businessProvider).get('/reports/cash', {
        'date_from': _from.text.trim(),
        'date_to': _to.text.trim(),
      });
      if (mounted) setState(() => _report = data);
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => BusinessPage(
    title: 'Laporan kas',
    subtitle: 'Dari Menu',
    preparation: false,
    child: ListView(
      padding: pagePadding(context),
      children: [
        const Text(
          'Rentang laporan',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _from,
          enabled: !_busy,
          decoration: const InputDecoration(
            labelText: 'Tanggal awal (YYYY-MM-DD)',
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _to,
          enabled: !_busy,
          decoration: const InputDecoration(
            labelText: 'Tanggal akhir (YYYY-MM-DD)',
          ),
        ),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: _busy ? null : _load,
          child: Text(_busy ? 'Menghitung…' : 'Tampilkan'),
        ),
        if (_busy) const LinearProgressIndicator(),
        if (_report == null && !_busy && _error == null)
          const Padding(
            padding: EdgeInsets.only(top: 16),
            child: Text('Pilih rentang tanggal, lalu tampilkan laporan.'),
          ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(
            _error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        ],
        if (_report != null) ...[
          const SizedBox(height: 20),
          Text(
            rangeLabel(_report!['date_from'], _report!['date_to']),
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: KamarthaColors.secondary,
            ),
          ),
          const SizedBox(height: 16),
          _group([
            Padding(
              padding: const EdgeInsets.all(16),
              child: LayoutBuilder(
                builder: (context, box) {
                  final values = [
                    _metric('Pemasukan', _report!['income']),
                    _metric('Pengeluaran', _report!['expense']),
                  ];
                  return box.maxWidth >= 400 &&
                          MediaQuery.textScalerOf(context).scale(16) <= 20
                      ? Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(child: values[0]),
                            const SizedBox(width: 16),
                            Expanded(child: values[1]),
                          ],
                        )
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            values[0],
                            const SizedBox(height: 16),
                            values[1],
                          ],
                        );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: _metric('Selisih kas', _report!['difference']),
            ),
          ]),
          const SizedBox(height: 24),
          const Text(
            'Rincian penerimaan',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          if ((_report!['payments'] as List).isEmpty)
            const Text('Belum ada transaksi pada rentang ini.')
          else
            _group([
              for (final payment in (_report!['payments'] as List))
                _transaction(
                  'Kamar ${payment['room_number']}',
                  '${shortDate(payment['received_on'])} · ${methodLabel(payment['method'])} · ${payment['status'] == 'VALID' ? 'Valid' : 'Batal'}',
                  payment['total_amount'],
                ),
            ]),
          const SizedBox(height: 24),
          const Text(
            'Rincian pengeluaran',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          if ((_report!['expenses'] as List).isEmpty)
            const Text('Belum ada pengeluaran pada rentang ini.')
          else
            _group([
              for (final expense in (_report!['expenses'] as List))
                _transaction(
                  categoryLabel(expense['category']),
                  '${shortDate(expense['expense_on'])} · ${expense['description']} · ${expense['status'] == 'VALID' ? 'Valid' : 'Batal'}',
                  expense['amount'],
                ),
            ]),
          const Padding(
            padding: EdgeInsets.only(top: 12),
            child: Text(
              'Koreksi atau input terlambat dapat memperbarui laporan tanggal sebelumnya. '
              'Saldo sebelum pencatatan tidak termasuk kas baru.',
            ),
          ),
        ],
      ],
    ),
  );

  Widget _metric(String label, Object? amount) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: const TextStyle(fontSize: 14, color: KamarthaColors.secondary),
      ),
      const SizedBox(height: 8),
      Text(
        formatRupiah(amount),
        style: const TextStyle(
          fontSize: 26,
          height: 1.2,
          fontWeight: FontWeight.w600,
        ),
      ),
    ],
  );

  Widget _group(List<Widget> rows) => Container(
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: KamarthaColors.border),
    ),
    clipBehavior: Clip.antiAlias,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (var i = 0; i < rows.length; i++) ...[
          if (i > 0) const Divider(height: 1),
          rows[i],
        ],
      ],
    ),
  );

  Widget _transaction(String title, String subtitle, Object? amount) => Padding(
    padding: const EdgeInsets.all(12),
    child: LayoutBuilder(
      builder: (context, box) {
        final details = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                height: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              subtitle,
              style: const TextStyle(
                fontSize: 14,
                height: 1.2,
                color: KamarthaColors.secondary,
              ),
            ),
          ],
        );
        final money = Text(
          formatRupiah(amount),
          style: const TextStyle(
            fontSize: 16,
            height: 1.2,
            fontWeight: FontWeight.w600,
          ),
        );
        return box.maxWidth >= 300 &&
                MediaQuery.textScalerOf(context).scale(16) <= 20
            ? Row(
                children: [
                  Expanded(child: details),
                  const SizedBox(width: 12),
                  money,
                ],
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [details, const SizedBox(height: 8), money],
              );
      },
    ),
  );
}
