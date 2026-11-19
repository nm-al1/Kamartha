import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/initialization/views/opening_import_page.dart';

class ImportApi extends BusinessRepository {
  ImportApi() : super(Dio());
  final keys = <String?>[];
  final payloads = <Map<String, dynamic>>[];
  bool fail = false;

  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    expect(method, 'POST');
    expect(path, '/initialization/import/confirm');
    keys.add(key);
    payloads.add(data);
    if (fail) {
      throw DioException(
        requestOptions: RequestOptions(path: path),
        type: DioExceptionType.receiveTimeout,
      );
    }
    return {'created_rooms': 1, 'created_residents': 1, 'created_records': 1};
  }
}

Map<String, dynamic> preview({bool valid = true}) => {
  'preview_hash': 'a' * 64,
  'tables': {
    'Kamar': [
      ['DUMMY-01'],
    ],
  },
  'can_import': valid,
  'cutover_date': '2026-11-12',
  'new_rooms': 1,
  'new_residents': 1,
  'new_records': 1,
  'total_receivable': 200000,
  'errors': valid
      ? []
      : [
          {
            'sheet': 'Kontrak',
            'row': 2,
            'message': 'Tagihan periode berjalan wajib dimasukkan.',
          },
        ],
  'items': [
    {
      'sheet': 'Kontrak',
      'row': 2,
      'label': 'K001',
      'status': 'NEW',
      'room_number': 'DUMMY-01',
      'residents': ['Penghuni Dummy'],
      'price': 700000,
      'remaining': 200000,
      'occupants': [
        {
          'name': 'Penghuni Dummy',
          'resident_id': 'resident',
          'entered_on': '2026-11-01',
          'state': 'STAYING',
        },
      ],
      'data': {
        'starts_on': '2026-11-01',
        'ends_on': '2026-12-01',
        'responsible_resident_id': 'resident',
        'occupancies': [
          {
            'resident_id': 'resident',
            'entered_on': '2026-11-01',
            'state': 'STAYING',
          },
        ],
        'invoices': [
          {
            'period_start': '2026-11-01',
            'due_on': '2026-11-01',
            'amount': 700000,
            'opening_paid': 500000,
          },
        ],
      },
    },
  ],
};

Widget host(
  Map<String, dynamic> data,
  ImportApi api,
  VoidCallback saved, {
  double scale = 1,
}) => ProviderScope(
  overrides: [businessProvider.overrideWithValue(api)],
  child: MaterialApp(
    theme: kamarthaTheme(),
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context)
          .copyWith(textScaler: TextScaler.linear(scale)),
      child: child!,
    ),
    home: Scaffold(
      body: ListView(
        children: [
          OpeningImportReview(
            preview: data,
            onSaved: saved,
            onBusyChanged: (_) {},
          ),
        ],
      ),
    ),
  ),
);

void main() {
  testWidgets(
    'Invalid preview blocks confirmation and shows sheet row errors',
    (tester) async {
      final api = ImportApi();
      await tester.pumpWidget(
        host(preview(valid: false), api, () => fail('Must not save')),
      );
      await tester.pumpAndSettle();
      expect(find.textContaining('Kontrak · baris 2:'), findsOneWidget);
      await tester.scrollUntilVisible(find.byType(Checkbox), 150);
      expect(tester.widget<Checkbox>(find.byType(Checkbox)).onChanged, isNull);
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNull,
      );
      expect(api.payloads, isEmpty);
    },
  );

  for (final size in [const Size(320, 568), const Size(800, 360)]) {
    testWidgets(
      'Review requires explicit confirmation and retains retry at $size',
      (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = size;
        addTearDown(tester.view.resetDevicePixelRatio);
        addTearDown(tester.view.resetPhysicalSize);
        final api = ImportApi()..fail = true;
        final data = preview();
        var saved = false;
        await tester.pumpWidget(host(data, api, () => saved = true, scale: 2));
        await tester.pumpAndSettle();
        final submit = find.widgetWithText(
          FilledButton,
          'Konfirmasi impor draft',
        );
        await tester.scrollUntilVisible(
          find.byType(Checkbox),
          120,
          maxScrolls: 60,
        );
        expect(tester.widget<FilledButton>(submit).onPressed, isNull);
        await tester.ensureVisible(find.byType(Checkbox));
        await tester.pumpAndSettle();
        await tester.tap(find.byType(Checkbox));
        await tester.pumpAndSettle();
        await tester.ensureVisible(submit);
        await tester.pumpAndSettle();
        await tester.tap(submit);
        await tester.pumpAndSettle();
        expect(saved, isFalse);
        expect(api.payloads.single, {
          'tables': data['tables'],
          'preview_hash': data['preview_hash'],
          'confirmed': true,
        });
        api.fail = false;
        await tester.ensureVisible(submit);
        await tester.pumpAndSettle();
        await tester.tap(submit);
        await tester.pumpAndSettle();
        expect(saved, isTrue);
        expect(api.keys[0], isNotNull);
        expect(api.keys[1], api.keys[0]);
        expect(tester.takeException(), isNull);
      },
    );
  }
}
