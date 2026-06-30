import 'package:flutter/material.dart';
import '../models/character.dart';
import '../services/api_service.dart';
import 'chat_screen.dart';

class CharacterProfileScreen extends StatefulWidget {
  final Character character;
  const CharacterProfileScreen({super.key, required this.character});

  @override
  State<CharacterProfileScreen> createState() => _CharacterProfileScreenState();
}

class _CharacterProfileScreenState extends State<CharacterProfileScreen> {
  bool _isLiked = false;
  bool _isBookmarked = false;
  int _likeCount = 0;

  @override
  void initState() {
    super.initState();
    _likeCount = widget.character.likeCount;
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    try {
      final token = await ApiService.getToken();
      if (token == null) return;
      // 좋아요/북마크 상태 로드 가능하면 추가
    } catch (e) {
      debugPrint('상태 로드 실패: $e');
    }
  }

  Future<void> _toggleLike() async {
    try {
      await ApiService.toggleLike(widget.character.id);
      setState(() {
        _isLiked = !_isLiked;
        _likeCount += _isLiked ? 1 : -1;
      });
    } catch (e) {
      debugPrint('좋아요 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final char = widget.character;
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      body: CustomScrollView(
        slivers: [
          // 헤더 이미지
          SliverAppBar(
            expandedHeight: 320,
            pinned: true,
            backgroundColor: const Color(0xFF0A0A0F),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
              onPressed: () => Navigator.pop(context),
            ),
            flexibleSpace: FlexibleSpaceBar(
              background: char.imageUrl.isNotEmpty
                  ? Image.network(
                      char.imageUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => _AvatarPlaceholder(name: char.name),
                    )
                  : _AvatarPlaceholder(name: char.name),
            ),
          ),

          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 이름 + 액션 버튼
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          char.name,
                          style: const TextStyle(
                            fontSize: 28, fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      // 좋아요
                      _ActionButton(
                        icon: _isLiked ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                        color: _isLiked ? const Color(0xFFFF6B8A) : const Color(0xFF6B7280),
                        onTap: _toggleLike,
                      ),
                      const SizedBox(width: 8),
                      // 북마크
                      _ActionButton(
                        icon: _isBookmarked ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
                        color: _isBookmarked ? const Color(0xFFFFD700) : const Color(0xFF6B7280),
                        onTap: () => setState(() => _isBookmarked = !_isBookmarked),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  // 태그
                  if (char.tags.isNotEmpty)
                    Wrap(
                      spacing: 8,
                      children: char.tags.map((tag) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF7C6CFF).withOpacity(0.12),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(color: const Color(0xFF7C6CFF).withOpacity(0.3)),
                        ),
                        child: Text(
                          '#$tag',
                          style: const TextStyle(color: Color(0xFF7C6CFF), fontSize: 12),
                        ),
                      )).toList(),
                    ),
                  const SizedBox(height: 16),

                  // 통계
                  Row(
                    children: [
                      _Stat(icon: Icons.favorite_rounded, value: _likeCount, color: const Color(0xFFFF6B8A), label: '좋아요'),
                      const SizedBox(width: 20),
                      _Stat(icon: Icons.chat_bubble_rounded, value: char.chatCount, color: const Color(0xFF5FD6FF), label: '대화수'),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // 소개
                  if (char.description.isNotEmpty) ...[
                    const Text('소개', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Text(
                      char.description,
                      style: const TextStyle(color: Colors.white70, fontSize: 15, height: 1.6),
                    ),
                    const SizedBox(height: 24),
                  ],

                  // 대화 시작 버튼
                  SizedBox(
                    width: double.infinity,
                    height: 54,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ElevatedButton(
                        onPressed: () => Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(builder: (_) => ChatScreen(character: char)),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        child: const Text(
                          '대화 시작하기',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
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
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Center(
        child: Text(
          name.isNotEmpty ? name[0] : '?',
          style: const TextStyle(fontSize: 80, fontWeight: FontWeight.w700, color: Colors.white),
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  const _ActionButton({required this.icon, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 44, height: 44,
        decoration: BoxDecoration(
          color: const Color(0xFF0F0F18),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF1F1F2E)),
        ),
        child: Icon(icon, color: color, size: 22),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final IconData icon;
  final int value;
  final Color color;
  final String label;
  const _Stat({required this.icon, required this.value, required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: color, size: 16),
        const SizedBox(width: 6),
        Text(
          value.toLocaleString(),
          style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 14),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12)),
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