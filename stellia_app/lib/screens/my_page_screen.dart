import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import 'login_screen.dart';
import 'notice_screen.dart';
import 'events_screen.dart';
import 'token_screen.dart';
import 'ranking_screen.dart';
import 'create_character_screen.dart';
import 'my_characters_screen.dart';
import 'liked_characters_screen.dart';
import 'bookmarks_screen.dart';
import 'achievements_screen.dart';
import 'settings_screen.dart';

class MyPageScreen extends StatefulWidget {
  const MyPageScreen({super.key});

  @override
  State<MyPageScreen> createState() => _MyPageScreenState();
}

class _MyPageScreenState extends State<MyPageScreen> {
  Map<String, dynamic>? _user;
  List<dynamic> _myCharacters = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final user = await ApiService.getMe();
      final chars = await ApiService.getCharacters();
      setState(() {
        _user = user;
        _myCharacters = chars;
      });
    } catch (e) {
      debugPrint('데이터 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    if (mounted) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (_) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text(
          '마이페이지',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF7C6CFF)),
            )
          : RefreshIndicator(
              color: const Color(0xFF7C6CFF),
              backgroundColor: const Color(0xFF0F0F18),
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  // 프로필 카드
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F0F18),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFF1F1F2E)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 64,
                          height: 64,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                            ),
                            borderRadius: BorderRadius.circular(32),
                          ),
                          child: Center(
                            child: Text(
                              (_user?['username'] ?? '?')[0].toUpperCase(),
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _user?['username'] ?? '',
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _user?['email'] ?? '',
                                style: const TextStyle(
                                  color: Color(0xFF6B7280),
                                  fontSize: 13,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  const Text(
                                    '✦ ',
                                    style: TextStyle(color: Color(0xFFFFD700)),
                                  ),
                                  Text(
                                    '${((_user?['token_balance'] ?? 0) as int).toLocaleString()} 럭키코인',
                                    style: const TextStyle(
                                      color: Color(0xFFFFD700),
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // 메뉴
                  _MenuItem(
                    icon: Icons.star_rounded,
                    label: '내 캐릭터',
                    subtitle: '${_myCharacters.length}개',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const MyCharactersScreen(),
                      ),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.favorite_rounded,
                    label: '좋아요한 캐릭터',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const LikedCharactersScreen(),
                      ),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.bookmark_rounded,
                    label: '북마크',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const BookmarksScreen(),
                      ),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.emoji_events_rounded,
                    label: '업적',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const AchievementsScreen(),
                      ),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.history_rounded,
                    label: '토큰 내역',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const TokenScreen()),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.campaign_rounded,
                    label: '공지사항',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const NoticeScreen()),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.celebration_rounded,
                    label: '이벤트',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const EventsScreen()),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.emoji_events_rounded,
                    label: '랭킹',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const RankingScreen()),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.add_rounded,
                    label: '캐릭터 만들기',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const CreateCharacterScreen(),
                      ),
                    ),
                  ),
                  _MenuItem(
                    icon: Icons.settings_rounded,
                    label: '설정',
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SettingsScreen()),
                    ),
                  ),

                  const SizedBox(height: 12),

                  // 로그아웃
                  GestureDetector(
                    onTap: _logout,
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F0F18),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFF1F1F2E)),
                      ),
                      child: const Row(
                        children: [
                          Icon(
                            Icons.logout_rounded,
                            color: Color(0xFFFF6B8A),
                            size: 20,
                          ),
                          SizedBox(width: 12),
                          Text(
                            '로그아웃',
                            style: TextStyle(
                              color: Color(0xFFFF6B8A),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

class _MenuItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? subtitle;
  final VoidCallback onTap;

  const _MenuItem({
    required this.icon,
    required this.label,
    this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF0F0F18),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF1F1F2E)),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF7C6CFF), size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            if (subtitle != null)
              Text(
                subtitle!,
                style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13),
              ),
            const SizedBox(width: 8),
            const Icon(
              Icons.chevron_right_rounded,
              color: Color(0xFF6B7280),
              size: 18,
            ),
          ],
        ),
      ),
    );
  }
}

extension on int {
  String toLocaleString() {
    return toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (m) => '${m[1]},',
    );
  }
}
