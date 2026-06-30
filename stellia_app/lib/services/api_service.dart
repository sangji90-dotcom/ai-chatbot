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

  static Future<void> toggleLike(String characterId) async {
  final token = await getToken();
  await _dio.post(
    '/likes/$characterId',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  }

  static Future<List<dynamic>> getCommunityPosts({String? postType}) async {
  final token = await getToken();
  final params = <String, dynamic>{'limit': 20};
  if (postType != null) params['post_type'] = postType;
  final res = await _dio.get(
    '/community',
    queryParameters: params,
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> togglePostLike(int postId) async {
  final token = await getToken();
  final res = await _dio.post(
    '/community/$postId/like',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<List<dynamic>> getStories() async {
  final token = await getToken();
  final res = await _dio.get(
    '/party/stories',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<List<dynamic>> searchCharacters(String q) async {
  final token = await getToken();
  final res = await _dio.get(
    '/characters/search',
    queryParameters: {'q': q, 'size': 20},
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<List<dynamic>> getRanking({String sort = 'popular'}) async {
  final token = await getToken();
  final res = await _dio.get(
    '/characters/ranking',
    queryParameters: {'limit': 20, 'sort': sort},
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<List<dynamic>> getNotifications() async {
  final token = await getToken();
  final res = await _dio.get(
    '/notifications',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<List<dynamic>> getNotices() async {
  final res = await _dio.get('/notices');
  return res.data;
  }

  static Future<Map<String, dynamic>> attendance() async {
  final token = await getToken();
  final res = await _dio.post(
    '/tokens/attendance',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> getReferralCode() async {
  final token = await getToken();
  final res = await _dio.get(
    '/events/referral/my-code',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> getTokens() async {
  final token = await getToken();
  final res = await _dio.get(
    '/tokens/me',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> getTokenHistory() async {
  final token = await getToken();
  final res = await _dio.get(
    '/tokens/me/history',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> purchaseToken(int packageId) async {
  final token = await getToken();
  final res = await _dio.post(
    '/tokens/purchase/$packageId',
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> autoComplete({
  required String name,
  String description = '',
  String job = '',
  int age = 20,
}) async {
  final token = await getToken();
  final res = await _dio.post(
    '/characters/auto-complete',
    data: {'name': name, 'description': description, 'job': job, 'age': age},
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }

  static Future<Map<String, dynamic>> createCharacter({
  required String name,
  required String description,
  required int age,
  required String job,
  required String personality,
  required String likes,
  required String dislikes,
  required String speechStyle,
  required String firstMessage,
  required String situation,
  required String visibility,
  required int isAdult,
}) async {
  final token = await getToken();
  final res = await _dio.post(
    '/characters',
    data: {
      'name': name,
      'description': description,
      'age': age,
      'job': job,
      'personality': personality,
      'likes': likes,
      'dislikes': dislikes,
      'speech_style': speechStyle,
      'first_message': firstMessage,
      'situation': situation,
      'visibility': visibility,
      'is_adult': isAdult,
      'tags': [],
      'image_url': '',
      'party_enabled': 0,
    },
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return res.data;
  }
}