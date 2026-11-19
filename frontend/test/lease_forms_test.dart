import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/leases/views/leases_page.dart';

import 'operations_test.dart' show OperationsApi;

import 'package:kamartha/features/rooms/views/master_page.dart';

class LeaseFormsApi extends OperationsApi {
  LeaseFormsApi({this.ended = false});
  final bool ended;
  final writes = <String>[];
  final requestKeys = <String?>[];
  final payloads = <Map<String, dynamic>>[];
  bool rejectWrites = false;
  bool loseNextResponse = false;
  int committedWrites = 0;
  final committedResults = <String, Map<String, dynamic>>{};
  int leaseReads = 0;
  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async {
    if (path == '/initialization/settings') {
      return {
        'mode': 'ACTIVE',
        'packages': [
          {'id': 'package', 'occupant_type': 2, 'period_months': 1},
        ],
      };
    }
    if (path == '/rooms') {
      return {
        'items': [
          {
            'id': 'room',
            'number': 'UJI-01',
            'room_type': 'Kamar uji',
            'supported_occupants': 2,
          },
        ],
        'pagination': {'has_more': false},
      };
    }
    if (path == '/residents') {
      return {
        'items': [
          for (final id in ['a', 'b', 'c'])
            {
              'id': id,
              'name': 'Penghuni uji $id',
              'identity_number': 'UJI-$id',
            },
        ],
        'pagination': {'has_more': false},
      };
    }
    if (path == '/leases/lease') {
      leaseReads++;
      return {
        'id': 'lease',
        'package_id': 'package',
        'room_number': 'UJI-01',
        'starts_on': '2026-11-01',
        'effective_ends_on': '2026-12-01',
        'occupant_type_snapshot': 2,
        'period_months_snapshot': 1,
        'period_price_snapshot': 700000,
        'status': ended ? 'ENDED' : 'ACTIVE',
        'version': 1,
        'occupancies': [
          for (final id in ['a', 'b', 'c'])
            {
              'id': 'occupancy-$id',
              'resident_id': id,
              'name': 'Penghuni uji $id',
              'responsible': id == 'a',
              'state': id == 'c' ? 'EXITED' : 'STAYING',
              'entered_on': '2026-11-01',
              'exited_on': id == 'c' ? '2026-11-02' : null,
            },
        ],
        'invoices': [],
      };
    }
    return super.get(path, query);
  }

  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    writes.add(path);
    requestKeys.add(key);
    payloads.add(Map.of(data));
    if (rejectWrites) {
      final request = RequestOptions(path: path);
      throw DioException(
        requestOptions: request,
        response: Response(
          requestOptions: request,
          statusCode: 409,
          data: {
            'error': {'message': 'Uji server menolak perubahan'},
            'request_id': 'synthetic-rejection',
          },
        ),
      );
    }
    if (committedResults.containsKey(key)) return committedResults[key]!;
    committedWrites++;
    final result = {'id': 'created'};
    if (key != null) committedResults[key] = result;
    if (loseNextResponse) {
      loseNextResponse = false;
      throw DioException(
        requestOptions: RequestOptions(path: path),
        type: DioExceptionType.receiveTimeout,
      );
    }
    return result;
  }
}

