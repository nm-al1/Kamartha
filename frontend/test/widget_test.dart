import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/app/app.dart';
import 'package:kamartha/core/money.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/auth/repositories/auth_repository.dart';

class FakeAuth extends AuthRepository {
  FakeAuth() : super(Dio());
  @override
  Future<Map<String, dynamic>?> me() async => null;
  @override
  Future<Map<String, dynamic>> csrf() async => {
    'setup_available': true,
    'csrf_token': 'test',
  };
}

class FlakyAuth extends FakeAuth {
  int attempts = 0;
  @override
  Future<Map<String, dynamic>?> me() async {
    attempts++;
    if (attempts == 1) throw Exception('offline');
    return null;
  }
}

class DemoAuth extends FakeAuth {
  bool created = false;
  bool signedIn = false;

  @override
  Future<Map<String, dynamic>?> me() async =>
      signedIn ? {'username': 'pengelola', 'mode': 'PREPARATION'} : null;

  @override
  Future<Map<String, dynamic>> csrf() async => {
    'setup_available': !created,
    'csrf_token': 'test',
  };

  @override
  Future<void> submit(String action, Map<String, dynamic> values) async {
    if (action == 'setup') created = true;
    signedIn = action == 'login';
  }
}

class DemoBusiness extends BusinessRepository {
  DemoBusiness() : super(Dio());
  int writes = 0;

  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async => path == '/auth/me'
      ? {'username': 'pengelola', 'mode': 'PREPARATION'}
      : {
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

  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    writes++;
    throw StateError('Preparation dashboard must not write business data');
  }
}

void main() {
  testWidgets('First setup logs in to the preparation dashboard and logs out', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1000, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final auth = DemoAuth();
    final business = DemoBusiness();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWithValue(auth),
          businessProvider.overrideWithValue(business),
        ],
        child: const KamarthaApp(),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Siapkan akun pertama'));
    await tester.pumpAndSettle();
    for (final (index, value) in [
      'kode-demo',
      'pengelola',
      'DemoPass2026!',
      'DemoPass2026!',
    ].indexed) {
      await tester.enterText(find.byType(TextFormField).at(index), value);
    }
    await tester.tap(find.widgetWithText(FilledButton, 'Buat akun pengelola'));
    await tester.pumpAndSettle();
    expect(auth.created, isTrue);
    await tester.enterText(find.byType(TextFormField).at(0), 'pengelola');
    await tester.enterText(find.byType(TextFormField).at(1), 'DemoPass2026!');
    await tester.tap(find.widgetWithText(FilledButton, 'Masuk'));
    await tester.pumpAndSettle();
    expect(find.text('Mode Persiapan'), findsOneWidget);
    expect(find.text('0 dari 0'), findsOneWidget);
    expect(find.text('Lengkapi data awal'), findsOneWidget);
    expect(business.writes, 0);
    await tester.tap(find.byTooltip('Sesi pengelola'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keluar'));
    await tester.pumpAndSettle();
    expect(auth.signedIn, isFalse);
    expect(find.widgetWithText(FilledButton, 'Masuk'), findsOneWidget);
    expect(find.text('Mode Persiapan'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Login validates required fields and offers first setup', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [authProvider.overrideWithValue(FakeAuth())],
        child: const KamarthaApp(),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Siapkan akun pertama'), findsOneWidget);
    expect(find.text('Kelola kos, lebih teratur.'), findsOneWidget);
    final submit = find.widgetWithText(FilledButton, 'Masuk');
    await tester.ensureVisible(submit);
    await tester.pumpAndSettle();
    await tester.tap(submit);
    await tester.pumpAndSettle();
    expect(find.text('Username wajib diisi.'), findsOneWidget);
    expect(find.text('Password wajib diisi.'), findsOneWidget);
  });

  test('Rupiah uses Indonesian thousands separators', () {
    expect(formatRupiah(500000), 'Rp500.000');
    expect(formatRupiah(1500000), 'Rp1.500.000');
    expect(formatRupiah(0), 'Rp0');
    expect(formatRupiah(-2500), '-Rp2.500');
    expect(formatRupiah(null), 'Rp—');
  });

  testWidgets('Successful reload clears the previous bootstrap error', (
    tester,
  ) async {
    final auth = FlakyAuth();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [authProvider.overrideWithValue(auth)],
        child: const KamarthaApp(),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Permintaan belum berhasil. Coba lagi.'), findsOneWidget);
    await tester.tap(find.text('Muat ulang'));
    await tester.pumpAndSettle();
    expect(find.text('Permintaan belum berhasil. Coba lagi.'), findsNothing);
    expect(find.text('Siapkan akun pertama'), findsOneWidget);
    expect(auth.attempts, 2);
  });
}
