import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 토큰 저장소.
///
/// 기존에는 access/refresh 토큰을 SharedPreferences 에 평문으로 저장했다.
/// (Android 는 앱 전용 디렉터리의 XML, 루팅/백업 추출로 노출 가능)
/// flutter_secure_storage 는 Android Keystore / iOS Keychain 을 사용한다.
/// 기존 설치 유저를 위해 SharedPreferences 에 남은 값은 1회 마이그레이션한다.
class TokenStorage {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  static Future<String?> getAccessToken() async {
    final value = await _storage.read(key: _accessKey);
    if (value != null) return value;
    return _migrateFromPrefs(_accessKey);
  }

  static Future<String?> getRefreshToken() async {
    final value = await _storage.read(key: _refreshKey);
    if (value != null) return value;
    return _migrateFromPrefs(_refreshKey);
  }

  static Future<void> save({required String access, String? refresh}) async {
    await _storage.write(key: _accessKey, value: access);
    if (refresh != null) {
      await _storage.write(key: _refreshKey, value: refresh);
    }
  }

  static Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessKey);
    await prefs.remove(_refreshKey);
  }

  static Future<String?> _migrateFromPrefs(String key) async {
    final prefs = await SharedPreferences.getInstance();
    final legacy = prefs.getString(key);
    if (legacy == null) return null;
    await _storage.write(key: key, value: legacy);
    await prefs.remove(key); // 평문 사본은 남기지 않는다
    return legacy;
  }
}
