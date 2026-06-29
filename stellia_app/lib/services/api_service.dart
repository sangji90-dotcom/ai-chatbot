import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'https://suburb-marrow-radial.ngrok-free.dev';
  static final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 30),
  ));

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    return res.data;
  }

  static Future<List<dynamic>> getCharacters({String? tag, int page = 1}) async {
    final token = await getToken();
    final res = await _dio.get(
      '/characters/ranking',
      queryParameters: {'limit': 20, 'offset': (page - 1) * 20},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<Map<String, dynamic>> sendMessage({
    required String characterId,
    required String message,
    required String sessionId,
  }) async {
    final token = await getToken();
    final res = await _dio.post(
      '/chat',
      data: {
        'character_id': characterId,
        'message': message,
        'session_id': sessionId,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<Map<String, dynamic>> getMe() async {
    final token = await getToken();
    final res = await _dio.get(
      '/users/me',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }
}