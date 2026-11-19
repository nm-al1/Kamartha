import 'package:dio/dio.dart';

class AuthRepository {
  AuthRepository(this.api);
  final Dio api;
  String? _csrf;

  Future<Map<String, dynamic>> csrf() async {
    final response = await api.get('/auth/csrf');
    final data = Map<String, dynamic>.from(response.data['data']);
    _csrf = data['csrf_token'] as String;
    return data;
  }

  Future<Map<String, dynamic>?> me() async {
    try {
      final response = await api.get('/auth/me');
      return Map<String, dynamic>.from(response.data['data']);
    } on DioException catch (error) {
      if (error.response?.statusCode == 401) return null;
      rethrow;
    }
  }

  Future<void> submit(String action, Map<String, dynamic> values) async {
    await csrf();
    final response = await api.post(
      '/auth/$action',
      data: values,
      options: Options(headers: {'X-CSRF-Token': _csrf}),
    );
    if (action == 'login') _csrf = response.data['data']['csrf_token'];
    if (action == 'logout' || action == 'change-password') _csrf = null;
  }
}
