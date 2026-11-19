import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/app/app.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/auth/repositories/auth_repository.dart';
import 'package:kamartha/features/initialization/views/opening_record_form.dart';

class OpeningApi extends BusinessRepository {
  OpeningApi() : super(Dio());
  final settings = <String, dynamic>{
    'mode': 'PREPARATION',
    'version': 1,
    'cutover_date': null,
    'packages': [
      {'id': 'package', 'occupant_type': 1, 'period_months': 1},
    ],
  };
  final records = <Map<String, dynamic>>[];
  bool fail = false;
  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async {
    if (fail) throw Exception('test connection failure');
    if (path == '/auth/me') {
      return {'username': 'admin', 'mode': settings['mode']};
    }
    if (path == '/dashboard') {
      return {
        'rooms': {
          'total': 0,
          'occupied': 0,
          'empty': 0,
          'needs_confirmation': 0,
        },
        'people_staying': 0,
        'active_contracts': 0,
        'receivables': 0,
        'overdue_receivables': 0,
        'reminders': {'invoices': [], 'leases': []},
      };
    }
    if (path == '/initialization/settings') return Map.of(settings);
    if (path == '/initialization/reconciliation') {
      return {
        'version': settings['version'],
        'cutover_date': settings['cutover_date'],
        'reconciliation_hash': 'a' * 64,
        'can_finalize': records.isNotEmpty,
        'record_count': records.length,
        'resident_count': 1,
        'occupied_room_count': 1,
        'invoice_count': 1,
        'total_receivable': 100000,
        'errors': [],
        'records': records.isEmpty
            ? []
            : [
                {
                  'room_number': 'A1',
                  'occupant_type': 1,
                  'period_months': 1,
                  'starts_on': '2026-01-01',
                  'ends_on': '2026-03-01',
                  'price': 500000,
                  'occupancies': [
                    {
                      'name': 'Dummy',
                      'state': 'STAYING',
                      'entered_on': '2026-01-01',
                    },
                  ],
                  'invoices': [
                    {
                      'period_start': '2026-02-01',
                      'due_on': '2026-02-01',
                      'amount': 500000,
                      'opening_paid': 400000,
                      'remaining': 100000,
                    },
                  ],
                },
              ],
      };
    }
    return {
      'items': path == '/initialization/records' ? records : [],
      'pagination': {'has_more': false},
    };
  }

  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    if (path == '/billing/synchronize') return {'created': 0};
    if (path == '/initialization/settings') {
      settings['cutover_date'] = data['cutover_date'];
      settings['version'] = 2;
      return Map.of(settings);
    }
    if (path == '/initialization/finalize') {
      settings['mode'] = 'ACTIVE';
      return {'mode': 'ACTIVE'};
    }
    final record = {
      'id': 'record',
      'version': 1,
      'state': 'DRAFT',
      'draft_data': data['draft_data'],
    };
    records.clear();
    records.add(record);
    settings['version'] = (settings['version'] as int) + 1;
    return record;
  }
}

