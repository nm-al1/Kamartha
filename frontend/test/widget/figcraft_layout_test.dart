import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/app/app.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/auth/views/auth_page.dart';
import 'package:kamartha/features/expenses/views/expenses_page.dart';
import 'package:kamartha/features/invoices/views/invoices_page.dart';
import 'package:kamartha/features/menu/views/menu_page.dart';
import 'package:kamartha/features/rooms/views/master_page.dart';
import 'package:kamartha/features/reports/views/reports_page.dart';
import 'package:kamartha/features/initialization/views/initialization_page.dart';
import 'package:kamartha/features/initialization/views/opening_record_form.dart';
import 'package:kamartha/features/leases/views/leases_page.dart';

import '../operations_test.dart' show OperationsApi;
import '../stage_b_test.dart' show FakeBusiness;
import '../widget_test.dart' show FakeAuth;
import '../initialization_flow_test.dart' show OpeningApi;

void main() {
  for (final width in [320.0, 390.0, 1280.0]) {
    testWidgets('Login branding is centered at $width', (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 800);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [authProvider.overrideWithValue(FakeAuth())],
          child: MaterialApp(
            theme: kamarthaTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context)
                  .copyWith(textScaler: const TextScaler.linear(.8)),
              child: child!,
            ),
            home: const AuthPage(action: 'login'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final header = find
          .ancestor(
            of: find.byKey(const ValueKey('login-brand-mark')),
            matching: find.byType(Padding),
          )
          .first;
      expect(
        tester.getSize(header).width,
        closeTo(width < 480 ? width : 480, .5),
      );
      for (final element in [
        find.byKey(const ValueKey('login-brand-mark')),
        find.text('kamartha'),
        find.text('Kelola kos, lebih teratur.'),
      ]) {
        expect(tester.getCenter(element).dx, closeTo(width / 2, .5));
      }
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'Payment form and review remain usable with large text and keyboard',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(320, 568);
      tester.view.viewInsets = const FakeViewPadding(bottom: 180);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.view.resetViewInsets);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [businessProvider.overrideWithValue(OperationsApi())],
          child: MaterialApp(
            theme: kamarthaTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context)
                  .copyWith(textScaler: const TextScaler.linear(2)),
              child: child!,
            ),
            home: const PaymentFormPage(
              invoice: {
                'id': 'invoice',
                'lease_id': 'lease',
                'room_number': 'B1',
                'resident_names': 'Penghuni untuk pengujian layout',
                'period_start': '2026-11-01',
                'period_end': '2026-12-01',
                'payment_status': 'OVERDUE',
                'remaining': 700000,
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      final amount = find.byKey(const ValueKey('payment-amount'));
      await tester.scrollUntilVisible(
        amount,
        140,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.enterText(amount, '700000');
      await tester.pumpAndSettle();
      final review = find.widgetWithText(FilledButton, 'Tinjau pembayaran');
      await tester.ensureVisible(review);
      await tester.tap(review);
      tester.view.resetViewInsets();
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tester.scrollUntilVisible(
        find.byType(Checkbox),
        180,
        scrollable: find.byType(Scrollable).first,
      );
      await Scrollable.ensureVisible(
        tester.element(find.byType(Checkbox)),
        alignment: 0.5,
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byType(Checkbox));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<FilledButton>(
              find.widgetWithText(FilledButton, 'Simpan pembayaran'),
            )
            .onPressed,
        isNotNull,
      );
      expect(tester.takeException(), isNull);
    },
  );

  for (final width in [320.0, 360.0, 390.0, 430.0, 800.0, 1280.0]) {
    for (final entry in <(String, Widget, BusinessRepository)>[
      ('kamar', const MasterPage(rooms: true), FakeBusiness()),
      ('tagihan', const InvoicesPage(), OperationsApi()),
      ('pengeluaran', const ExpensesPage(), OperationsApi()),
      (
        'detail pengeluaran',
        const ExpenseDetailPage(id: 'expense'),
        OperationsApi(),
      ),
      ('menu', const MenuPage(), OperationsApi()),
      ('laporan', const ReportsPage(), OperationsApi()),
      ('data awal', const InitializationPage(), OpeningApi()),
      ('masa sewa', const LeasesPage(), OperationsApi()),
      (
        'detail penghuni',
        const MasterPage(rooms: false, id: 'resident'),
        OperationsApi(),
      ),
      ('detail kontrak', const LeaseDetailPage(id: 'lease'), OperationsApi()),
    ]) {
      testWidgets(
        '${entry.$1} fits $width at 200 percent without clipped layout',
        (tester) async {
          tester.view.devicePixelRatio = 1;
          tester.view.physicalSize = Size(
            width,
            width == 800
                ? 360
                : width == 1280
                ? 900
                : 568,
          );
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          await tester.pumpWidget(
            ProviderScope(
              overrides: [businessProvider.overrideWithValue(entry.$3)],
              child: MaterialApp(
                theme: kamarthaTheme(),
                builder: (context, child) => MediaQuery(
                  data: MediaQuery.of(context)
                      .copyWith(textScaler: const TextScaler.linear(2)),
                  child: child!,
                ),
                home: entry.$2,
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          final pageScroll = find
              .descendant(
                of: find.byType(ListView).last,
                matching: find.byType(Scrollable),
              )
              .first;
          if (entry.$1 == 'laporan') {
            final show = find.widgetWithText(FilledButton, 'Tampilkan');
            await tester.scrollUntilVisible(show, 120, scrollable: pageScroll);
            await Scrollable.ensureVisible(
              tester.element(show),
              alignment: 0.5,
            );
            await tester.pumpAndSettle();
            await tester.tap(show);
            await tester.pumpAndSettle();
            await tester.scrollUntilVisible(
              find.text('Rp500.000'),
              150,
              scrollable: pageScroll,
            );
            expect(tester.takeException(), isNull);
          }
          for (var i = 0; i < 4; i++) {
            await tester.drag(pageScroll, const Offset(0, -500));
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull);
          }
        },
      );
    }
  }

  testWidgets('Opening draft supports long labels with 200 percent text', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(320, 568);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: kamarthaTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: const TextScaler.linear(2)),
          child: child!,
        ),
        home: Scaffold(
          body: OpeningRecordForm(
            rooms: const [
              {
                'id': 'room',
                'number': 'UJI-01',
                'room_type': 'Kamar dengan keterangan panjang',
              },
            ],
            residents: const [],
            packages: const [],
            initial: const {'room_id': 'room'},
            onSave: (_) async {},
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    for (var i = 0; i < 8; i++) {
      await tester.drag(find.byType(Scrollable).first, const Offset(0, -200));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    }
    await tester.scrollUntilVisible(
      find.widgetWithText(FilledButton, 'Simpan draft'),
      120,
      scrollable: find.byType(Scrollable).first,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('Expense form reflows with 200 percent text and keyboard', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(320, 568);
    tester.view.viewInsets = const FakeViewPadding(bottom: 200);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetViewInsets);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [businessProvider.overrideWithValue(OperationsApi())],
        child: MaterialApp(
          theme: kamarthaTheme(),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context)
                .copyWith(textScaler: const TextScaler.linear(2)),
            child: child!,
          ),
          home: const ExpenseDetailPage(id: 'expense'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Koreksi'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.widgetWithText(FilledButton, 'Simpan'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Alasan minimal 3 karakter.'),
      160,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Alasan minimal 3 karakter.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Login can reach and validate its submit button with keyboard and 200 percent text',
    (tester) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = const Size(320, 568);
      tester.view.viewInsets = const FakeViewPadding(bottom: 200);
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.view.resetViewInsets);
      await tester.pumpWidget(
        ProviderScope(
          overrides: [authProvider.overrideWithValue(FakeAuth())],
          child: MaterialApp(
            theme: kamarthaTheme(),
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context)
                  .copyWith(textScaler: const TextScaler.linear(2)),
              child: child!,
            ),
            home: const AuthPage(action: 'login'),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final submit = find.widgetWithText(FilledButton, 'Masuk');
      await tester.ensureVisible(submit);
      await tester.pumpAndSettle();
      await tester.tap(submit);
      await tester.pumpAndSettle();
      expect(find.text('Username wajib diisi.'), findsOneWidget);
      expect(find.text('Password wajib diisi.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
