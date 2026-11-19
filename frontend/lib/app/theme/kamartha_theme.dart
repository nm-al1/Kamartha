import 'package:flutter/material.dart';

abstract final class KamarthaColors {
  static const primary = Color(0xFFFD3D18);
  static const brand = Color(0xFFFA6921);
  static const link = Color(0xFFFE4300);
  static const ink = Color(0xFF142039);
  static const secondary = Color(0xFF526079);
  static const background = Color(0xFFF3F6F9);
  static const border = Color(0xFFDCE3EB);
  static const divider = Color(0xFFEEF2F6);
  static const success = Color(0xFF08964D);
  static const successBackground = Color(0xFFD5F5E5);
  static const warning = Color(0xFFFE6507);
  static const warningText = Color(0xFF9A3B00);
  static const warningBackground = Color(0xFFFFF3E0);
  static const danger = Color(0xFFE53935);
  static const dangerText = Color(0xFFB71C1C);
  static const dangerBackground = Color(0xFFFEE2E2);
  static const chip = Color(0xFFECF2F7);
  static const activeTab = Color(0xFF091C39);
  static const headerGradient = LinearGradient(
    colors: [Color(0xFFF85413), brand, Color(0xFFEF3A0E)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

EdgeInsets pagePadding(BuildContext context) =>
    EdgeInsets.all(MediaQuery.sizeOf(context).width < 390 ? 16 : 20);

ThemeData kamarthaTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: KamarthaColors.primary,
    primary: KamarthaColors.primary,
    onPrimary: Colors.white,
    surface: Colors.white,
    onSurface: KamarthaColors.ink,
    onSurfaceVariant: KamarthaColors.secondary,
    outline: KamarthaColors.border,
    error: KamarthaColors.danger,
  );
  return ThemeData(
    useMaterial3: true,
    visualDensity: VisualDensity.standard,
    fontFamily: 'Inter',
    colorScheme: scheme,
    scaffoldBackgroundColor: KamarthaColors.background,
    textTheme: const TextTheme(
      bodyLarge: TextStyle(
        fontSize: 16,
        height: 1.45,
        color: KamarthaColors.ink,
      ),
      bodyMedium: TextStyle(
        fontSize: 16,
        height: 1.45,
        color: KamarthaColors.ink,
      ),
      bodySmall: TextStyle(
        fontSize: 14,
        height: 1.4,
        color: KamarthaColors.secondary,
      ),
      titleSmall: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      titleMedium: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      titleLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
      headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
      displaySmall: TextStyle(fontSize: 30, fontWeight: FontWeight.w600),
      labelLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.white,
      foregroundColor: KamarthaColors.ink,
      surfaceTintColor: Colors.transparent,
      titleSpacing: 16,
      titleTextStyle: TextStyle(
        fontFamily: 'Inter',
        fontSize: 30,
        fontWeight: FontWeight.w600,
        color: KamarthaColors.ink,
      ),
      shape: Border(bottom: BorderSide(color: KamarthaColors.border)),
    ),
    inputDecorationTheme: const InputDecorationTheme(
      constraints: BoxConstraints(minHeight: 52),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(12)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(12)),
        borderSide: BorderSide(color: KamarthaColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.all(Radius.circular(12)),
        borderSide: BorderSide(color: KamarthaColors.ink, width: 2),
      ),
      filled: true,
      fillColor: Colors.white,
      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    ),
    cardTheme: const CardThemeData(
      color: Colors.white,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      margin: EdgeInsets.symmetric(vertical: 6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(16)),
        side: BorderSide(color: KamarthaColors.border),
      ),
    ),
    dividerTheme: const DividerThemeData(
      color: KamarthaColors.divider,
      thickness: 1,
      space: 1,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(48, 48),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: KamarthaColors.ink,
        side: const BorderSide(color: KamarthaColors.border),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: KamarthaColors.link,
        minimumSize: const Size(48, 48),
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(
        minimumSize: const Size(48, 48),
        foregroundColor: KamarthaColors.secondary,
      ),
    ),
  );
}