class OpeningAuth extends AuthRepository {
  OpeningAuth(this.business) : super(Dio());
  final OpeningApi business;
  bool signedIn = true;
  @override
  Future<Map<String, dynamic>?> me() async => signedIn
      ? {'username': 'admin', 'mode': business.settings['mode']}
      : null;
  @override
  Future<Map<String, dynamic>> csrf() async => {
    'csrf_token': 'test',
    'setup_available': false,
  };
  @override
  Future<void> submit(String action, Map<String, dynamic> values) async {
    signedIn = action == 'login';
  }
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Removing an occupancy keeps the remaining resident selection', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(640, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: OpeningRecordForm(
            rooms: const [],
            packages: const [],
            residents: const [
              {'id': 'first', 'name': 'First', 'identity_number': '1'},
              {'id': 'second', 'name': 'Second', 'identity_number': '2'},
            ],
            initial: const {
              'occupancies': [
                {'resident_id': 'first', 'state': 'STAYING'},
                {'resident_id': 'second', 'state': 'STAYING'},
              ],
            },
            onSave: (_) async {},
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tapVisible(tester, find.text('Hapus baris penghuni').first);
    final remaining = tester.state<FormFieldState<String>>(
      find.byType(DropdownButtonFormField<String>).at(3),
    );
    expect(remaining.value, 'second');
  });

  testWidgets(
    'Preparation UI saves date, draft, edits, reviews and finalizes',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(1280, 1400));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final api = OpeningApi();
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            businessProvider.overrideWithValue(api),
            authProvider.overrideWithValue(OpeningAuth(api)),
          ],
          child: const KamarthaApp(),
        ),
      );
      await tester.pumpAndSettle();
      await tapVisible(tester, find.text('Data awal'));
      expect(find.text('Persiapan pencatatan'), findsOneWidget);
      await tester.enterText(
        find.widgetWithText(TextField, 'YYYY-MM-DD'),
        '2026-02-01',
      );
      await tapVisible(tester, find.text('Simpan tanggal batas'));
      await tapVisible(tester, find.text('Tambah berkas'));
      await tester.scrollUntilVisible(
        find.text('Simpan draft'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tapVisible(tester, find.text('Simpan draft'));
      expect(api.records, hasLength(1));
      await tapVisible(tester, find.text('Berkas 1 • DRAFT'));
      await tester.scrollUntilVisible(
        find.text('Simpan draft'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tapVisible(tester, find.text('Simpan draft'));
      await tapVisible(tester, find.byType(CheckboxListTile).at(0));
      await tapVisible(tester, find.byType(CheckboxListTile).at(1));
      await tapVisible(tester, find.text('Tinjau finalisasi'));
      expect(
        find.text('Kunci data awal dan buka operasional?'),
        findsOneWidget,
      );
      await tapVisible(tester, find.text('Finalisasi'));
      expect(find.text('kamar dihuni'), findsOneWidget);
      expect(api.settings['mode'], 'ACTIVE');
      await tester.tap(find.byTooltip('Sesi pengelola'));
      await tester.pumpAndSettle();
      await tapVisible(tester, find.text('Ganti password'));
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password lama'),
        'DemoPass2026!',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password baru'),
        'NewDemoPass2026!',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Konfirmasi password'),
        'NewDemoPass2026!',
      );
      await tapVisible(
        tester,
        find.widgetWithText(FilledButton, 'Ganti password'),
      );
      expect(find.widgetWithText(FilledButton, 'Masuk'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Initialization reports errors and retries without inventing data',
    (tester) async {
      final api = OpeningApi()..fail = true;
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            businessProvider.overrideWithValue(api),
            authProvider.overrideWithValue(OpeningAuth(api)),
          ],
          child: const KamarthaApp(),
        ),
      );
      await tester.pumpAndSettle();
      await tapVisible(tester, find.text('Data awal'));
      expect(find.text('Muat ulang status'), findsOneWidget);
      api.fail = false;
      await tapVisible(tester, find.text('Muat ulang status'));
      expect(find.text('Simpan tanggal batas'), findsOneWidget);
    },
  );

  testWidgets(
    'Opening form serializes real selections and optional unknown exit',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(640, 1600));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      Map<String, dynamic>? saved;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpeningRecordForm(
              rooms: const [
                {'id': 'room', 'number': 'A1', 'room_type': 'Standar'},
              ],
              residents: const [
                {'id': 'person', 'name': 'Dummy', 'identity_number': 'TEST'},
              ],
              packages: const [
                {'id': 'package', 'occupant_type': 1, 'period_months': 1},
              ],
              initial: const {
                'room_id': 'room',
                'package_id': 'package',
                'responsible_resident_id': 'person',
                'starts_on': '2026-01-01',
                'ends_on': '2026-03-01',
                'price': 500000,
                'occupancies': [
                  {
                    'resident_id': 'person',
                    'entered_on': '2026-01-01',
                    'state': 'EXITED',
                    'exit_date_unknown': true,
                  },
                ],
                'invoices': [
                  {
                    'period_start': '2026-02-01',
                    'due_on': '2026-02-01',
                    'amount': 500000,
                    'opening_paid': 100000,
                  },
                ],
              },
              onSave: (value) async {
                saved = value;
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Simpan draft'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tapVisible(tester, find.text('Simpan draft'));
      expect(saved!['room_id'], 'room');
      expect(saved!['price'], 500000);
      expect(saved!['occupancies'][0]['exit_date_unknown'], isTrue);
      expect(saved!['invoices'][0]['opening_paid'], 100000);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Opening form reports an invalid nominal inline and focuses the field',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(640, 1600));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      var saved = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpeningRecordForm(
              rooms: const [],
              residents: const [],
              packages: const [],
              initial: const {'price': '500.000'},
              onSave: (_) async {
                saved = true;
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Simpan draft'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tapVisible(tester, find.text('Simpan draft'));
      expect(saved, isFalse);
      expect(
        find.text('Isi nominal rupiah bulat lebih dari 0.'),
        findsOneWidget,
      );
      final price = tester.widget<TextField>(
        find.widgetWithText(
          TextField,
          'Harga kesepakatan per periode (rupiah)',
        ),
      );
      expect(price.focusNode!.hasFocus, isTrue);
    },
  );

  testWidgets(
    'Opening form attaches server field errors without an Exception prefix',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(640, 1600));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final request = RequestOptions(path: '/initialization/records');
      final failure = DioException(
        requestOptions: request,
        response: Response(
          requestOptions: request,
          statusCode: 422,
          data: {
            'error': {
              'code': 'VALIDATION_ERROR',
              'message': 'Periksa isian yang diberikan.',
              'fields': [
                {'field': 'body.draft_data.price', 'code': 'int_parsing'},
              ],
            },
            'request_id': 'test',
          },
        ),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpeningRecordForm(
              rooms: const [],
              residents: const [],
              packages: const [],
              initial: const {'price': '500000'},
              onSave: (_) async {
                throw failure;
              },
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Simpan draft'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tapVisible(tester, find.text('Simpan draft'));
      expect(find.text('Isian tidak sesuai.'), findsOneWidget);
      expect(
        find.textContaining('Periksa isian yang diberikan.'),
        findsOneWidget,
      );
      expect(find.textContaining('Exception:'), findsNothing);
    },
  );

  test(
    'Business repository paginates and sends CSRF and idempotency headers',
    () async {
      final dio = Dio();
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            if (options.method != 'GET') {
              expect(options.headers['X-CSRF-Token'], 'csrf');
              expect(options.headers['Idempotency-Key'], 'key');
              handler.resolve(
                Response(
                  requestOptions: options,
                  data: {
                    'data': {'saved': true},
                  },
                ),
              );
            } else if (options.path == '/auth/csrf') {
              handler.resolve(
                Response(
                  requestOptions: options,
                  data: {
                    'data': {'csrf_token': 'csrf'},
                  },
                ),
              );
            } else {
              final first = options.queryParameters['offset'] == 0;
              handler.resolve(
                Response(
                  requestOptions: options,
                  data: {
                    'data': {
                      'items': [
                        {'id': first ? 'first' : 'last'},
                      ],
                      'pagination': {'has_more': first},
                    },
                  },
                ),
              );
            }
          },
        ),
      );
      final repo = BusinessRepository(dio);
      expect(await repo.all('/rooms'), hasLength(2));
      expect(
        (await repo.write('POST', '/rooms', {
          'number': 'A1',
        }, key: 'key'))['saved'],
        isTrue,
      );
      dio.close();
    },
  );
}
