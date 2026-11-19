import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../app/theme/kamartha_theme.dart';
import 'widgets/kamartha_floating_nav_bar.dart';

class BusinessPage extends StatelessWidget {
  const BusinessPage({
    super.key,
    required this.title,
    required this.child,
    this.preparation = true,
    this.showAppBar = true,
    this.subtitle,
    this.actions,
  });
  final String title;
  final String? subtitle;
  final Widget child;
  final bool preparation;
  final bool showAppBar;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    final router = GoRouter.maybeOf(context);
    final path = router != null
        ? GoRouterState.of(context).uri.path
        : switch (title) {
            'Beranda' => '/home',
            'Kamar' => '/rooms',
            'Tagihan' => '/invoices',
            'Pengeluaran' => '/expenses',
            'Menu' => '/menu',
            _ => '',
          };
    final mainScreen = [
      '/home',
      '/rooms',
      '/invoices',
      '/expenses',
      '/menu',
    ].contains(path);
    final compact = MediaQuery.sizeOf(context).width < 600;
    final selected = switch (path) {
      '/home' => 0,
      '/rooms' => 1,
      '/invoices' => 2,
      _ => 3,
    };
    void navigate(String target) => router?.go(target);
    final hasBack = !mainScreen || path == '/expenses';
    final largeText = MediaQuery.textScalerOf(context).scale(16) > 20;
    final headerScaler = MediaQuery.textScalerOf(context)
        .clamp(maxScaleFactor: 1.3);
    final titleStyle =
        Theme.of(context).appBarTheme.titleTextStyle ??
        Theme.of(context).textTheme.titleLarge!;
    final titleWidth =
        (MediaQuery.sizeOf(context).width -
                32 -
                (hasBack ? 56 : 0) -
                (actions != null
                    ? actions!.length * 48
                    : hasBack
                    ? 0
                    : largeText
                    ? 48
                    : 112))
            .clamp(48.0, double.infinity);
    final measuredTitle = TextPainter(
      text: TextSpan(text: title, style: titleStyle),
      textDirection: Directionality.of(context),
      textScaler: headerScaler,
    )..layout(maxWidth: titleWidth);
    final toolbarHeight =
        (measuredTitle.height +
                (subtitle == null ? 0 : headerScaler.scale(20)) +
                48)
            .clamp(104.0, double.infinity);
    measuredTitle.dispose();
    return Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: showAppBar
          ? AppBar(
              automaticallyImplyLeading: false,
              toolbarHeight: toolbarHeight,
              leading: !hasBack
                  ? null
                  : IconButton(
                      tooltip: 'Kembali',
                      icon: const Icon(Icons.arrow_back, size: 28),
                      onPressed: () {
                        if (router?.canPop() == true) {
                          router!.pop();
                        } else {
                          navigate(
                            path.startsWith('/rooms/')
                                ? '/rooms'
                                : path.startsWith('/invoices/')
                                ? '/invoices'
                                : path.startsWith('/expenses/')
                                ? '/expenses'
                                : path.startsWith('/leases/')
                                ? '/leases'
                                : '/menu',
                          );
                        }
                      },
                    ),
              title: MediaQuery.withClampedTextScaling(
                maxScaleFactor: 1.3,
                child: subtitle == null
                    ? Text(
                        title,
                        softWrap: true,
                        overflow: TextOverflow.visible,
                      )
                    : Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title,
                            softWrap: true,
                            overflow: TextOverflow.visible,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            subtitle!,
                            style: const TextStyle(
                              fontSize: 14,
                              height: 1.2,
                              fontWeight: FontWeight.w400,
                              color: KamarthaColors.secondary,
                            ),
                          ),
                        ],
                      ),
              ),
              actions:
                  actions ??
                  [
                    if (!hasBack && largeText)
                      IconButton(
                        tooltip: 'Menu',
                        onPressed: () => navigate('/menu'),
                        icon: const Icon(Icons.menu),
                      )
                    else if (!hasBack)
                      TextButton(
                        onPressed: () => navigate('/menu'),
                        child: const Text(
                          'kamartha',
                          style: TextStyle(
                            color: KamarthaColors.brand,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                  ],
            )
          : null,
      body: SafeArea(
        top: !showAppBar,
        bottom: !compact || !mainScreen,
        child: Row(
          children: [
            if (!compact)
              SizedBox(
                width: 184,
                child: ListView(
                  children: [
                    const Padding(
                      padding: EdgeInsets.all(20),
                      child: Text(
                        'kamartha',
                        style: TextStyle(
                          color: KamarthaColors.brand,
                          fontWeight: FontWeight.w600,
                          fontSize: 24,
                        ),
                      ),
                    ),
                    for (final entry in [
                      ('Beranda', '/home'),
                      ('Kamar', '/rooms'),
                      if (!preparation) ('Tagihan', '/invoices'),
                      ('Menu', '/menu'),
                      if (preparation) ('Data awal', '/initialization'),
                      ('Penghuni', '/residents'),
                      if (!preparation) ...[
                        ('Masa sewa', '/leases'),
                        ('Pengeluaran', '/expenses'),
                        ('Laporan', '/reports'),
                      ],
                    ])
                      ListTile(
                        title: Text(entry.$1),
                        selected: path == entry.$2,
                        selectedColor: KamarthaColors.primary,
                        selectedTileColor: KamarthaColors.warningBackground,
                        onTap: () => navigate(entry.$2),
                      ),
                  ],
                ),
              ),
            Expanded(
              child: Align(
                alignment: Alignment.topCenter,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1000),
                  child: child,
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar:
          compact && mainScreen && MediaQuery.viewInsetsOf(context).bottom == 0
          ? KamarthaFloatingNavBar(
              selectedIndex: selected,
              onSelected: (index) {
                if (index == 2 && preparation) {
                  navigate('/initialization');
                } else {
                  navigate(['/home', '/rooms', '/invoices', '/menu'][index]);
                }
              },
            )
          : null,
    );
  }
}
