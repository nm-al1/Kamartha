import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api.dart';
import '../features/auth/repositories/auth_repository.dart';
import '../features/auth/views/auth_page.dart';
import '../features/initialization/views/initialization_page.dart';
import '../features/leases/views/leases_page.dart';
import '../features/rooms/views/master_page.dart';
import '../features/invoices/views/invoices_page.dart';
import '../features/expenses/views/expenses_page.dart';
import '../features/reports/views/reports_page.dart';
import '../features/dashboard/views/home_page.dart';
import 'theme/kamartha_theme.dart';
import '../features/menu/views/menu_page.dart';
import '../features/reminders/views/reminders_page.dart';

final authProvider = Provider<AuthRepository>((ref) {
  final api = createApi();
  ref.onDispose(() => api.close());
  return AuthRepository(api);
});

final routerProvider = Provider<GoRouter>(
  (ref) => GoRouter(
    initialLocation: '/login',
    redirect: (context, state) async {
      final path = state.uri.path;
      if (path == '/login' || path == '/setup') return null;
      try {
        final manager = await ref.read(authProvider).me();
        if (manager == null) return '/login';
        if (path == '/initialization' && manager['mode'] == 'ACTIVE') {
          return '/home';
        }
      } catch (_) {
        // Let the destination show its retry state if the API cannot be reached.
      }
      return null;
    },
    routes: [
      for (final action in ['login', 'setup', 'change-password'])
        GoRoute(
          path: '/$action',
          builder: (_, _) => AuthPage(key: ValueKey(action), action: action),
        ),
      GoRoute(
        path: '/session',
        builder: (_, _) => const AuthPage(action: 'session'),
      ),
      GoRoute(
        path: '/initialization',
        builder: (_, _) => const InitializationPage(),
      ),
      GoRoute(path: '/home', builder: (_, _) => const HomePage()),
      GoRoute(path: '/menu', builder: (_, _) => const MenuPage()),
      GoRoute(path: '/leases', builder: (_, _) => const LeasesPage()),
      GoRoute(
        path: '/leases/:id',
        builder: (_, state) => LeaseDetailPage(id: state.pathParameters['id']!),
      ),
      GoRoute(path: '/invoices', builder: (_, _) => const InvoicesPage()),
      GoRoute(
        path: '/invoices/:id',
        builder: (_, state) =>
            InvoiceDetailPage(id: state.pathParameters['id']!),
      ),
      GoRoute(path: '/expenses', builder: (_, _) => const ExpensesPage()),
      GoRoute(
        path: '/expenses/:id',
        builder: (_, state) =>
            ExpenseDetailPage(id: state.pathParameters['id']!),
      ),
      GoRoute(path: '/reports', builder: (_, _) => const ReportsPage()),
      GoRoute(path: '/reminders', builder: (_, _) => const RemindersPage()),
      GoRoute(
        path: '/rooms',
        builder: (_, state) => MasterPage(
          rooms: true,
          initialQuery: state.uri.queryParameters['q'] ?? '',
        ),
      ),
      GoRoute(
        path: '/rooms/:id',
        builder: (_, state) =>
            MasterPage(rooms: true, id: state.pathParameters['id']),
      ),
      GoRoute(
        path: '/residents',
        builder: (_, _) => const MasterPage(rooms: false),
      ),
      GoRoute(
        path: '/residents/:id',
        builder: (_, state) =>
            MasterPage(rooms: false, id: state.pathParameters['id']),
      ),
    ],
  ),
);

class KamarthaApp extends ConsumerWidget {
  const KamarthaApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
    title: 'Kamartha',
    debugShowCheckedModeBanner: false,
    theme: kamarthaTheme(),
    routerConfig: ref.watch(routerProvider),
  );
}
