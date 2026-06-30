import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CommunityScreen extends StatefulWidget {
  const CommunityScreen({super.key});

  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> {
  List<dynamic> _posts = [];
  bool _loading = true;
  String _selectedType = 'all';

  final List<Map<String, String>> _types = [
    {'key': 'all', 'label': '전체'},
    {'key': 'general', 'label': '💬 일반'},
    {'key': 'party_recruit', 'label': '⚔ 파티 모집'},
    {'key': 'fanart', 'label': '🎨 팬아트'},
  ];

  @override
  void initState() {
    super.initState();
    _loadPosts();
  }

  Future<void> _loadPosts() async {
    try {
      final data = await ApiService.getCommunityPosts(
        postType: _selectedType == 'all' ? null : _selectedType,
      );
      setState(() => _posts = data);
    } catch (e) {
      debugPrint('게시글 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _toggleLike(int postId, int index) async {
    try {
      final res = await ApiService.togglePostLike(postId);
      setState(() {
        _posts[index]['is_liked'] = res['liked'];
        _posts[index]['like_count'] = res['like_count'];
      });
    } catch (e) {
      debugPrint('좋아요 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text('커뮤니티', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: Column(
        children: [
          // 필터 탭
          SizedBox(
            height: 48,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _types.length,
              itemBuilder: (context, i) {
                final t = _types[i];
                final selected = _selectedType == t['key'];
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      _selectedType = t['key']!;
                      _loading = true;
                    });
                    _loadPosts();
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
                        t['label']!,
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

          // 게시글 목록
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C6CFF)))
                : RefreshIndicator(
                    color: const Color(0xFF7C6CFF),
                    backgroundColor: const Color(0xFF0F0F18),
                    onRefresh: _loadPosts,
                    child: _posts.isEmpty
                        ? const Center(
                            child: Text('게시글이 없어요.', style: TextStyle(color: Color(0xFF6B7280))),
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _posts.length,
                            itemBuilder: (context, i) {
                              final post = _posts[i];
                              return _PostCard(
                                post: post,
                                onLike: () => _toggleLike(post['id'], i),
                              );
                            },
                          ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _PostCard extends StatelessWidget {
  final Map<String, dynamic> post;
  final VoidCallback onLike;

  const _PostCard({required this.post, required this.onLike});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F0F18),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1F1F2E)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 작성자
          Row(
            children: [
              Container(
                width: 32, height: 32,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Center(
                  child: Text(
                    (post['username'] ?? '?')[0].toUpperCase(),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(post['username'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                    Text(
                      post['created_at']?.toString().substring(0, 10) ?? '',
                      style: const TextStyle(color: Color(0xFF6B7280), fontSize: 11),
                    ),
                  ],
                ),
              ),
              if (post['post_type'] == 'party_recruit')
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFF7C6CFF).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: const Color(0xFF7C6CFF).withOpacity(0.3)),
                  ),
                  child: const Text('⚔ 파티 모집', style: TextStyle(color: Color(0xFF7C6CFF), fontSize: 11, fontWeight: FontWeight.w600)),
                ),
            ],
          ),
          const SizedBox(height: 12),

          // 제목
          if (post['title'] != null && post['title'].toString().isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(
                post['title'],
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
              ),
            ),

          // 내용
          Text(
            post['content'] ?? '',
            style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.5),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),

          // 이미지
          if (post['image_url'] != null && post['image_url'].toString().isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: Image.network(
                  post['image_url'],
                  height: 180, width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const SizedBox(),
                ),
              ),
            ),

          // 캐릭터 태그
          if (post['character_tags'] != null && (post['character_tags'] as List).isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Wrap(
                spacing: 6,
                children: (post['character_tags'] as List).map((c) => Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFF5FD6FF).withOpacity(0.08),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: const Color(0xFF5FD6FF).withOpacity(0.2)),
                  ),
                  child: Text('@ ${c['name']}', style: const TextStyle(color: Color(0xFF5FD6FF), fontSize: 11, fontWeight: FontWeight.w600)),
                )).toList(),
              ),
            ),

          const SizedBox(height: 12),
          const Divider(color: Color(0xFF1F1F2E), height: 1),
          const SizedBox(height: 10),

          // 액션
          Row(
            children: [
              GestureDetector(
                onTap: onLike,
                child: Row(
                  children: [
                    Icon(
                      post['is_liked'] == true ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                      color: post['is_liked'] == true ? const Color(0xFFFF6B8A) : const Color(0xFF6B7280),
                      size: 18,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${post['like_count'] ?? 0}',
                      style: TextStyle(
                        color: post['is_liked'] == true ? const Color(0xFFFF6B8A) : const Color(0xFF6B7280),
                        fontSize: 13, fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Row(
                children: [
                  const Icon(Icons.chat_bubble_outline_rounded, color: Color(0xFF6B7280), size: 16),
                  const SizedBox(width: 4),
                  Text('${post['comment_count'] ?? 0}', style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}