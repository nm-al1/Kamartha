import 'package:dio/dio.dart';
import 'package:dio/browser.dart';

void configureAdapter(Dio dio) {
  dio.httpClientAdapter = BrowserHttpClientAdapter(withCredentials: true);
}
