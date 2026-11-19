import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/features/dashboard/views/home_page.dart';
import 'package:kamartha/features/expenses/views/expenses_page.dart';
import 'package:kamartha/features/invoices/views/invoices_page.dart';
import 'package:kamartha/features/reports/views/reports_page.dart';
import 'package:kamartha/features/leases/views/leases_page.dart';
import 'package:kamartha/features/rooms/views/master_page.dart';

class OperationsApi extends BusinessRepository {
  OperationsApi({this.mode = 'ACTIVE'}) : super(Dio());
  final String mode;
  int synchronizations = 0;
  bool expenseCancelled = false;
  final expenseWrites = <Map<String, dynamic>>[];

  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async {
    if (path == '/auth/me') return {'mode': mode, 'username': 'admin'};
    if (path == '/residents/resident') {
      return {
        'id': 'resident',
        'name': 'Penghuni uji',
        'identity_type': 'KTP',
        'identity_number': 'UJI-IDENTITAS',
        'history': [
          {
            'room_number': 'B1',
            'lease_id': 'lease',
            'state': 'EXITED',
            'entered_on': '2026-11-01',
            'exited_on': null,
            'exit_date_unknown': true,
            'starts_on': '2026-11-01',
            'effective_ends_on': '2026-12-01',
          },
        ],
      };
    }
    if (path == '/initialization/settings') {
      return {'mode': mode, 'packages': []};
    }
    if (path == '/residents') {
      return {
        'items': [],
        'pagination': {'has_more': false},
      };
    }
    if (path == '/leases' || path == '/leases/lease') {
      final lease = {
        'id': 'lease',
        'room_number': 'B1',
        'resident_names': 'Penghuni uji',
        'starts_on': '2026-11-01',
        'effective_ends_on': '2026-12-01',
        'occupant_type_snapshot': 1,
        'period_months_snapshot': 1,
        'period_price_snapshot': 700000,
        'status': 'ACTIVE',
        'version': 1,
        'occupancies': [
          {
            'id': 'occupancy',
            'resident_id': 'resident',
            'name': 'Penghuni uji',
            'responsible': true,
            'state': 'STAYING',
            'entered_on': '2026-11-01',
          },
        ],
        'invoices': [
          {
            'period_start': '2026-11-01',
            'period_end': '2026-12-01',
            'amount': 700000,
            'paid_total': 0,
            'remaining': 700000,
            'payment_status': 'OVERDUE',
          },
        ],
      };
      return path == '/leases'
          ? {
              'items': [lease],
              'pagination': {'has_more': false},
            }
          : lease;
    }
    if (path == '/reports/cash') {
      return {
        'date_from': query!['date_from'],
        'date_to': query['date_to'],
        'income': 700000,
        'expense': 200000,
        'difference': 500000,
        'payments': [
          {
            'room_number': 'B1',
            'total_amount': 700000,
            'received_on': '2026-11-02',
            'method': 'TRANSFER',
            'status': 'CANCELLED',
          },
        ],
        'expenses': [],
      };
    }
    if (path == '/dashboard') {
      return {
        'today': '2026-04-07',
        'rooms': {
          'total': 2,
          'occupied': 1,
          'empty': 1,
          'needs_confirmation': 0,
        },
        'people_staying': 1,
        'active_contracts': 1,
        'receivables': 700000,
        'overdue_receivables': 700000,
        'reminders': {
          'invoices': [
            {
              'id': 'invoice',
              'room_number': 'B1',
              'resident_names': 'Dewi',
              'remaining': 700000,
              'due_on': '2026-03-10',
            },
          ],
          'leases': [],
        },
      };
    }
    if (path == '/invoices') {
      return {
        'items': [
          {
            'id': 'invoice',
            'room_number': 'B1',
            'resident_names': 'Dewi',
            'period_start': '2026-03-10',
            'period_end': '2026-04-10',
            'due_on': '2026-03-10',
            'remaining': 700000,
            'payment_status': 'OVERDUE',
          },
        ],
        'summary': {'total_remaining': 700000},
        'pagination': {'has_more': false},
      };
    }
    if (path == '/expenses/expense') {
      return {
        'id': 'expense',
        'expense_on': '2026-04-02',
        'amount': 200000,
        'category': 'INTERNET',
        'description': 'Internet April',
        'status': expenseCancelled ? 'CANCELLED' : 'VALID',
        'version': expenseCancelled ? 2 : 1,
        'attachment': null,
        'audits': expenseCancelled
            ? [
                {
                  'action': 'CANCEL',
                  'recorded_at': '2026-04-07T10:00:00+08:00',
                  'reason': 'Salah catat',
                },
              ]
            : [],
      };
    }
    if (path == '/expenses') {
      return {
        'items': [
          {
            'id': 'expense',
            'expense_on': '2026-04-02',
            'amount': 200000,
            'category': 'INTERNET',
            'description': 'Internet April',
            'status': 'VALID',
            'version': 1,
          },
        ],
        'pagination': {'has_more': false},
      };
    }
    return {};
  }

  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    if (path == '/billing/synchronize') synchronizations++;
    if (path.startsWith('/expenses/')) {
      expenseWrites.add({'method': method, 'path': path, ...data});
      if (path.endsWith('/cancel')) expenseCancelled = true;
    }
    return {'created': 0};
  }
}

