import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../models/character.dart';
import 'login_screen.dart';
import 'character_profile_screen.dart';
import 'community_screen.dart';
import 'party_lobby_screen.dart';
import 'my_page_screen.dart';
import 'search_screen.dart';
import 'notification_screen.dart';
import 'ranking_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Character> _characters = [];
  bool _loading = true;
  int _bottomIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadCharacters();
  }

  Future<void> _loadCharacters() async {
    try {
      final data = await ApiService.getCharacters();
      setState(() {
        _characters = data.map((e) => Character.fromJson(e)).toList();
      });
    } catch (e) {
      debugPrint('캐릭터 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
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
        title: ShaderMask(
          shaderCallback: (bounds) => const LinearGradient(
            colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
          ).createShader(bounds),
          child: const Text(
            'Stellia',
            style: TextStyle(
              fontSize: 24, fontWeight: FontWeight.w800,
              color: Colors.white, letterSpacing: -0.5,
            ),
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search_rounded, color: Color(0xFF6B7280)),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SearchScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_rounded, color: Color(0xFF6B7280)),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const NotificationScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.emoji_events_rounded, color: Color(0xFF6B7280)),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RankingScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Color(0xFF6B7280)),
            onPressed: _logout,
          ),
        ],
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
              onRefresh: _loadCharacters,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  // 히어로
                  Container(
                    height: 160,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(20),
                      gradient: const RadialGradient(
                        center: Alignment.topRight,
                        radius: 1.2,
                        colors: [Color(0xFF2D1B69), Color(0xFF0F0F18)],
                      ),
                      border: Border.all(color: const Color(0xFF1F1F2E)),
                    ),
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          'Meet Fate.',
                          style: TextStyle(
                            fontSize: 26, fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                        ShaderMask(
                          shaderCallback: (bounds) => const LinearGradient(
                            colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                          ).createShader(bounds),
                          child: const Text(
                            'Beyond Worlds.',
                            style: TextStyle(
                              fontSize: 26, fontWeight: FontWeight.w800,
                              color: Colors.white,
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Chat with AI characters from other worlds.',
                          style: TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // 인기 캐릭터
                  const Text(
                    '🔥 인기 캐릭터',
                    style: TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 14),

                  ..._characters.map((char) => _CharacterCard(
                    character: char,
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => CharacterProfileScreen(character: char),
                      ),
                    ),
                  )),
                ],
              ),
            ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0xFF1F1F2E))),
          color: Color(0xFF0A0A0F),
        ),
        child: BottomNavigationBar(
          currentIndex: _bottomIndex,
          onTap: (i) {
            if (i == 1) {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const CommunityScreen()));
            } else if (i == 2) {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const PartyLobbyScreen()));
            } else if (i == 3) {
              Navigator.push(context, MaterialPageRoute(builder: (_) => const MyPageScreen()));
            } else {
              setState(() => _bottomIndex = i);
            }
          },
          backgroundColor: Colors.transparent,
          elevation: 0,
          selectedItemColor: const Color(0xFF7C6CFF),
          unselectedItemColor: const Color(0xFF6B7280),
          type: BottomNavigationBarType.fixed,
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home_rounded), label: '홈'),
            BottomNavigationBarItem(icon: Icon(Icons.explore_rounded), label: '탐색'),
            BottomNavigationBarItem(icon: Icon(Icons.chat_bubble_rounded), label: '채팅'),
            BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: '프로필'),
          ],
        ),
      ),
    );
  }
}

class _CharacterCard extends StatelessWidget {
  final Character character;
  final VoidCallback onTap;

  const _CharacterCard({required this.character, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF0F0F18),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF1F1F2E)),
        ),
        child: Row(
          children: [
            // 아바타
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: character.imageUrl.isNotEmpty
                  ? Image.network(
                      character.imageUrl,
                      width: 64, height: 64,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => _AvatarPlaceholder(name: character.name),
                    )
                  : _AvatarPlaceholder(name: character.name),
            ),
            const SizedBox(width: 14),

            // 정보
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    character.name,
                    style: const TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    character.description,
                    style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _Stat(icon: Icons.favorite_rounded, value: character.likeCount, color: const Color(0xFFFF6B8A)),
                      const SizedBox(width: 12),
                      _Stat(icon: Icons.chat_bubble_rounded, value: character.chatCount, color: const Color(0xFF5FD6FF)),
                    ],
                  ),
                ],
              ),
            ),

            const Icon(Icons.chevron_right_rounded, color: Color(0xFF6B7280)),
          ],
        ),
      ),
    );
  }
}

class _AvatarPlaceholder extends StatelessWidget {
  final String name;
  const _AvatarPlaceholder({required this.name});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 64, height: 64,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Center(
        child: Text(
          name.isNotEmpty ? name[0] : '?',
          style: const TextStyle(
            fontSize: 24, fontWeight: FontWeight.w700, color: Colors.white,
          ),
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final IconData icon;
  final int value;
  final Color color;
  const _Stat({required this.icon, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 13, color: color),
        const SizedBox(width: 4),
        Text(
          value.toLocaleString(),
          style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600),
        ),
      ],
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