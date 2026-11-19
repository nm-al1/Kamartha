import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/app/app.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/auth/views/auth_page.dart';
import 'package:kamartha/features/dashboard/views/home_page.dart';

import '../operations_test.dart' show OperationsApi;
import '../widget_test.dart' show FakeAuth;
import '../lease_forms_test.dart' show LeaseFormsApi;

import 'package:kamartha/features/rooms/views/master_page.dart';

void main() {
  testWidgets(
    'Room filters follow FigCraft three columns and full confirmation row',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(360, 800);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [businessProvider.overrideWithValue(LeaseFormsApi())],
          child: MaterialApp(
            theme: kamarthaTheme(),
            home: const MasterPage(rooms: true),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final all = tester.getRect(find.widgetWithText(TextButton, 'Semua'));
      final occupied = tester.getRect(
        find.widgetWithText(TextButton, 'Dihuni'),
      );
      final empty = tester.getRect(find.widgetWithText(TextButton, 'Kosong'));
      final confirm = tester.getRect(
        find.widgetWithText(TextButton, 'Perlu konfirmasi'),
      );
      expect(all.top, occupied.top);
      expect(all.top, empty.top);
      expect(all.width, closeTo(104, .1));
      expect(occupied.width, all.width);
      expect(empty.width, all.width);
      expect(confirm.left, 16);
      expect(confirm.width, 328);
      expect(confirm.top, greaterThanOrEqualTo(all.bottom + 8));
      await tester.tap(find.widgetWithText(TextButton, 'Kosong'));
      await tester.pumpAndSettle();
      expect(find.text('Belum ada data yang cocok.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Login keyboard reaches fields and opens recovery with Enter', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [authProvider.overrideWithValue(FakeAuth())],
        child: MaterialApp(
          theme: kamarthaTheme(),
          home: const AuthPage(action: 'login'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final fields = find.byType(EditableText);
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.pumpAndSettle();
    expect(
      tester.widget<EditableText>(fields.at(0)).focusNode.hasFocus,
      isTrue,
    );
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.pumpAndSettle();
    expect(
      tester.widget<EditableText>(fields.at(1)).focusNode.hasFocus,
      isTrue,
    );
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pumpAndSettle();
    expect(find.text('Pemulihan akun'), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect(tester.takeException(), isNull);
  });

  setUpAll(() async {
    final fonts = FontLoader('Inter')
      ..addFont(rootBundle.load('assets/fonts/Inter.ttf'));
    await fonts.load();
  });

  testWidgets(
    'Home follows FigCraft panel geometry, grouped rows and badge tabs',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(360, 800);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [businessProvider.overrideWithValue(OperationsApi())],
          child: MaterialApp(theme: kamarthaTheme(), home: const HomePage()),
        ),
      );
      await tester.pumpAndSettle();
      final panel = tester.getRect(
        find.byKey(const ValueKey('home-occupancy-panel')),
      );
      expect(panel.left, 16);
      expect(panel.top, closeTo(168, 3));
      expect(panel.width, 328);
      expect(panel.height, closeTo(167, 4));
      expect(find.text('Halo, admin'), findsOneWidget);
      expect(find.text('Selasa, 7 April 2026'), findsOneWidget);
      expect(find.byKey(const ValueKey('home-reminder-group')), findsOneWidget);
      expect(find.byKey(const ValueKey('home-invoice-count')), findsOneWidget);
    },
  );

  testWidgets(
    'Login uses FigCraft brand box, overlapping panel and external field labels',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(360, 800);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [authProvider.overrideWithValue(FakeAuth())],
          child: MaterialApp(
            theme: kamarthaTheme(),
            home: const AuthPage(action: 'login'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final logo = tester.getRect(
        find.byKey(const ValueKey('login-brand-mark')),
      );
      expect(logo.size, const Size(56, 56));
      expect(logo.top, closeTo(72, 2));
      final panel = tester.getRect(
        find.byKey(const ValueKey('login-form-panel')),
      );
      expect(panel.left, 16);
      expect(panel.top, closeTo(286, 4));
      expect(panel.width, 328);
      expect(find.text('Masukkan username'), findsOneWidget);
      expect(
        find.text('Pendaftaran ditutup setelah akun pengelola dibuat.'),
        findsOneWidget,
      );
      expect(find.text('Kamartha · Pengelola kos'), findsOneWidget);
    },
  );
}
