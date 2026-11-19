import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../app/app.dart';

final businessProvider = Provider<BusinessRepository>(
  (ref) => BusinessRepository(ref.watch(authProvider).api),
);

class BusinessRepository {
  BusinessRepository(this.api);
  final Dio api;

  Future<Map<String, dynamic>> get(
    String path, [
    Map<String, dynamic>? query,
  ]) async {
    final response = await api.get(path, queryParameters: query);
    return Map<String, dynamic>.from(response.data['data']);
  }

  Future<Map<String, dynamic>> write(
    String method,
    String path,
    Map<String, dynamic> data, {
    String? key,
  }) async {
    final csrf = await get('/auth/csrf');
    final response = await api.request(
      path,
      data: data,
      options: Options(
        method: method,
        headers: {'X-CSRF-Token': csrf['csrf_token'], 'Idempotency-Key': ?key},
      ),
    );
    return Map<String, dynamic>.from(response.data['data']);
  }

  Future<Map<String, dynamic>> upload(
    String path,
    String filename,
    List<int> bytes,
    String mimeType, {
    String? key,
  }) async {
    final csrf = await get('/auth/csrf');
    final response = await api.post(
      path,
      data: FormData.fromMap({
        'file': MultipartFile.fromBytes(
          bytes,
          filename: filename,
          contentType: DioMediaType.parse(mimeType),
        ),
      }),
      options: Options(
        headers: {'X-CSRF-Token': csrf['csrf_token'], 'Idempotency-Key': ?key},
      ),
    );
    return Map<String, dynamic>.from(response.data['data']);
  }

  Future<List<Map<String, dynamic>>> all(String path) async {
    final result = <Map<String, dynamic>>[];
    var offset = 0;
    while (true) {
      final data = await get(path, {'limit': 100, 'offset': offset});
      final items = (data['items'] as List)
          .map((e) => Map<String, dynamic>.from(e))
          .toList();
      result.addAll(items);
      if (data['pagination']['has_more'] != true) break;
      offset += items.length;
      if (items.isEmpty) break;
    }
    return result;
  }
}
