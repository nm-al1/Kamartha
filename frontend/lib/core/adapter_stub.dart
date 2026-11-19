import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

void configureAdapter(Dio dio) {
  final base = Uri.tryParse(dio.options.baseUrl);
  if (!kDebugMode ||
      base == null ||
      base.scheme != 'http' ||
      base.host != '127.0.0.1' ||
      base.port != 8001) {
    return;
  }

  // Keep the USB demo session in memory. The browser still owns web cookies.
  final cookies = <String, Cookie>{};
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (request, handler) {
        if (request.uri.origin == base.origin) {
          request.followRedirects = false;
          request.headers['Origin'] = base.origin;
          if (cookies.isNotEmpty) {
            request.headers['Cookie'] = cookies.values
                .map((cookie) => '${cookie.name}=${cookie.value}')
                .join('; ');
          }
        }
        handler.next(request);
      },
      onResponse: (response, handler) {
        if (response.requestOptions.uri.origin == base.origin) {
          for (final value
              in response.headers[HttpHeaders.setCookieHeader] ?? <String>[]) {
            final cookie = Cookie.fromSetCookieValue(value);
            if (cookie.name != 'kamartha_preauth' &&
                cookie.name != 'kamartha_session') {
              continue;
            }
            if (cookie.maxAge == 0 || cookie.value.isEmpty) {
              cookies.remove(cookie.name);
            } else if (!cookie.secure) {
              cookies[cookie.name] = cookie;
            }
          }
        }
        handler.next(response);
      },
    ),
  );
}
