import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/character.dart';
import 'character_profile_screen.dart';

class RankingScreen extends StatefulWidget {
  const RankingScreen({super.key});

  @override
  State<RankingScreen> createState() => _RankingScreenState();
}

class _RankingScreenState extends State<RankingScreen> {
  List<Character> _characters = [];
  bool _loading = true;
  String _sort = 'popular';

  final List<Map<String, String>> _sortOptions = [
    {'key': 'popular', 'label': '인기순'},
    {'key': 'chat', 'label': '대화순'},
    {'key': 'latest', 'label': '최신순'},
    {'key': 'view', 'label': '조회순'},
  ];

  @override
  void initState() {
    super.initState();
    _loadRanking();
  }

  Future<void> _loadRanking() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getRanking(sort: _sort);
      setState(() => _characters = data.map((e) => Character.fromJson(e)).toList());
    } catch (e) {
      debugPrint('랭킹 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text('🏆 랭킹', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: Column(
        children: [
          // 정렬 탭
          SizedBox(
            height: 48,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _sortOptions.length,
              itemBuilder: (context, i) {
                final opt = _sortOptions[i];
                final selected = _sort == opt['key'];
                return GestureDetector(
                  onTap: () {
                    setState(() => _sort = opt['key']!);
                    _loadRanking();
                  },
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      gradient: selected ? const LinearGradient(
                        colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                      ) : null,
                      color: selected ? null : const Color(0xFF0F0F18),
                      borderRadius: BorderRadius.circular(999),
                      border: Border.all(color: const Color(0xFF1F1F2E)),
                    ),
                    child: Center(
                      child: Text(
                        opt['label']!,
                        style: TextStyle(
                          color: selected ? Colors.white : const Color(0xFF6B7280),
                          fontWeight: FontWeight.w600, fontSize: 13,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          // 랭킹 목록
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C6CFF)))
                : RefreshIndicator(
                    color: const Color(0xFF7C6CFF),
                    backgroundColor: const Color(0xFF0F0F18),
                    onRefresh: _loadRanking,
                    child: ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _characters.length,
                      itemBuilder: (context, i) {
                        final char = _characters[i];
                        return GestureDetector(
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => CharacterProfileScreen(character: char)),
                          ),
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0F0F18),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: i < 3 ? const Color(0xFF7C6CFF).withOpacity(0.3) : const Color(0xFF1F1F2E),
                              ),
                            ),
                            child: Row(
                              children: [
                                // 순위
                                SizedBox(
                                  width: 36,
                                  child: Text(
                                    i == 0 ? '🥇' : i == 1 ? '🥈' : i == 2 ? '🥉' : '${i + 1}',
                                    style: TextStyle(
                                      fontSize: i < 3 ? 22 : 15,
                                      fontWeight: FontWeight.w700,
                                      color: Colors.white,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                                const SizedBox(width: 10),

                                // 아바타
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(10),
                                  child: char.imageUrl.isNotEmpty
                                      ? Image.network(char.imageUrl, width: 52, height: 52, fit: BoxFit.cover,
                                          errorBuilder: (_, __, ___) => _placeholder(char.name))
                                      : _placeholder(char.name),
                                ),
                                const SizedBox(width: 12),

                                // 정보
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(char.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                                      const SizedBox(height: 4),
                                      Text(char.description, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                                      const SizedBox(height: 6),
                                      Row(
                                        children: [
                                          const Icon(Icons.favorite_rounded, color: Color(0xFFFF6B8A), size: 12),
                                          const SizedBox(width: 3),
                                          Text('${char.likeCount}', style: const TextStyle(color: Color(0xFFFF6B8A), fontSize: 12, fontWeight: FontWeight.w600)),
                                          const SizedBox(width: 10),
                                          const Icon(Icons.chat_bubble_rounded, color: Color(0xFF5FD6FF), size: 12),
                                          const SizedBox(width: 3),
                                          Text('${char.chatCount}', style: const TextStyle(color: Color(0xFF5FD6FF), fontSize: 12, fontWeight: FontWeight.w600)),
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
                      },
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _placeholder(String name) => Container(
    width: 52, height: 52,
    decoration: BoxDecoration(
      gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
      borderRadius: BorderRadius.circular(10),
    ),
    child: Center(child: Text(name[0], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 20))),
  );
}