import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/core/business_repository.dart';
import 'package:kamartha/features/reminders/views/reminders_page.dart';

void main() {
  testWidgets(
    'A failed poll clears the QR and a ready session uses today by default',
    (tester) async {
      final repo = ReminderFixture();
      await tester.pumpWidget(
        ProviderScope(
          overrides: [businessProvider.overrideWithValue(repo)],
          child: const MaterialApp(home: RemindersPage()),
        ),
      );
      await tester.pumpAndSettle();
      expect(
        find.bySemanticsLabel('QR untuk menautkan nomor WhatsApp pengirim uji'),
        findsOneWidget,
      );
      expect(find.byType(TextField), findsNothing);

      repo.fail = true;
      await tester.pump(const Duration(seconds: 10));
      await tester.pumpAndSettle();
      expect(find.byType(Image), findsNothing);
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNull,
      );

      repo
        ..fail = false
        ..ready = true;
      await tester.pump(const Duration(seconds: 10));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Jalankan pengingat hari ini'));
      await tester.pumpAndSettle();
      expect(repo.payload, isEmpty);
      final uncertain = find.text('Belum pasti, perlu pemeriksaan');
      await tester.scrollUntilVisible(
        uncertain,
        180,
        scrollable: find.ancestor(
          of: find.byType(FilledButton),
          matching: find.byType(Scrollable),
        ),
      );
      expect(uncertain, findsOneWidget);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}

class ReminderFixture extends BusinessRepository {
  ReminderFixture() : super(Dio());

  bool fail = false, ready = false;
  Map<String, dynamic>? payload;

  @override
  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async {
    if (fail) throw StateError('Synthetic poll failure');
    if (path == '/reminders/history') {
      return {
        'items': [
          if (payload != null)
            {
              'status': 'UNKNOWN',
              'stage': 'H3',
              'room_number': 'UJI',
              'amount': 700000,
              'recipient_mask': '***0000',
              'due_on': '2026-11-21',
              'reminder_date': '2026-11-18',
            },
        ],
      };
    }
    return {
      'enabled': true,
      'ready': ready,
      'allow_demo_date': false,
      'hour_wita': 9,
      'today': '2026-11-18',
      'qr': ready
          ? null
          : 'data:image/png;base64,'
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
    };
  }

  @override
  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    payload = data;
    return {'sent': 0, 'unknown': 1, 'skipped': 0, 'existing': 0};
  }
}
