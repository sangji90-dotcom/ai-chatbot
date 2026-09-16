import 'package:dio/dio.dart';
import 'dart:io';

import 'token_storage.dart';

class ApiService {
  /// 빌드 시 주입한다:
  ///   flutter build apk --dart-define=API_BASE_URL=https://api.stellia.example
  /// (ngrok 주소 하드코딩은 주소가 바뀔 때마다 앱을 다시 배포해야 했다)
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static final Dio _dio = _buildDio();

  static Dio _buildDio() {
    final dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 60),
      ),
    );

    // 401 이면 refresh 토큰으로 1회 갱신 후 재시도한다
    dio.interceptors.add(
      InterceptorsWrapper(
        onError: (DioException e, handler) async {
          final isAuthCall =
              e.requestOptions.path.startsWith('/auth/');
          if (e.response?.statusCode != 401 ||
              isAuthCall ||
              e.requestOptions.extra['retried'] == true) {
            return handler.next(e);
          }

          final refreshed = await _refresh();
          if (!refreshed) return handler.next(e);

          final token = await TokenStorage.getAccessToken();
          final opts = e.requestOptions;
          opts.extra['retried'] = true;
          opts.headers['Authorization'] = 'Bearer $token';
          try {
            final res = await dio.fetch(opts);
            return handler.resolve(res);
          } catch (_) {
            return handler.next(e);
          }
        },
      ),
    );
    return dio;
  }

  static Future<bool> _refresh() async {
    final refresh = await TokenStorage.getRefreshToken();
    if (refresh == null) return false;
    try {
      final res = await Dio(BaseOptions(baseUrl: baseUrl)).post(
        '/auth/refresh',
        data: {'refresh_token': refresh},
      );
      await TokenStorage.save(
        access: res.data['access_token'],
        refresh: res.data['refresh_token'],
      );
      return true;
    } catch (_) {
      await TokenStorage.clear();
      return false;
    }
  }

  static Future<String?> getToken() => TokenStorage.getAccessToken();

  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final res = await _dio.post(
      '/auth/login',
      data:
          'username=${Uri.encodeComponent(email)}&password=${Uri.encodeComponent(password)}',
      options: Options(contentType: 'application/x-www-form-urlencoded'),
    );
    return res.data;
  }

  static Future<List<dynamic>> getCharacters({
    String? tag,
    int page = 1,
  }) async {
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

  /// 메시지 평가. reason 은 dislike 일 때만 의미가 있다.
  /// 사유가 없으면 '기억을 못한다' 인지 '말투가 이상하다' 인지 구분할 수 없어
  /// 기억 품질을 측정할 수 없다.
  static Future<void> rateMessage({
    required String sessionId,
    required int messageId,
    required String rating,
    String reason = '',
  }) async {
    final token = await getToken();
    await _dio.post(
      '/chat/rating',
      data: {
        'session_id': sessionId,
        'message_id': messageId,
        'rating': rating,
        'reason': reason,
      },
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
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

  /// PG 연동 전까지 서버의 토큰 지급 엔드포인트는 관리자 전용이다.
  /// (누구나 호출해 무한 충전할 수 있던 경로를 닫았다)
  /// PG 를 붙이면 여기서 결제 SDK -> 서버 webhook 검증 순으로 바꾼다.
  static bool get purchaseEnabled => false;

  static Future<Map<String, dynamic>> purchaseToken(int packageId) async {
    throw UnsupportedError('결제 기능 준비 중');
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

  static Future<void> uploadCharacterImage(
    String characterId,
    File image,
  ) async {
    final token = await getToken();
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(image.path),
    });
    await _dio.post(
      '/characters/$characterId/image',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
  }

  static Future<Map<String, dynamic>> createPost({
    required String content,
    String title = '',
    String postType = 'general',
  }) async {
    final token = await getToken();
    final formData = FormData.fromMap({
      'content': content,
      'post_type': postType,
      if (title.isNotEmpty) 'title': title,
    });
    final res = await _dio.post(
      '/community',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<Map<String, dynamic>> getPostDetail(int postId) async {
    final token = await getToken();
    final res = await _dio.get(
      '/community/$postId',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<void> createComment(int postId, String content) async {
    final token = await getToken();
    await _dio.post(
      '/community/$postId/comments',
      data: {'content': content},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
  }

  static Future<List<dynamic>> getMyCharacters() async {
    final token = await getToken();
    final res = await _dio.get(
      '/characters/me',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<List<dynamic>> getLikedCharacters() async {
    final token = await getToken();
    final res = await _dio.get(
      '/likes/me',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<List<dynamic>> getBookmarks() async {
    final token = await getToken();
    final res = await _dio.get(
      '/likes/bookmarks',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<List<dynamic>> getAchievements() async {
    final token = await getToken();
    final res = await _dio.get(
      '/achievements/me',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<void> updateSettings(Map<String, dynamic> data) async {
    final token = await getToken();
    await _dio.patch(
      '/users/me/settings',
      data: data,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
  }

  static Future<void> updateProfile(String username) async {
    final token = await getToken();
    await _dio.patch(
      '/users/me',
      data: {'username': username},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
  }

  static Future<Map<String, dynamic>> getRoomInfo(String code) async {
    final token = await getToken();
    final res = await _dio.get(
      '/party/rooms/$code',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<void> leaveRoom(String code) async {
    final token = await getToken();
    await _dio.delete(
      '/party/rooms/$code/leave',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
  }

  static Future<Map<String, dynamic>> createRoom(
    int storyId,
    int maxMembers,
  ) async {
    final token = await getToken();
    final res = await _dio.post(
      '/party/rooms',
      data: {'story_id': storyId, 'max_members': maxMembers},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<Map<String, dynamic>> joinRoom(String code) async {
    final token = await getToken();
    final res = await _dio.post(
      '/party/rooms/join',
      data: {'code': code, 'character_stats': {}},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<List<dynamic>> getChatSessions(String characterId) async {
    final token = await getToken();
    final res = await _dio.get(
      '/chat/sessions/$characterId',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }

  static Future<List<dynamic>> getChatHistory(
    String characterId,
    String sessionId,
  ) async {
    final token = await getToken();
    final res = await _dio.get(
      '/chat/history/$characterId',
      queryParameters: {'session_id': sessionId},
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return res.data;
  }
}
