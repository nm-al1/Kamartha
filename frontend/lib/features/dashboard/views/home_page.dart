import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/kamartha_theme.dart';
import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';
import '../../../core/money.dart';
import '../../../core/request_key.dart';

class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});
  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  Map<String, dynamic>? _data;
  bool _busy = true, _leaseReminders = false;
  bool? _preparation;
  String? _error;
  String _username = 'Pengelola';

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
      final manager = await repository.get('/auth/me');
      final mode = manager['mode'];
      if (mode != 'ACTIVE' && mode != 'PREPARATION') {
        throw StateError('Mode aplikasi tidak dikenal.');
      }
      final preparation = mode == 'PREPARATION';
      if (!preparation) {
        await repository.write(
          'POST',
          '/billing/synchronize',
          {},
          key: newRequestKey(),
        );
      }
      final data = await repository.get('/dashboard');
      if (data['rooms'] is! Map || data['reminders'] is! Map) {
        throw const FormatException('Ringkasan dashboard tidak lengkap.');
      }
      if (mounted) {
        setState(() {
          _data = data;
          _preparation = preparation;
          _username = '${manager['username'] ?? 'Pengelola'}';
        });
      }
    } catch (error) {
      if (mounted) {
        setState(
          () => _error =
              '${apiError(error)} Data tagihan mungkin belum diperbarui.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _open(String path) => GoRouter.maybeOf(context)?.push(path);

  @override
  Widget build(BuildContext context) {
    final invoices = _data?['reminders']['invoices'] as List? ?? [];
    final leases = _data?['reminders']['leases'] as List? ?? [];
    final horizontal = pagePadding(context).left;
    return BusinessPage(
      title: 'Beranda',
      showAppBar: false,
      preparation: _preparation != false,
      child: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          children: [
            if (_busy)
              const LinearProgressIndicator(
                semanticsLabel: 'Memuat ringkasan kos',
              ),
            if (_data != null) _hero(horizontal),
            Padding(
              padding: EdgeInsets.fromLTRB(horizontal, 0, horizontal, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_error != null) ...[
                    Text(_error!),
                    TextButton(
                      onPressed: _load,
                      child: const Text('Coba lagi'),
                    ),
                  ],
                  if (_preparation == true) ...[
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'Mode Persiapan',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Lengkapi dan tinjau data awal sebelum mencatat pembayaran atau pengeluaran. Transaksi belum dibuka.',
                            ),
                            const SizedBox(height: 12),
                            FilledButton(
                              onPressed: () => _open('/initialization'),
                              child: const Text('Lengkapi data awal'),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (_data != null) ...[
                    const Text(
                      'Perlu ditindaklanjuti',
                      style: TextStyle(
                        fontSize: 20,
                        height: 1.2,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: IntrinsicHeight(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              child: _tab(
                                'Tagihan',
                                invoices.length,
                                !_leaseReminders,
                                () => setState(() => _leaseReminders = false),
                                const ValueKey('home-invoice-count'),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _tab(
                                'Akhir sewa',
                                leases.length,
                                _leaseReminders,
                                () => setState(() => _leaseReminders = true),
                                const ValueKey('home-lease-count'),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    if ((_leaseReminders ? leases : invoices).isEmpty)
                      const Card(
                        child: Padding(
                          padding: EdgeInsets.all(20),
                          child: Text(
                            'Belum ada tagihan atau akhir sewa yang mendesak.',
                          ),
                        ),
                      )
                    else
                      Container(
                        key: const ValueKey('home-reminder-group'),
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
                              i < (_leaseReminders ? leases : invoices).length;
                              i++
                            ) ...[
                              if (i > 0) const Divider(),
                              if (_leaseReminders)
                                _leaseRow(leases[i])
                              else
                                _invoiceRow(invoices[i]),
                            ],
                          ],
                        ),
                      ),
                    if (_preparation == false) ...[
                      const SizedBox(height: 8),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton(
                          style: TextButton.styleFrom(
                            padding: EdgeInsets.zero,
                            alignment: Alignment.centerLeft,
                            textStyle: const TextStyle(
                              fontFamily: 'Inter',
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          onPressed: () =>
                              _open(_leaseReminders ? '/leases' : '/invoices'),
                          child: Text(
                            _leaseReminders
                                ? 'Lihat semua masa sewa →'
                                : 'Lihat semua tagihan →',
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Pencatatan cepat',
                        style: TextStyle(
                          fontSize: 20,
                          height: 1.2,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: [
                          OutlinedButton.icon(
                            onPressed: () => _open('/invoices'),
                            style: OutlinedButton.styleFrom(
                              backgroundColor: Colors.white,
                            ),
                            icon: const Icon(
                              Icons.add,
                              color: KamarthaColors.primary,
                            ),
                            label: const Text('Catat pembayaran'),
                          ),
                          OutlinedButton.icon(
                            onPressed: () => _open('/expenses'),
                            style: OutlinedButton.styleFrom(
                              backgroundColor: Colors.white,
                            ),
                            icon: const Icon(
                              Icons.add,
                              color: KamarthaColors.primary,
                            ),
                            label: const Text('Pengeluaran'),
                          ),
                        ],
                      ),
                    ],
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Piutang: ${formatRupiah(_data!['receivables'])}',
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Menunggak: ${formatRupiah(_data!['overdue_receivables'])}',
                            ),
                            Text(
                              'Kontrak aktif: ${_data!['active_contracts']}',
                            ),
                            if (_preparation == false)
                              TextButton(
                                onPressed: () => _open('/reports'),
                                child: const Text('Laporan kas'),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _hero(double horizontal) {
    final rooms = _data!['rooms'];
    return Column(
      children: [
        ClipRect(
          child: Stack(
            children: [
              const Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: KamarthaColors.headerGradient,
                  ),
                ),
              ),
              Positioned(
                right: -94,
                top: -78,
                child: Container(
                  width: 230,
                  height: 230,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withValues(alpha: .06),
                  ),
                ),
              ),
              Padding(
                padding: EdgeInsets.fromLTRB(horizontal, 32, horizontal, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'kamartha',
                      style: TextStyle(
                        fontSize: 30,
                        height: 1.2,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Halo, $_username',
                                style: const TextStyle(
                                  fontSize: 20,
                                  height: 1.2,
                                  fontWeight: FontWeight.w600,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _longDate('${_data!['today']}'),
                                style: const TextStyle(
                                  fontSize: 14,
                                  height: 1.2,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        SizedBox(
                          width: 52,
                          height: 52,
                          child: IconButton(
                            tooltip: 'Sesi pengelola',
                            onPressed: () => _open('/session'),
                            style: IconButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: const BorderSide(color: Colors.white),
                              shape: const CircleBorder(),
                            ),
                            icon: const Icon(Icons.person_outline, size: 28),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Stack(
          children: [
            const Positioned(
              left: 0,
              right: 0,
              top: 0,
              height: 40,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: KamarthaColors.headerGradient,
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(horizontal, 0, horizontal, 16),
              child: Container(
                key: const ValueKey('home-occupancy-panel'),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x24142039),
                      blurRadius: 24,
                      offset: Offset(0, 8),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Semantics(
                      container: true,
                      child: TextField(
                        style: const TextStyle(fontSize: 16, height: 1.2),
                        decoration: const InputDecoration(
                          hintText: 'Cari nomor kamar',
                          hintStyle: TextStyle(color: KamarthaColors.secondary),
                          prefixIcon: Icon(Icons.search, size: 24),
                          prefixIconConstraints: BoxConstraints(
                            minWidth: 48,
                            minHeight: 24,
                          ),
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 16,
                          ),
                          isDense: true,
                          fillColor: KamarthaColors.background,
                          border: OutlineInputBorder(
                            borderSide: BorderSide.none,
                            borderRadius: BorderRadius.all(Radius.circular(26)),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderSide: BorderSide.none,
                            borderRadius: BorderRadius.all(Radius.circular(26)),
                          ),
                        ),
                        textInputAction: TextInputAction.search,
                        onSubmitted: (query) => _open(
                          '/rooms?q=${Uri.encodeQueryComponent(query.trim())}',
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Semantics(
                      container: true,
                      child: LayoutBuilder(
                        builder: (context, box) {
                          final occupancy = _stat(
                            '${rooms['occupied']} dari ${rooms['total']}',
                            'kamar dihuni',
                          );
                          final people = _stat(
                            '${_data!['people_staying']}',
                            'orang tinggal',
                          );
                          if (box.maxWidth <
                              MediaQuery.textScalerOf(context).scale(220)) {
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                occupancy,
                                const SizedBox(height: 12),
                                people,
                              ],
                            );
                          }
                          return Row(
                            children: [
                              Expanded(child: occupancy),
                              const SizedBox(width: 16),
                              Container(
                                width: 1,
                                height: 48,
                                color: KamarthaColors.divider,
                              ),
                              const SizedBox(width: 16),
                              Expanded(child: people),
                            ],
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 12),
                    Semantics(
                      container: true,
                      child: Text(
                        '${rooms['empty']} kosong · ${rooms['needs_confirmation']} perlu konfirmasi',
                        style: const TextStyle(
                          fontSize: 14,
                          height: 1.2,
                          fontWeight: FontWeight.w600,
                          color: KamarthaColors.warning,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _stat(String value, String label) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        value,
        style: const TextStyle(
          fontSize: 24,
          height: 1.2,
          fontWeight: FontWeight.w600,
          color: KamarthaColors.ink,
        ),
      ),
      const SizedBox(height: 4),
      Text(
        label,
        style: const TextStyle(
          fontSize: 14,
          height: 1.2,
          color: KamarthaColors.secondary,
        ),
      ),
    ],
  );

  Widget _tab(
    String label,
    int count,
    bool selected,
    VoidCallback onPressed,
    Key badgeKey,
  ) => TextButton(
    style: TextButton.styleFrom(
      minimumSize: const Size(0, 48),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      backgroundColor: selected
          ? KamarthaColors.activeTab
          : KamarthaColors.chip,
      foregroundColor: selected ? Colors.white : KamarthaColors.secondary,
      padding: const EdgeInsets.all(12),
    ),
    onPressed: onPressed,
    child: Row(
      children: [
        Expanded(
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 16,
              height: 1.2,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        const SizedBox(width: 8),
        Container(
          key: badgeKey,
          constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
          alignment: Alignment.center,
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
          decoration: BoxDecoration(
            color: selected ? KamarthaColors.primary : const Color(0xFFD8E2ED),
            borderRadius: BorderRadius.circular(99),
          ),
          child: Text(
            '$count',
            style: TextStyle(
              fontSize: 12,
              height: 1.2,
              fontWeight: FontWeight.w600,
              color: selected ? Colors.white : KamarthaColors.secondary,
            ),
          ),
        ),
      ],
    ),
  );

  Widget _invoiceRow(dynamic invoice) {
    final today = DateTime.tryParse('${_data!['today']}');
    final due = DateTime.tryParse('${invoice['due_on']}');
    final days = today != null && due != null
        ? due.difference(today).inDays
        : null;
    final overdue = days != null && days < 0;
    final status = days == null
        ? 'Jatuh tempo ${invoice['due_on']}'
        : overdue
        ? 'Terlambat ${-days} hari'
        : days == 0
        ? 'Jatuh tempo hari ini'
        : days == 1
        ? 'Jatuh tempo besok'
        : 'Jatuh tempo $days hari';
    return InkWell(
      onTap: () => _open('/invoices/${invoice['id']}'),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: LayoutBuilder(
          builder: (context, box) {
            final scale = MediaQuery.textScalerOf(context);
            final money = formatRupiah(invoice['remaining']);
            final measure = TextPainter(
              text: TextSpan(
                text: money,
                style: const TextStyle(
                  fontFamily: 'Inter',
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  height: 1.2,
                ),
              ),
              textDirection: Directionality.of(context),
              textScaler: scale,
            )..layout();
            final inline =
                scale.scale(16) <= 20 &&
                box.maxWidth - measure.width - 101 >= 80;
            measure.dispose();
            final details = Column(
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
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(top: 5),
                      child: Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: overdue
                              ? KamarthaColors.danger
                              : KamarthaColors.warning,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        status,
                        style: TextStyle(
                          fontSize: 14,
                          height: 1.2,
                          fontWeight: FontWeight.w600,
                          color: overdue
                              ? KamarthaColors.danger
                              : KamarthaColors.warning,
                        ),
                      ),
                    ),
                  ],
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
              children: [
                Container(
                  width: 51,
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
                Expanded(child: details),
                if (inline) ...[
                  const SizedBox(width: 12),
                  Text(
                    money,
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
                  size: 14,
                  color: KamarthaColors.secondary,
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _leaseRow(dynamic lease) => ListTile(
    title: Text('Kamar ${lease['room_number']} · akhir sewa'),
    subtitle: Text(
      '${lease['effective_ends_on']} · ${lease['staying'] == true ? 'Masih dihuni, perlu konfirmasi' : 'Tidak ada penghuni tinggal'}',
    ),
    trailing: const Icon(Icons.chevron_right),
    onTap: () => _open('/leases/${lease['id']}'),
  );

  String _longDate(String value) {
    final date = DateTime.tryParse(value);
    if (date == null) return value;
    const days = [
      'Senin',
      'Selasa',
      'Rabu',
      'Kamis',
      'Jumat',
      'Sabtu',
      'Minggu',
    ];
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
    return '${days[date.weekday - 1]}, ${date.day} ${months[date.month - 1]} ${date.year}';
  }
}
