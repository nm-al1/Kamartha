import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/kamartha_theme.dart';
import '../../../core/api.dart';
import '../../../core/business_page.dart';
import '../../../core/business_repository.dart';

class MenuPage extends ConsumerStatefulWidget {
  const MenuPage({super.key});
  @override
  ConsumerState<MenuPage> createState() => _MenuPageState();
}

class _MenuPageState extends ConsumerState<MenuPage> {
  Map<String, dynamic>? _manager;
  String? _error;
  bool _busy = true;

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
      final manager = await ref.read(businessProvider).get('/auth/me');
      if (manager['mode'] != 'PREPARATION' && manager['mode'] != 'ACTIVE') {
        throw StateError('Mode aplikasi tidak dikenal.');
      }
      if (mounted) setState(() => _manager = manager);
    } catch (error) {
      if (mounted) setState(() => _error = apiError(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final preparation = _manager?['mode'] != 'ACTIVE';
    return BusinessPage(
      title: 'Menu',
      preparation: preparation,
      child: ListView(
        padding: pagePadding(context),
        children: [
          if (_busy)
            const LinearProgressIndicator(
              semanticsLabel: 'Memuat akun pengelola',
            ),
          if (_error != null) ...[
            Text(_error!),
            TextButton(onPressed: _load, child: const Text('Coba lagi')),
          ],
          if (_manager != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const CircleAvatar(
                      backgroundColor: KamarthaColors.background,
                      foregroundColor: KamarthaColors.secondary,
                      radius: 24,
                      child: Icon(Icons.person_outline, size: 28),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${_manager!['username']}',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          Text(
                            preparation
                                ? 'Akun pengelola · Mode Persiapan'
                                : 'Akun pengelola kos',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            _heading('OPERASIONAL'),
            _group([
              if (preparation)
                (
                  'Data awal',
                  'Persiapan dan rekonsiliasi sebelum transaksi',
                  Icons.checklist_outlined,
                  '/initialization',
                ),
              (
                'Penghuni',
                'Data dan riwayat penghuni',
                Icons.people_outline,
                '/residents',
              ),
              if (!preparation) ...[
                (
                  'Masa sewa',
                  'Kontrak, perpanjangan, dan keluar',
                  Icons.calendar_today_outlined,
                  '/leases',
                ),
                (
                  'Pengeluaran',
                  'Catat biaya operasional kos',
                  Icons.receipt_long_outlined,
                  '/expenses',
                ),
              ],
            ]),
            if (!preparation) ...[
              _heading('LAPORAN'),
              _group([
                (
                  'Laporan kas',
                  'Pemasukan dan pengeluaran per tanggal',
                  Icons.article_outlined,
                  '/reports',
                ),
              ]),
            ],
            _heading('PENGINGAT UJI'),
            _group([
              ('WA otomatis (uji)', 'H-3 dan hari jatuh tempo', Icons.notifications_active_outlined, '/reminders'),
            ]),
            _heading('AKUN'),
            _group([
              (
                'Ganti password',
                'Gunakan password lama untuk mengganti',
                Icons.key_outlined,
                '/change-password',
              ),
              (
                'Akun dan sesi',
                'Lihat akun atau keluar dari aplikasi',
                Icons.logout,
                '/session',
              ),
            ]),
          ],
        ],
      ),
    );
  }

  Widget _heading(String title) => Padding(
    padding: const EdgeInsets.only(top: 20, bottom: 12),
    child: Text(
      title,
      style: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: KamarthaColors.secondary,
      ),
    ),
  );

  Widget _group(List<(String, String, IconData, String)> items) => Card(
    child: Column(
      children: [
        for (var i = 0; i < items.length; i++) ...[
          if (i > 0) const Divider(),
          InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: () => GoRouter.maybeOf(context)?.push(items[i].$4),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(items[i].$3, color: KamarthaColors.secondary, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          items[i].$1,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          items[i].$2,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
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
  );
}