Widget wrap(Widget child, OperationsApi api) => ProviderScope(
  overrides: [businessProvider.overrideWithValue(api)],
  child: MaterialApp(home: child),
);

void main() {
  testWidgets('Resident history preserves unknown exit dates', (tester) async {
    await tester.pumpWidget(
      wrap(const MasterPage(rooms: false, id: 'resident'), OperationsApi()),
    );
    await tester.pumpAndSettle();
    final scroll = find
        .descendant(
          of: find.byType(ListView).last,
          matching: find.byType(Scrollable),
        )
        .first;
    await tester.scrollUntilVisible(
      find.text('Tanggal tidak diketahui'),
      150,
      scrollable: scroll,
    );
    expect(find.text('Tanggal tidak diketahui'), findsOneWidget);
    expect(find.text('Sudah keluar'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('Lease detail exposes contract facts and preserves actions', (
    tester,
  ) async {
    await tester.pumpWidget(
      wrap(const LeaseDetailPage(id: 'lease'), OperationsApi()),
    );
    await tester.pumpAndSettle();
    expect(find.text('Detail kontrak'), findsOneWidget);
    expect(find.text('Harga per periode'), findsOneWidget);
    expect(find.text('Penghuni uji'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.widgetWithText(FilledButton, 'Perpanjang'),
      180,
      scrollable: find
          .descendant(
            of: find.byType(ListView).last,
            matching: find.byType(Scrollable),
          )
          .first,
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Perpanjang'));
    await tester.pumpAndSettle();
    expect(find.text('Perpanjang kontrak'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Batal'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'Cash report shows authoritative totals and cancelled transactions',
    (tester) async {
      await tester.pumpWidget(wrap(const ReportsPage(), OperationsApi()));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(FilledButton, 'Tampilkan'));
      await tester.pumpAndSettle();
      expect(find.text('Rp500.000'), findsOneWidget);
      final reportScroll = find
          .descendant(
            of: find.byType(ListView).last,
            matching: find.byType(Scrollable),
          )
          .first;
      await tester.scrollUntilVisible(
        find.text('Rincian penerimaan'),
        150,
        scrollable: reportScroll,
      );
      expect(find.text('Rincian penerimaan'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.textContaining('Transfer · Batal'),
        180,
        scrollable: reportScroll,
      );
      expect(find.textContaining('Transfer · Batal'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('Belum ada pengeluaran pada rentang ini.'),
        180,
        scrollable: reportScroll,
      );
      expect(
        find.text('Belum ada pengeluaran pada rentang ini.'),
        findsOneWidget,
      );
    },
  );
  test('Expense action text meets AA contrast', () {
    double contrast(Color a, Color b) {
      final x = a.computeLuminance(), y = b.computeLuminance();
      return ((x > y ? x : y) + .05) / ((x > y ? y : x) + .05);
    }

    expect(
      contrast(KamarthaColors.warningText, KamarthaColors.warningBackground),
      greaterThanOrEqualTo(4.5),
    );
    expect(
      contrast(KamarthaColors.dangerText, Colors.white),
      greaterThanOrEqualTo(4.5),
    );
  });
  testWidgets('Invoice list shows the authoritative remaining summary', (
    tester,
  ) async {
    await tester.pumpWidget(wrap(const InvoicesPage(), OperationsApi()));
    await tester.pumpAndSettle();
    expect(find.textContaining('Sisa tagihan aktif'), findsOneWidget);
    expect(find.text('Rp700.000'), findsWidgets);
    expect(find.text('Dewi'), findsOneWidget);
    expect(find.textContaining('Menunggak'), findsWidgets);
  });

  testWidgets('Payment review requires confirmation before saving', (
    tester,
  ) async {
    await tester.pumpWidget(
      wrap(
        PaymentFormPage(
          invoice: {
            'id': 'invoice',
            'lease_id': 'lease',
            'room_number': 'B1',
            'resident_names': 'Dewi',
            'period_start': '2026-03-10',
            'period_end': '2026-04-10',
            'due_on': '2026-03-10',
            'payment_status': 'OVERDUE',
            'amount': 700000,
            'paid_total': 0,
            'remaining': 700000,
          },
        ),
        OperationsApi(),
      ),
    );
    await tester.pumpAndSettle();
    final amount = find.byKey(const ValueKey('payment-amount'));
    await tester.scrollUntilVisible(
      amount,
      150,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.enterText(amount, '700000');
    final review = find.text('Tinjau pembayaran');
    await tester.ensureVisible(review);
    await tester.tap(review);
    await tester.pumpAndSettle();
    expect(find.text('Rincian penerimaan'), findsOneWidget);
    expect(find.text('Sisa setelah bayar'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.byType(Checkbox),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    FilledButton save() => tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Simpan pembayaran'),
    );
    expect(save().onPressed, isNull);
    await tester.tap(find.byType(Checkbox));
    await tester.pumpAndSettle();
    expect(save().onPressed, isNotNull);
  });

  testWidgets('Expense list shows category and status', (tester) async {
    await tester.pumpWidget(wrap(const ExpensesPage(), OperationsApi()));
    await tester.pumpAndSettle();
    expect(find.textContaining('Internet/Wi-Fi'), findsOneWidget);
    expect(find.text('Valid'), findsWidgets);
    expect(
      find.byWidgetPredicate(
        (widget) =>
            widget is Semantics &&
            widget.properties.button == true &&
            (widget.properties.label ?? '').startsWith(
              'Buka detail pengeluaran Internet/Wi-Fi, Internet April,',
            ),
      ),
      findsOneWidget,
    );
  });

  testWidgets('Expense detail shows data and correction form without writing', (
    tester,
  ) async {
    final api = OperationsApi();
    await tester.pumpWidget(wrap(const ExpenseDetailPage(id: 'expense'), api));
    await tester.pumpAndSettle();
    expect(find.text('Rp200.000'), findsOneWidget);
    expect(find.text('Internet April'), findsOneWidget);
    expect(find.text('Tidak ada'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, 'Koreksi'));
    await tester.pumpAndSettle();
    expect(find.text('Koreksi pengeluaran'), findsOneWidget);
    expect(find.text('Alasan koreksi'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Batal'));
    await tester.pumpAndSettle();
    expect(api.expenseWrites, isEmpty);
  });

  testWidgets(
    'Expense cancellation sends version and disables closed actions',
    (tester) async {
      final api = OperationsApi();
      await tester.pumpWidget(
        wrap(const ExpenseDetailPage(id: 'expense'), api),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(OutlinedButton, 'Batalkan'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), 'Salah catat');
      await tester.tap(
        find.widgetWithText(FilledButton, 'Batalkan pengeluaran'),
      );
      await tester.pumpAndSettle();
      expect(api.expenseWrites.single, {
        'method': 'POST',
        'path': '/expenses/expense/cancel',
        'expected_version': 1,
        'reason': 'Salah catat',
      });
      expect(
        tester
            .widget<FilledButton>(find.widgetWithText(FilledButton, 'Koreksi'))
            .onPressed,
        isNull,
      );
      expect(
        tester
            .widget<OutlinedButton>(
              find.widgetWithText(OutlinedButton, 'Batalkan'),
            )
            .onPressed,
        isNull,
      );
      await tester.scrollUntilVisible(
        find.textContaining('Dibatalkan ·'),
        200,
        scrollable: find.byType(Scrollable).last,
      );
      expect(find.textContaining('Dibatalkan ·'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Dashboard shows occupancy counts and renewal reminders', (
    tester,
  ) async {
    final api = OperationsApi();
    await tester.pumpWidget(wrap(const HomePage(), api));
    await tester.pumpAndSettle();
    expect(find.text('1 dari 2'), findsOneWidget);
    expect(find.text('orang tinggal'), findsOneWidget);
    expect(find.textContaining('Piutang: Rp700.000'), findsOneWidget);
    expect(find.text('Dewi'), findsOneWidget);
    expect(api.synchronizations, 1);
  });

  for (final width in [320.0, 360.0, 390.0, 430.0]) {
    testWidgets('FigCraft dashboard reflows at $width and 200 percent', (
      tester,
    ) async {
      await tester.binding.setSurfaceSize(Size(width, 568));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [businessProvider.overrideWithValue(OperationsApi())],
          child: MaterialApp(
            home: MediaQuery(
              data: MediaQueryData(
                size: Size(width, 568),
                textScaler: const TextScaler.linear(2),
              ),
              child: const HomePage(),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Halo, admin'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'Preparation dashboard does not synchronize operational invoices',
    (tester) async {
      final api = OperationsApi(mode: 'PREPARATION');
      await tester.pumpWidget(wrap(const HomePage(), api));
      await tester.pumpAndSettle();
      expect(find.text('Mode Persiapan'), findsOneWidget);
      expect(api.synchronizations, 0);
    },
  );
}
