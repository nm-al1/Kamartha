import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/app.dart';
import '../../../core/api.dart';
import '../../../app/theme/kamartha_theme.dart';

class AuthPage extends ConsumerStatefulWidget {
  const AuthPage({super.key, required this.action});
  final String action;
  @override
  ConsumerState<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends ConsumerState<AuthPage> {
  final _form = GlobalKey<FormState>();
  final _username = TextEditingController();
  final _password = TextEditingController();
  final _confirmation = TextEditingController();
  final _code = TextEditingController();
  final _old = TextEditingController();
  bool _busy = true, _visible = false, _setup = false;
  String? _error;
  Map<String, dynamic>? _manager;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final repository = ref.read(authProvider);
      final manager = await repository.me();
      final csrf = await repository.csrf();
      if (!mounted) return;
      if (manager != null &&
          (widget.action == 'login' || widget.action == 'setup')) {
        context.go('/home');
        return;
      }
      if (manager == null &&
          (widget.action == 'session' || widget.action == 'change-password')) {
        context.go('/login');
        return;
      }
      setState(() {
        _manager = manager;
        _setup = csrf['setup_available'] == true;
        _error = null;
        _busy = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = apiError(error);
          _busy = false;
        });
      }
    }
  }

  @override
  void dispose() {
    for (final field in [_username, _password, _confirmation, _code, _old]) {
      field.dispose();
    }
    super.dispose();
  }

  Future<void> _submit([String? override]) async {
    final action = override ?? widget.action;
    if (action != 'logout' && !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final values = <String, dynamic>{
        if (action == 'login' || action == 'setup') 'username': _username.text,
        if (action != 'logout') 'password': _password.text,
        if (action == 'setup' || action == 'change-password')
          'password_confirmation': _confirmation.text,
        if (action == 'setup') 'setup_code': _code.text,
        if (action == 'change-password') 'old_password': _old.text,
      };
      await ref.read(authProvider).submit(action, values);
      if (!mounted) return;
      _password.clear();
      _confirmation.clear();
      _code.clear();
      _old.clear();
      if (action == 'change-password') {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Password diubah. Silakan masuk ulang.'),
          ),
        );
      }
      context.go(action == 'login' ? '/home' : '/login');
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = apiError(error);
          _busy = false;
        });
      }
    }
  }

  Widget _field(
    String label,
    TextEditingController controller, {
    bool secret = false,
    bool strong = false,
  }) => Builder(
    builder: (fieldContext) => Focus(
      canRequestFocus: false,
      onFocusChange: (focused) {
        if (focused) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (fieldContext.mounted) {
              Scrollable.ensureVisible(
                fieldContext,
                duration: const Duration(milliseconds: 180),
                alignmentPolicy: ScrollPositionAlignmentPolicy.keepVisibleAtEnd,
              );
            }
          });
        }
      },
      child: Padding(
      padding: EdgeInsets.only(bottom: widget.action == 'login' ? 24 : 16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (widget.action == 'login') ...[
          Text(label, style: const TextStyle(fontSize: 14, height: 1.2, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
        ],
        TextFormField(
          controller: controller,
          obscureText: secret && !_visible,
          enabled: !_busy,
          autocorrect: !secret,
          enableSuggestions: !secret,
          decoration: InputDecoration(
          labelText: widget.action == 'login' ? null : label,
          hintText: widget.action == 'login' ? secret ? 'Masukkan password' : 'Masukkan username' : null,
          fillColor: widget.action == 'login' ? const Color(0xFFF5F7FA) : Colors.white,
          border: widget.action == 'login' ? const OutlineInputBorder(borderSide: BorderSide.none,
            borderRadius: BorderRadius.all(Radius.circular(12))) : null,
          enabledBorder: widget.action == 'login' ? const OutlineInputBorder(borderSide: BorderSide.none,
            borderRadius: BorderRadius.all(Radius.circular(12))) : null,
          isDense: widget.action == 'login',
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          prefixIcon: widget.action == 'login' ? Icon(secret ? Icons.lock_outline : Icons.person_outline,
            color: KamarthaColors.secondary, size: 24) : null,
            suffixIcon: secret
                ? IconButton(
                    tooltip: _visible
                        ? 'Sembunyikan password'
                        : 'Tampilkan password',
                    onPressed: () => setState(() => _visible = !_visible),
                    icon: Icon(
                      _visible ? Icons.visibility_off : Icons.visibility,
                    ),
                  )
                : null,
          ),
          validator: (value) {
            final text = value ?? '';
            if (text.isEmpty) return '$label wajib diisi.';
            if (controller == _username &&
                !RegExp(r'^[A-Za-z0-9._]{4,32}$').hasMatch(text)) {
              return 'Gunakan 4–32 huruf, angka, titik atau garis bawah.';
            }
            if (strong && (text.length < 8 || text.length > 128)) {
              return 'Gunakan 8–128 karakter.';
            }
            if (secret && text.length > 128) return 'Maksimal 128 karakter.';
            if (controller == _confirmation && text != _password.text) {
              return 'Konfirmasi password tidak cocok.';
            }
            return null;
          },
        ),
      ]),
      ),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final action = widget.action;
    if (action == 'login') return _loginPage();
    final title = switch (action) {
      'setup' => 'Buat akun pengelola',
      'change-password' => 'Ganti password',
      'session' => 'Sesi pengelola',
      _ => 'Masuk',
    };
    return Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: action == 'login'
          ? null
          : AppBar(
              title: const Text('KAMARTHA'),
              backgroundColor: KamarthaColors.brand,
              foregroundColor: Colors.white,
            ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: action == 'login' ? EdgeInsets.zero : pagePadding(context),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (action == 'login')
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 40,
                      ),
                      decoration: const BoxDecoration(
                        gradient: KamarthaColors.headerGradient,
                      ),
                      child: const Column(
                        children: [
                          Icon(
                            Icons.home_rounded,
                            size: 48,
                            color: Colors.white,
                          ),
                          SizedBox(height: 16),
                          Text(
                            'kamartha',
                            style: TextStyle(
                              fontSize: 30,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                          SizedBox(height: 12),
                          Text(
                            'Kelola kos, lebih teratur.',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 16, color: Colors.white),
                          ),
                        ],
                      ),
                    ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(28),
                    ),
                    child: Form(
                      key: _form,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const SizedBox(height: 24),
                          Text(
                            title,
                            style: Theme.of(context).textTheme.headlineMedium,
                          ),
                          if (action == 'login') ...[
                            const SizedBox(height: 8),
                            Text(
                              'Gunakan akun pengelola kos.',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                          const SizedBox(height: 24),
                          if (_busy) const LinearProgressIndicator(),
                          if (_error != null) ...[
                            Text(
                              _error!,
                              style: const TextStyle(color: Color(0xFFB42318)),
                            ),
                            TextButton(
                              onPressed: _busy ? null : _bootstrap,
                              child: const Text('Muat ulang'),
                            ),
                            const SizedBox(height: 16),
                          ],
                          if (action == 'session') ...[
                            Text('Pengelola: ${_manager?['username'] ?? '—'}'),
                            Text('Mode: ${_manager?['mode'] ?? '—'}'),
                            const SizedBox(height: 16),
                            TextButton(
                              onPressed: _busy
                                  ? null
                                  : () => context.go('/home'),
                              child: const Text('Buka aplikasi'),
                            ),
                            const SizedBox(height: 24),
                            FilledButton(
                              onPressed: _busy
                                  ? null
                                  : () => context.go('/change-password'),
                              child: const Text('Ganti password'),
                            ),
                            TextButton(
                              onPressed: _busy ? null : () => _submit('logout'),
                              child: const Text('Keluar'),
                            ),
                          ] else ...[
                            if (action == 'setup' && !_setup && !_busy)
                              const Text(
                                'Registrasi sudah ditutup atau belum tersedia. Silakan masuk.',
                              ),
                            if (action == 'setup')
                              _field('Kode penyiapan', _code, secret: true),
                            if (action != 'change-password')
                              _field('Username', _username),
                            if (action == 'change-password')
                              _field('Password lama', _old, secret: true),
                            _field(
                              action == 'login' ? 'Password' : 'Password baru',
                              _password,
                              secret: true,
                              strong: action != 'login',
                            ),
                            if (action != 'login')
                              _field(
                                'Konfirmasi password',
                                _confirmation,
                                secret: true,
                                strong: true,
                              ),
                            FilledButton(
                              onPressed: _busy || (action == 'setup' && !_setup)
                                  ? null
                                  : _submit,
                              child: Text(title),
                            ),
                            if (action == 'login')
                              TextButton(
                                onPressed: () => showDialog<void>(
                                  context: context,
                                  builder: (context) => AlertDialog(
                                    title: const Text('Pemulihan akun'),
                                    content: const Text(
                                      'Hubungi tim pemeliharaan untuk verifikasi pemilik dan pemulihan akun. Tidak tersedia reset email atau OTP otomatis.',
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () => Navigator.pop(context),
                                        child: const Text('Tutup'),
                                      ),
                                    ],
                                  ),
                                ),
                                child: const Text('Lupa password?'),
                              ),
                            if (action == 'login')
                              TextButton(
                                onPressed: _busy
                                    ? null
                                    : () => context.go('/setup'),
                                child: Text(
                                  _setup
                                      ? 'Siapkan akun pertama'
                                      : 'Lihat registrasi awal',
                                ),
                              ),
                            if (action != 'login')
                              TextButton(
                                onPressed: _busy
                                    ? null
                                    : () => context.go(
                                        action == 'setup'
                                            ? '/login'
                                            : '/session',
                                      ),
                                child: const Text('Kembali'),
                              ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _loginPage() => Scaffold(
    resizeToAvoidBottomInset: true,
    body: SafeArea(child: SingleChildScrollView(child: Center(child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 480),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        ClipRect(child: Stack(fit: StackFit.passthrough, children: [
          const Positioned.fill(child: DecoratedBox(decoration: BoxDecoration(gradient: KamarthaColors.headerGradient))),
          Positioned(top: -110, right: -84, child: Container(width: 260, height: 260,
            decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withValues(alpha: .06)))),
          Padding(padding: const EdgeInsets.fromLTRB(32, 72, 32, 71),
            child: Column(children: [
              Container(key: const ValueKey('login-brand-mark'), width: 56, height: 56,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
                child: const CustomPaint(size: Size(28, 32), painter: _LoginMarkPainter())),
              const SizedBox(height: 16),
              const Text('kamartha', textAlign: TextAlign.center,
                style: TextStyle(fontSize: 30, height: 1.2, fontWeight: FontWeight.w600, color: Colors.white)),
              const SizedBox(height: 16),
              const Text('Kelola kos, lebih teratur.', textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, height: 1.2, color: Colors.white)),
            ]),
          ),
        ])),
        Stack(children: [
          const Positioned(left: 0, right: 0, top: 0, height: 34,
            child: DecoratedBox(decoration: BoxDecoration(gradient: KamarthaColors.headerGradient))),
          Padding(padding: EdgeInsets.symmetric(horizontal: pagePadding(context).left),
            child: Container(key: const ValueKey('login-form-panel'),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(28)),
              child: Form(key: _form, child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                const Text('Masuk', style: TextStyle(fontSize: 30, height: 1.2, fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),
                const Text('Gunakan akun pengelola kos.', style: TextStyle(fontSize: 14, height: 1.2, color: KamarthaColors.secondary)),
                const SizedBox(height: 24),
                if (_busy) const LinearProgressIndicator(),
                if (_error != null) ...[
                  Text(_error!, style: const TextStyle(color: Color(0xFFB42318))),
                  TextButton(onPressed: _busy ? null : _bootstrap, child: const Text('Muat ulang')),
                  const SizedBox(height: 16),
                ],
                _field('Username', _username),
                _field('Password', _password, secret: true),
                Align(alignment: Alignment.centerLeft, child: TextButton(
                  style: TextButton.styleFrom(padding: EdgeInsets.zero, alignment: Alignment.topLeft,
                    textStyle: const TextStyle(fontFamily: 'Inter', fontSize: 14, height: 1.2, fontWeight: FontWeight.w600)),
                  onPressed: () => showDialog<void>(context: context, builder: (context) => AlertDialog(
                    title: const Text('Pemulihan akun'),
                    content: const Text('Hubungi tim pemeliharaan untuk verifikasi pemilik dan pemulihan akun. Tidak tersedia reset email atau OTP otomatis.'),
                    actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Tutup'))],
                  )), child: const Text('Lupa password?'),
                )),
                FilledButton(onPressed: _busy ? null : _submit, child: const Text('Masuk')),
                const SizedBox(height: 24),
                const Text('Pendaftaran ditutup setelah akun pengelola dibuat.', textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 14, height: 1.2, color: KamarthaColors.secondary)),
                if (_setup) TextButton(onPressed: _busy ? null : () => context.go('/setup'),
                  child: const Text('Siapkan akun pertama')),
                const SizedBox(height: 24),
                const Text('Kamartha · Pengelola kos', textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 14, height: 1.2, color: KamarthaColors.secondary)),
              ])),
            ),
          ),
        ]),
        const SizedBox(height: 24),
      ]),
    )))),
  );
}

class _LoginMarkPainter extends CustomPainter {
  const _LoginMarkPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()..moveTo(14, 0)..lineTo(28, 14)..lineTo(28, 32)
      ..lineTo(0, 32)..lineTo(0, 14)..close();
    canvas.drawPath(path, Paint()..color = KamarthaColors.primary);
  }
  @override
  bool shouldRepaint(_LoginMarkPainter oldDelegate) => false;
}