Widget host(Widget page, LeaseFormsApi api, {double scale = 1}) =>
    ProviderScope(
      overrides: [businessProvider.overrideWithValue(api)],
      child: MaterialApp(
        theme: kamarthaTheme(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        home: page,
      ),
    );

void main() {
  for (final size in [const Size(320, 568), const Size(800, 360)]) {
    for (final rooms in [true, false]) {
      testWidgets(
        'Master form rooms=$rooms fits large text and keyboard at $size',
        (tester) async {
          tester.view.devicePixelRatio = 1;
          tester.view.physicalSize = size;
          addTearDown(tester.view.resetDevicePixelRatio);
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetViewInsets);
          final api = LeaseFormsApi();
          await tester.pumpWidget(
            host(MasterPage(rooms: rooms), api, scale: 2),
          );
          await tester.pumpAndSettle();
          await tester.tap(find.widgetWithText(TextButton, '+ Tambah'));
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          tester.view.viewInsets = const FakeViewPadding(bottom: 160);
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          await tester.enterText(find.byType(TextField).last, 'Uji');
        await tester.tap(rooms ? find.byTooltip('Kembali').last : find.widgetWithText(TextButton, 'Batal'));
          await tester.pumpAndSettle();
          expect(api.writes, isEmpty);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  for (final size in [
    const Size(320, 568),
    const Size(360, 800),
    const Size(390, 844),
    const Size(430, 932),
    const Size(800, 360),
  ]) {
    for (final action in [
      'Perpanjang',
      'Keluar',
      'Ganti penanggung jawab',
      'Tambah pengganti',
      'Kontrak lanjutan',
    ]) {
      testWidgets('$action supports large text keyboard and Escape at $size', (
        tester,
      ) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = size;
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetViewInsets);
        final api = LeaseFormsApi(ended: action == 'Kontrak lanjutan');
        await tester.pumpWidget(
          host(const LeaseDetailPage(id: 'lease'), api, scale: 2),
        );
        await tester.pumpAndSettle();
        final button = action == 'Keluar'
            ? find.widgetWithText(TextButton, action)
            : find.widgetWithText(FilledButton, action);
        await tester.scrollUntilVisible(
          button,
          120,
          scrollable: find
              .descendant(
                of: find.byType(ListView).last,
                matching: find.byType(Scrollable),
              )
              .first,
        );
        await tester.ensureVisible(button.first);
        await tester.pumpAndSettle();
        await tester.tap(button.first);
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        tester.view.viewInsets = const FakeViewPadding(bottom: 160);
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        final field = find
            .descendant(
              of: find.byType(AlertDialog),
              matching: find.byType(TextField),
            )
            .last;
        await tester.ensureVisible(field);
        await tester.enterText(field, '1');
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        final cancel = find.widgetWithText(TextButton, 'Batal');
        await tester.ensureVisible(cancel);
        await tester.pumpAndSettle();
        final bounds = tester.getRect(cancel);
        expect(bounds.top, greaterThanOrEqualTo(0));
        expect(bounds.bottom, lessThanOrEqualTo(size.height - 160));
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.sendKeyEvent(LogicalKeyboardKey.escape);
        await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsNothing);
        expect(api.writes, isEmpty);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets(
    'Lost response retry reuses key; changed input and confirmed success use new keys',
    (tester) async {
      final api = LeaseFormsApi()..loseNextResponse = true;
      await tester.pumpWidget(host(const LeaseDetailPage(id: 'lease'), api));
      await tester.pumpAndSettle();
      Future<void> extend(String periods) async {
        final action = find.widgetWithText(FilledButton, 'Perpanjang');
        final scroll = find
            .descendant(
              of: find.byType(ListView).last,
              matching: find.byType(Scrollable),
            )
            .first;
        await tester.drag(scroll, const Offset(0, 3000));
        await tester.pumpAndSettle();
        await tester.scrollUntilVisible(action, 120, scrollable: scroll);
        await tester.tap(action);
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), periods);
        await tester.tap(
          find.descendant(
            of: find.byType(AlertDialog),
            matching: find.widgetWithText(FilledButton, 'Perpanjang'),
          ),
        );
        await tester.pumpAndSettle();
      }

      await extend('1');
      expect(api.committedWrites, 1);
      await extend('1');
      expect(api.committedWrites, 1);
      expect(api.requestKeys[1], api.requestKeys[0]);
      await extend('1');
      expect(api.committedWrites, 2);
      expect(api.requestKeys[2], isNot(api.requestKeys[1]));
      api.rejectWrites = true;
      await extend('2');
      await extend('3');
      expect(api.requestKeys[4], isNot(api.requestKeys[3]));
      expect(api.committedWrites, 2);
      expect(tester.takeException(), isNull);
    },
  );
  for (final entry in [
    ('Perpanjang', 'Perpanjang', '/leases/lease/extend'),
    ('Keluar', 'Simpan keluar', '/leases/lease/occupancies/occupancy-a/exit'),
    ('Ganti penanggung jawab', 'Simpan', '/leases/lease/responsible'),
    ('Tambah pengganti', 'Simpan pengganti', '/leases/lease/occupancies'),
    ('Kontrak lanjutan', 'Simpan lanjutan', '/leases/lease/continue'),
  ]) {
    testWidgets(
      '${entry.$1} sends expected data and reloads or navigates after success',
      (tester) async {
        final api = LeaseFormsApi(ended: entry.$1 == 'Kontrak lanjutan');
        final router = GoRouter(
          initialLocation: '/leases/lease',
          routes: [
            GoRoute(
              path: '/leases/lease',
              builder: (_, _) => const LeaseDetailPage(id: 'lease'),
            ),
            GoRoute(
              path: '/leases/created',
              builder: (_, _) =>
                  const Scaffold(body: Text('Kontrak hasil uji')),
            ),
          ],
        );
        addTearDown(router.dispose);
        await tester.pumpWidget(
          ProviderScope(
            overrides: [businessProvider.overrideWithValue(api)],
            child: MaterialApp.router(
              theme: kamarthaTheme(),
              routerConfig: router,
            ),
          ),
        );
        await tester.pumpAndSettle();
        final action = entry.$1 == 'Keluar'
            ? find.widgetWithText(TextButton, entry.$1)
            : find.widgetWithText(FilledButton, entry.$1);
        final scroll = find
            .descendant(
              of: find.byType(ListView).last,
              matching: find.byType(Scrollable),
            )
            .first;
        await tester.scrollUntilVisible(action, 120, scrollable: scroll);
        await Scrollable.ensureVisible(
          tester.element(action.first),
          alignment: .5,
        );
        await tester.pumpAndSettle();
        await tester.tap(action.first);
        await tester.pumpAndSettle();
        final reason = find.byWidgetPredicate(
          (w) => w is TextField && w.decoration?.labelText == 'Alasan',
        );
        if (reason.evaluate().isNotEmpty) {
          await tester.enterText(reason, 'Alasan pengujian');
        }
        if (entry.$1 == 'Keluar') {
          await tester.tap(find.byType(DropdownButtonFormField<String>));
          await tester.pumpAndSettle();
          await tester.tap(find.text('Penghuni uji b').last);
          await tester.pumpAndSettle();
        }
        await tester.tap(
          find.descendant(
            of: find.byType(AlertDialog),
            matching: find.widgetWithText(FilledButton, entry.$2),
          ),
        );
        await tester.pumpAndSettle();
        expect(api.writes.single, entry.$3);
        final payload = api.payloads.single;
        switch (entry.$1) {
          case 'Perpanjang':
            expect(payload, {'periods': 1, 'expected_version': 1});
          case 'Keluar':
            expect(payload['successor_resident_id'], 'b');
            expect(payload['exited_on'], matches(r'^\d{4}-\d{2}-\d{2}$'));
          case 'Ganti penanggung jawab':
            expect(payload['occupancy_id'], 'occupancy-b');
          case 'Tambah pengganti':
            expect(payload['resident_id'], 'c');
            expect(payload['predecessor_occupancy_id'], 'occupancy-c');
          case 'Kontrak lanjutan':
            expect(payload['package_id'], 'package');
            expect(payload['resident_ids'], ['a', 'b']);
            expect(payload['responsible_resident_id'], 'a');
            expect(payload['periods'], 1);
            expect(payload['price'], 700000);
            expect(payload['starts_on'], '2026-12-01');
        }
        if (entry.$1 == 'Kontrak lanjutan') {
          expect(find.text('Kontrak hasil uji'), findsOneWidget);
        } else {
          expect(api.leaseReads, 2);
        }
        expect(tester.takeException(), isNull);
      },
    );
  }
  for (final entry in [
    ('Perpanjang', 'Perpanjang', '/leases/lease/extend'),
    ('Keluar', 'Simpan keluar', '/leases/lease/occupancies/occupancy-a/exit'),
    ('Ganti penanggung jawab', 'Simpan', '/leases/lease/responsible'),
    ('Tambah pengganti', 'Simpan pengganti', '/leases/lease/occupancies'),
    ('Kontrak lanjutan', 'Simpan lanjutan', '/leases/lease/continue'),
  ]) {
    testWidgets('${entry.$1} reports a rejected save and permits retry', (
      tester,
    ) async {
      final api = LeaseFormsApi(ended: entry.$1 == 'Kontrak lanjutan')
        ..rejectWrites = true;
      await tester.pumpWidget(host(const LeaseDetailPage(id: 'lease'), api));
      await tester.pumpAndSettle();
      Future<void> submit() async {
        final action = entry.$1 == 'Keluar'
            ? find.widgetWithText(TextButton, entry.$1)
            : find.widgetWithText(FilledButton, entry.$1);
        final scroll = find
            .descendant(
              of: find.byType(ListView).last,
              matching: find.byType(Scrollable),
            )
            .first;
        if (action.evaluate().isEmpty) {
          await tester.drag(scroll, const Offset(0, 2000));
          await tester.pumpAndSettle();
        }
        await tester.scrollUntilVisible(action, 120, scrollable: scroll);
        await Scrollable.ensureVisible(
          tester.element(action.first),
          alignment: .5,
        );
        await tester.pumpAndSettle();
        await tester.tap(action.first);
        await tester.pumpAndSettle();
        final reason = find.byWidgetPredicate(
          (w) => w is TextField && w.decoration?.labelText == 'Alasan',
        );
        if (reason.evaluate().isNotEmpty) {
          await tester.enterText(reason, 'Alasan pengujian');
        }
        await tester.tap(
          find.descendant(
            of: find.byType(AlertDialog),
            matching: find.widgetWithText(FilledButton, entry.$2),
          ),
        );
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
      }

      await submit();
      expect(api.writes.single, entry.$3);
      final pageScroll = find
          .descendant(
            of: find.byType(ListView).last,
            matching: find.byType(Scrollable),
          )
          .first;
      await tester.drag(pageScroll, const Offset(0, 3000));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Uji server menolak perubahan'),
        findsOneWidget,
      );
      await submit();
      expect(api.writes, [entry.$3, entry.$3]);
      expect(api.requestKeys.first, isNotNull);
      expect(api.requestKeys.last, api.requestKeys.first);
      if (entry.$1 == 'Perpanjang') {
        expect(api.payloads.first, {'periods': 1, 'expected_version': 1});
      } else {
        expect(api.payloads.first['reason'], 'Alasan pengujian');
      }
    });
  }
  for (final action in [
    'Keluar',
    'Ganti penanggung jawab',
    'Tambah pengganti',
    'Kontrak lanjutan',
  ]) {
    testWidgets('$action focused dialog cancels safely', (tester) async {
      final api = LeaseFormsApi(ended: action == 'Kontrak lanjutan');
      await tester.pumpWidget(host(const LeaseDetailPage(id: 'lease'), api));
      await tester.pumpAndSettle();
      final button = action == 'Keluar'
          ? find.widgetWithText(TextButton, action)
          : find.widgetWithText(FilledButton, action);
      final scroll = find
          .descendant(
            of: find.byType(ListView).last,
            matching: find.byType(Scrollable),
          )
          .first;
      await tester.scrollUntilVisible(button, 120, scrollable: scroll);
      await Scrollable.ensureVisible(
        tester.element(button.first),
        alignment: .5,
      );
      await tester.pumpAndSettle();
      await tester.tap(button.first);
      await tester.pumpAndSettle();
      expect(find.byType(AlertDialog), findsOneWidget);
      await tester.enterText(find.byType(TextField).first, 'uji');
      await tester.tap(find.widgetWithText(TextButton, 'Batal'));
      await tester.pumpAndSettle();
      expect(api.writes, isEmpty);
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets(
    'Focused extension dialog cancels without disposed-controller errors',
    (tester) async {
      final api = LeaseFormsApi();
      await tester.pumpWidget(host(const LeaseDetailPage(id: 'lease'), api));
      await tester.pumpAndSettle();
      final action = find.widgetWithText(FilledButton, 'Perpanjang');
      await tester.scrollUntilVisible(
        action,
        120,
        scrollable: find
            .descendant(
              of: find.byType(ListView).last,
              matching: find.byType(Scrollable),
            )
            .first,
      );
      await tester.tap(action);
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), '2');
      await tester.tap(find.widgetWithText(TextButton, 'Batal'));
      await tester.pumpAndSettle();
      expect(api.writes, isEmpty);
      expect(tester.takeException(), isNull);
    },
  );

  for (final width in [320.0, 360.0, 390.0, 430.0]) {
    testWidgets('New contract validates at $width with 200 percent text', (
      tester,
    ) async {
      tester.view.devicePixelRatio = 1;
      tester.view.physicalSize = Size(width, 568);
      addTearDown(tester.view.resetDevicePixelRatio);
      addTearDown(tester.view.resetPhysicalSize);
      final api = LeaseFormsApi();
      await tester.pumpWidget(host(const LeaseCreatePage(), api, scale: 2));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      final review = find.widgetWithText(FilledButton, 'Tinjau kontrak');
      await tester.scrollUntilVisible(
        review,
        160,
        scrollable: find.byType(Scrollable).first,
      );
      await Scrollable.ensureVisible(tester.element(review), alignment: .5);
      await tester.pumpAndSettle();
      await tester.tap(review);
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Pilih penanggung jawab.'),
        -100,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('Pilih penanggung jawab.'), findsOneWidget);
      expect(api.writes, isEmpty);
      expect(tester.takeException(), isNull);
    });
  }
}
