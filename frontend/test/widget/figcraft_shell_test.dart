import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kamartha/app/theme/kamartha_theme.dart';
import 'package:kamartha/core/business_page.dart';
import 'package:kamartha/core/widgets/kamartha_floating_nav_bar.dart';

void main() {
  testWidgets('Navbar keeps white hover surface and visible keyboard focus', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          bottomNavigationBar: KamarthaFloatingNavBar(
            selectedIndex: 1,
            onSelected: (_) {},
          ),
        ),
      ),
    );
    final tabs = find.descendant(
      of: find.byType(KamarthaFloatingNavBar),
      matching: find.byType(InkWell),
    );
    expect(tabs, findsNWidgets(4));
    for (final tab in tester.widgetList<InkWell>(tabs)) {
      expect(tab.hoverColor, Colors.transparent);
      expect(tab.focusColor, KamarthaColors.chip);
    }
  });

  testWidgets('Capsule supports Tab Enter and reverse keyboard traversal', (
    tester,
  ) async {
    int? selected;
    await tester.pumpWidget(
      MaterialApp(
        theme: kamarthaTheme(),
        home: Scaffold(
          bottomNavigationBar: KamarthaFloatingNavBar(
            selectedIndex: 0,
            onSelected: (index) => selected = index,
          ),
        ),
      ),
    );
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.pumpAndSettle();
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pumpAndSettle();
    expect(selected, 0);
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.sendKeyEvent(LogicalKeyboardKey.space);
    await tester.pumpAndSettle();
    expect(selected, 1);
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.tab);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pumpAndSettle();
    expect(selected, 0);
    expect(tester.takeException(), isNull);
  });

  test('Windows web does not shrink minimum control dimensions', () {
    debugDefaultTargetPlatformOverride = TargetPlatform.windows;
    addTearDown(() => debugDefaultTargetPlatformOverride = null);
    expect(kamarthaTheme().visualDensity, VisualDensity.standard);
  });
  test('FigCraft tokens replace the old rust palette', () {
    final theme = kamarthaTheme();
    expect(theme.colorScheme.primary, const Color(0xFFFD3D18));
    expect(theme.scaffoldBackgroundColor, const Color(0xFFF3F6F9));
    expect(theme.textTheme.bodyLarge!.fontSize, 16);
    expect(theme.textTheme.bodyMedium!.fontSize, 16);
  });

  for (final width in [320.0, 360.0, 390.0, 430.0]) {
    for (final scale in [1.0, 2.0]) {
      testWidgets('Four-tab capsule fits width $width at scale $scale', (
        tester,
      ) async {
        await tester.binding.setSurfaceSize(Size(width, 568));
        addTearDown(() => tester.binding.setSurfaceSize(null));
        int? selected;
        await tester.pumpWidget(
          MaterialApp(
            theme: kamarthaTheme(),
            home: MediaQuery(
              data: MediaQueryData(
                size: Size(width, 568),
                textScaler: TextScaler.linear(scale),
              ),
              child: Scaffold(
                bottomNavigationBar: KamarthaFloatingNavBar(
                  selectedIndex: 0,
                  onSelected: (index) => selected = index,
                ),
              ),
            ),
          ),
        );
        expect(find.text('Beranda'), findsOneWidget);
        expect(find.text('Kamar'), findsOneWidget);
        expect(find.text('Tagihan'), findsOneWidget);
        expect(find.text('Menu'), findsOneWidget);
        expect(find.byType(NavigationBar), findsNothing);
        await tester.tap(find.text('Menu'));
        expect(selected, 3);
        expect(tester.takeException(), isNull);
      });
    }
  }

  testWidgets('Detail back returns to its actual previous screen', (
    tester,
  ) async {
    final router = GoRouter(
      initialLocation: '/rooms',
      routes: [
        GoRoute(
          path: '/rooms',
          builder: (context, _) => BusinessPage(
            title: 'Kamar',
            preparation: false,
            child: TextButton(
              onPressed: () => context.push('/rooms/one'),
              child: const Text('Detail uji'),
            ),
          ),
        ),
        GoRoute(
          path: '/rooms/one',
          builder: (_, _) => const BusinessPage(
            title: 'Detail kamar',
            preparation: false,
            child: Text('Isi detail'),
          ),
        ),
      ],
    );
    addTearDown(router.dispose);
    await tester.pumpWidget(
      MaterialApp.router(theme: kamarthaTheme(), routerConfig: router),
    );
    await tester.tap(find.text('Detail uji'));
    await tester.pumpAndSettle();
    expect(find.byType(KamarthaFloatingNavBar), findsNothing);
    await tester.tap(find.byTooltip('Kembali'));
    await tester.pumpAndSettle();
    expect(find.text('Detail uji'), findsOneWidget);
  });
}
