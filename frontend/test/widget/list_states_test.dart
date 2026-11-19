import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/expenses/views/expenses_page.dart';
import 'package:kamartha/features/invoices/views/invoices_page.dart';
import 'package:kamartha/features/leases/views/leases_page.dart';
import 'package:kamartha/features/rooms/views/master_page.dart';

import '../operations_test.dart' show OperationsApi;

class ListStateApi extends OperationsApi {
  ListStateApi(this.path);
  final String path;
  final pending = Completer<Map<String, dynamic>>();
  bool retry = false;

  @override
  Future<Map<String, dynamic>> get(String path, [Map<String, dynamic>? query]) {
    if (path != this.path) return super.get(path, query);
    if (!retry) return pending.future;
    return Future.value({
      'items': <Map<String, dynamic>>[],
      'pagination': {'has_more': false, 'total': 0},
      'summary': {'total_remaining': 0},
    });
  }
}

void main() {
  setUpAll(() async {
    final fonts = FontLoader('Inter')
      ..addFont(rootBundle.load('assets/fonts/Inter.ttf'));
    await fonts.load();
  });
  for (final entry in <(String, Widget)>[
    ('/rooms', const MasterPage(rooms: true)),
    ('/residents', const MasterPage(rooms: false)),
    ('/leases', const LeasesPage()),
    ('/invoices', const InvoicesPage()),
    ('/expenses', const ExpensesPage()),
  ]) {
    testWidgets(
      '${entry.$1} loading error retry and empty states at 200 percent',
      (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = const Size(320, 568);
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);
        final api = ListStateApi(entry.$1);
        await tester.pumpWidget(
          ProviderScope(
            overrides: [businessProvider.overrideWithValue(api)],
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
        await tester.pump();
        final scroll = find
            .descendant(
              of: find.byType(ListView).last,
              matching: find.byType(Scrollable),
            )
            .first;
        await tester.scrollUntilVisible(
          find.byType(LinearProgressIndicator),
          80,
          scrollable: scroll,
        );
        expect(find.byType(LinearProgressIndicator), findsOneWidget);
        final request = RequestOptions(path: entry.$1);
        api.pending.completeError(
          DioException(
            requestOptions: request,
            response: Response(
              requestOptions: request,
              statusCode: 503,
              data: {
                'error': {'message': 'Layanan uji sedang tidak tersedia.'},
                'request_id': 'synthetic-state',
              },
            ),
          ),
        );
        await tester.pumpAndSettle();
        final again = find.widgetWithText(TextButton, 'Coba lagi');
        await tester.scrollUntilVisible(again, 100, scrollable: scroll);
        expect(
          find.textContaining('Layanan uji sedang tidak tersedia.'),
          findsOneWidget,
        );
        api.retry = true;
        await Scrollable.ensureVisible(tester.element(again), alignment: .5);
        await tester.pumpAndSettle();
        await tester.tap(again);
        await tester.pumpAndSettle();
        await tester.drag(scroll, const Offset(0, -300));
        await tester.pumpAndSettle();
        expect(
          find.textContaining('Layanan uji sedang tidak tersedia.'),
          findsNothing,
        );
        expect(
          find.textContaining(RegExp('Belum ada|Tidak ada')),
          findsWidgets,
        );
        expect(find.byType(LinearProgressIndicator), findsNothing);
        expect(tester.takeException(), isNull);
      },
    );
  }
}
