import 'package:dio/dio.dart';

import 'adapter_stub.dart' if (dart.library.js_interop) 'adapter_web.dart';

Dio createApi() {
  final dio = Dio(
    BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_URL',
        defaultValue: 'http://localhost:8000/api/v1',
      ),
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
    ),
  );
  configureAdapter(dio);
  return dio;
}

String apiError(Object error) {
  if (error is DioException) {
    final body = error.response?.data;
    if (body is Map && body['error'] is Map) {
      final detail = body['error'] as Map;
      return '${detail['message']} (ID: ${body['request_id']})';
    }
    return 'Layanan tidak dapat dihubungi. Periksa koneksi lalu coba lagi.';
  }
  return 'Permintaan belum berhasil. Coba lagi.';
}

Map<String, String> apiFieldErrors(Object error) {
  if (error is! DioException) return const {};
  final body = error.response?.data;
  if (body is! Map || body['error'] is! Map) return const {};
  final fields = (body['error'] as Map)['fields'];
  if (fields is! List) return const {};
  final result = <String, String>{};
  for (final item in fields) {
    if (item is Map && item['field'] is String) {
      final parts = (item['field'] as String).split('.');
      result[parts.last] = 'Isian tidak sesuai.';
    }
  }
  return result;
}
