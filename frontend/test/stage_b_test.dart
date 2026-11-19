import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/rooms/views/master_page.dart';
import 'package:kamartha/features/initialization/views/opening_record_form.dart';

void main() {
  testWidgets('Incomplete opening form saves a draft without invented values', (
    tester,
  ) async {
    Map<String, dynamic>? saved;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: OpeningRecordForm(
            rooms: const [],
            residents: const [],
            packages: const [],
            onSave: (data) async {
              saved = data;
            },
          ),
        ),
      ),
    );
    await tester.scrollUntilVisible(
      find.text('Simpan draft'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.ensureVisible(
      find.widgetWithText(FilledButton, 'Simpan draft'),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Simpan draft'));
    await tester.pumpAndSettle();
    expect(saved, isNotNull);
    expect(saved!['room_id'], isNull);
    expect(saved!['price'], isNull);
  });

  for (final width in [360.0, 390.0, 430.0, 1280.0]) {
    testWidgets('Master room form creates data at width $width', (
      tester,
    ) async {
      await tester.binding.setSurfaceSize(Size(width, 900));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final repository = FakeBusiness();
      await tester.pumpWidget(
        ProviderScope(
          overrides: [businessProvider.overrideWithValue(repository)],
          child: const MaterialApp(home: MasterPage(rooms: true)),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Belum ada data yang cocok.'), findsOneWidget);
      await tester.tap(find.text('+ Tambah'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const ValueKey('room-number')), 'A1');
      expect(
        tester
            .widget<TextFormField>(find.byKey(const ValueKey('room-room_type')))
            .controller!
            .text,
        'Standar',
      );
      await tester.enterText(
        find.byKey(const ValueKey('room-reference_price')),
        '500000',
      );
      await tester.ensureVisible(find.text('Simpan kamar'));
      await tester.tap(find.text('Simpan kamar'));
      await tester.pumpAndSettle();
      expect(repository.saved?['number'], 'A1');
      expect(repository.saved?['room_type'], 'Standar');
      expect(repository.saved?['supported_occupants'], 2);
      expect(repository.saved?['reference_price'], 500000);
      expect(repository.key, isNotEmpty);
      expect(tester.takeException(), isNull);
    });
  }
}

class FakeBusiness extends BusinessRepository {
  FakeBusiness() : super(Dio());
  Map<String, dynamic>? saved;
  String? key;
  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async => path == '/initialization/settings'
      ? {'mode': 'PREPARATION'}
      : {
          'items': <Map<String, dynamic>>[],
          'pagination': {'has_more': false},
        };
  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    saved = data;
    this.key = key;
    return {'id': 'test', ...data};
  }
}
