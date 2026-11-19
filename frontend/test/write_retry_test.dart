import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/features/invoices/views/invoices_page.dart';
import 'package:kamartha/features/leases/views/leases_page.dart';

import 'lease_forms_test.dart' show LeaseFormsApi, host;

void main() {
  Future<void> reveal(WidgetTester tester, Finder target) async {
    await tester.scrollUntilVisible(target, 100, scrollable: find.byType(Scrollable).first);
    await Scrollable.ensureVisible(tester.element(target), alignment: .5);
    await tester.pumpAndSettle();
  }

  Widget launch(Widget page) => Builder(builder: (context) => Scaffold(body: FilledButton(
    onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page)), child: const Text('Mulai uji'))));

  testWidgets('Payment committed then lost response retries nested allocations with same key', (tester) async {
    final api = LeaseFormsApi()..loseNextResponse = true;
    await tester.pumpWidget(host(launch(const PaymentFormPage(invoice: {
      'id': 'invoice', 'lease_id': 'lease', 'remaining': 700000, 'room_number': 'UJI-01',
      'resident_names': 'Penghuni Dummy', 'period_start': '2026-11-01', 'period_end': '2026-12-01',
    })), api));
    await tester.tap(find.text('Mulai uji'));
    await tester.pumpAndSettle();
    final amount = find.byKey(const ValueKey('payment-amount'));
    await reveal(tester, amount);
    await tester.enterText(amount, '700000');
    final review = find.widgetWithText(FilledButton, 'Tinjau pembayaran');
    await reveal(tester, review);
    await tester.tap(review);
    await tester.pumpAndSettle();
    await reveal(tester, find.byType(Checkbox));
    await tester.tap(find.byType(Checkbox));
    await tester.pumpAndSettle();
    final save = find.widgetWithText(FilledButton, 'Simpan pembayaran');
    await reveal(tester, save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    expect(api.committedWrites, 1);
    await reveal(tester, save);
    await tester.tap(save);
    await tester.pumpAndSettle();
    expect(api.requestKeys, hasLength(2));
    expect(api.requestKeys[0], api.requestKeys[1]);
    expect(api.committedWrites, 1);
    expect(find.text('Mulai uji'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('New lease lost response retry retains resident-list request identity', (tester) async {
    final api = LeaseFormsApi()..loseNextResponse = true;
    await tester.pumpWidget(host(launch(const LeaseCreatePage()), api));
    await tester.tap(find.text('Mulai uji'));
    await tester.pumpAndSettle();
    Future<void> select(String label, String option) async {
      final field = find.widgetWithText(DropdownButtonFormField<String>, label);
      await reveal(tester, field);
      await tester.tap(field);
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining(option).last);
      await tester.pumpAndSettle();
    }
    await select('Kamar', 'UJI-01');
    await select('Paket', '2 orang / 1 bulan');
    final price = find.widgetWithText(TextFormField, 'Harga total per periode (rupiah)');
    await reveal(tester, price);
    await tester.enterText(price, '1000000');
    await select('Penghuni pertama', 'Penghuni uji a');
    await select('Penghuni kedua', 'Penghuni uji b');
    await select('Penanggung jawab', 'Penghuni uji a');
    Future<void> submit() async {
      final review = find.widgetWithText(FilledButton, 'Tinjau kontrak');
      await reveal(tester, review);
      await tester.tap(review);
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(FilledButton, 'Simpan kontrak'));
      await tester.pumpAndSettle();
    }
    await submit();
    expect(api.committedWrites, 1);
    await submit();
    expect(api.requestKeys, hasLength(2));
    expect(api.requestKeys[0], api.requestKeys[1]);
    expect(api.committedWrites, 1);
    expect(find.text('Mulai uji'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
