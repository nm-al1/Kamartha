import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/menu/views/menu_page.dart';

class MenuApi extends BusinessRepository {
  MenuApi(this.mode) : super(Dio());
  final String mode;
  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async => {'username': 'pengelola', 'mode': mode};
}

void main() {
  testWidgets('Menu exposes operational destinations only after finalization', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(360, 800);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [businessProvider.overrideWithValue(MenuApi('PREPARATION'))],
        child: const MaterialApp(home: MenuPage()),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Data awal'), findsOneWidget);
    expect(find.text('Pengeluaran'), findsNothing);
    expect(find.text('Laporan kas'), findsNothing);
    expect(find.text('pengelola'), findsOneWidget);
  });

  testWidgets('Menu opens resident management through an existing route', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(360, 800);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final router = GoRouter(
      initialLocation: '/menu',
      routes: [
        GoRoute(path: '/menu', builder: (_, _) => const MenuPage()),
        GoRoute(
          path: '/residents',
          builder: (_, _) => const Scaffold(body: Text('Daftar penghuni uji')),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [businessProvider.overrideWithValue(MenuApi('ACTIVE'))],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Penghuni'));
    await tester.pumpAndSettle();
    expect(find.text('Daftar penghuni uji'), findsOneWidget);
  });
}
