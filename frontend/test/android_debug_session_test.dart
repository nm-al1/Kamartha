import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kamartha/core/adapter_stub.dart';

void main() {
  test(
    'USB debug sends and clears app cookies on the loopback API only',
    () async {
      final dio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:8001/api/v1'));
      final adapter = _DebugApi();
      dio.httpClientAdapter = adapter;
      configureAdapter(dio);

      await dio.get('/auth/csrf');
      await dio.post('/auth/login');
      await dio.get('https://example.invalid');
      await dio.post('/auth/logout');
      await dio.get('/auth/me');

      expect(adapter.requests.map((request) => request.headers['Cookie']), [
        null,
        'kamartha_preauth=preauth',
        null,
        'kamartha_session=session',
        null,
      ]);
      expect(adapter.requests[1].headers['Origin'], 'http://127.0.0.1:8001');
      expect(adapter.requests[1].followRedirects, isFalse);
      expect(adapter.requests[2].headers['Origin'], isNull);
    },
  );
}

class _DebugApi implements HttpClientAdapter {
  final requests = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final cookies = switch (options.path) {
      '/auth/csrf' => [
        'kamartha_preauth=preauth; HttpOnly; Path=/; SameSite=lax',
      ],
      '/auth/login' => [
        'kamartha_session=session; HttpOnly; Path=/; SameSite=lax',
        'kamartha_preauth=""; Max-Age=0; Path=/',
      ],
      '/auth/logout' => ['kamartha_session=""; Max-Age=0; Path=/'],
      'https://example.invalid' => ['kamartha_session=foreign; Path=/'],
      _ => <String>[],
    };
    return ResponseBody.fromString('', 200, headers: {'set-cookie': cookies});
  }

  @override
  void close({bool force = false}) {}
}
