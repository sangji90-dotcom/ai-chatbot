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
    setState(() => _loading = true);
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

  void _showWriteModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0F0F18),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => _WritePostModal(onPosted: () {
        Navigator.pop(context);
        _loadPosts();
      }),
    );
  }

  void _showDetail(Map<String, dynamic> post, int index) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF0F0F18),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => _PostDetailModal(
        post: post,
        onLike: () => _toggleLike(post['id'], index),
        onDeleted: () {
          Navigator.pop(context);
          _loadPosts();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text('커뮤니티', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        actions: [
          TextButton(
            onPressed: _showWriteModal,
            child: const Text('+ 글쓰기', style: TextStyle(color: Color(0xFF7C6CFF), fontWeight: FontWeight.w600)),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: Column(
        children: [
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
                    setState(() => _selectedType = t['key']!);
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
                              return GestureDetector(
                                onTap: () => _showDetail(post, i),
                                child: _PostCard(
                                  post: post,
                                  onLike: () => _toggleLike(post['id'], i),
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
}

// ── 게시글 카드 ──────────────────────────────────────────────
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
            ],
          ),
          const SizedBox(height: 12),
          if (post['title'] != null && post['title'].toString().isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(post['title'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
            ),
          Text(
            post['content'] ?? '',
            style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.5),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 12),
          const Divider(color: Color(0xFF1F1F2E), height: 1),
          const SizedBox(height: 10),
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
                    Text('${post['like_count'] ?? 0}',
                      style: TextStyle(
                        color: post['is_liked'] == true ? const Color(0xFFFF6B8A) : const Color(0xFF6B7280),
                        fontSize: 13, fontWeight: FontWeight.w600,
                      )),
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

// ── 글쓰기 모달 ──────────────────────────────────────────────
class _WritePostModal extends StatefulWidget {
  final VoidCallback onPosted;
  const _WritePostModal({required this.onPosted});

  @override
  State<_WritePostModal> createState() => _WritePostModalState();
}

class _WritePostModalState extends State<_WritePostModal> {
  final _titleController = TextEditingController();
  final _contentController = TextEditingController();
  String _postType = 'general';
  bool _submitting = false;

  final List<Map<String, String>> _types = [
    {'key': 'general', 'label': '💬 일반'},
    {'key': 'party_recruit', 'label': '⚔ 파티 모집'},
    {'key': 'fanart', 'label': '🎨 팬아트'},
  ];

  Future<void> _submit() async {
    if (_contentController.text.trim().isEmpty) return;
    setState(() => _submitting = true);
    try {
      await ApiService.createPost(
        content: _contentController.text.trim(),
        title: _titleController.text.trim(),
        postType: _postType,
      );
      widget.onPosted();
    } catch (e) {
      debugPrint('글쓰기 실패: $e');
    } finally {
      setState(() => _submitting = false);
    }
  }

  InputDecoration _deco(String hint) => InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: Color(0xFF6B7280)),
    filled: true,
    fillColor: const Color(0xFF1A1A2E),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF7C6CFF))),
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
  );

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40, height: 4,
                decoration: BoxDecoration(color: const Color(0xFF1F1F2E), borderRadius: BorderRadius.circular(2)),
              ),
            ),
            const SizedBox(height: 20),
            const Text('게시글 작성', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              children: _types.map((t) => GestureDetector(
                onTap: () => setState(() => _postType = t['key']!),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    gradient: _postType == t['key'] ? const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]) : null,
                    color: _postType == t['key'] ? null : const Color(0xFF1A1A2E),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: const Color(0xFF1F1F2E)),
                  ),
                  child: Text(t['label']!, style: TextStyle(color: _postType == t['key'] ? Colors.white : const Color(0xFF6B7280), fontSize: 13, fontWeight: FontWeight.w600)),
                ),
              )).toList(),
            ),
            const SizedBox(height: 12),
            TextField(controller: _titleController, style: const TextStyle(color: Colors.white), decoration: _deco('제목 (선택)')),
            const SizedBox(height: 10),
            TextField(controller: _contentController, style: const TextStyle(color: Colors.white), decoration: _deco('내용을 입력해주세요...'), maxLines: 4),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: _submitting ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF7C6CFF),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                child: _submitting
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('게시하기', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 게시글 상세 모달 ──────────────────────────────────────────
class _PostDetailModal extends StatefulWidget {
  final Map<String, dynamic> post;
  final VoidCallback onLike;
  final VoidCallback onDeleted;

  const _PostDetailModal({required this.post, required this.onLike, required this.onDeleted});

  @override
  State<_PostDetailModal> createState() => _PostDetailModalState();
}

class _PostDetailModalState extends State<_PostDetailModal> {
  List<dynamic> _comments = [];
  final _commentController = TextEditingController();
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _loadComments();
  }

  Future<void> _loadComments() async {
    try {
      final res = await ApiService.getPostDetail(widget.post['id']);
      setState(() => _comments = res['comments'] ?? []);
    } catch (e) {
      debugPrint('댓글 로드 실패: $e');
    }
  }

  Future<void> _submitComment() async {
    if (_commentController.text.trim().isEmpty) return;
    setState(() => _submitting = true);
    try {
      await ApiService.createComment(widget.post['id'], _commentController.text.trim());
      _commentController.clear();
      await _loadComments();
    } catch (e) {
      debugPrint('댓글 작성 실패: $e');
    } finally {
      setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      maxChildSize: 0.95,
      builder: (_, controller) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40, height: 4,
                      decoration: BoxDecoration(color: const Color(0xFF1F1F2E), borderRadius: BorderRadius.circular(2)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (widget.post['title'] != null && widget.post['title'].toString().isNotEmpty)
                    Text(widget.post['title'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
                  const SizedBox(height: 8),
                  Text(widget.post['username'] ?? '', style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                  const SizedBox(height: 12),
                  Text(widget.post['content'] ?? '', style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.6)),
                  const SizedBox(height: 12),
                  GestureDetector(
                    onTap: widget.onLike,
                    child: Row(
                      children: [
                        Icon(
                          widget.post['is_liked'] == true ? Icons.favorite_rounded : Icons.favorite_border_rounded,
                          color: widget.post['is_liked'] == true ? const Color(0xFFFF6B8A) : const Color(0xFF6B7280),
                          size: 20,
                        ),
                        const SizedBox(width: 4),
                        Text('${widget.post['like_count'] ?? 0}', style: const TextStyle(color: Color(0xFF6B7280))),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Divider(color: Color(0xFF1F1F2E)),
                  const SizedBox(height: 8),
                  Text('댓글 ${_comments.length}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                ],
              ),
            ),
            Expanded(
              child: ListView.builder(
                controller: controller,
                padding: const EdgeInsets.symmetric(horizontal: 20),
                itemCount: _comments.length,
                itemBuilder: (_, i) {
                  final c = _comments[i];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 28, height: 28,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Center(child: Text((c['username'] ?? '?')[0].toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700))),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(c['username'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                              Text(c['content'] ?? '', style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.5)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _commentController,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        hintText: '댓글 작성...',
                        hintStyle: const TextStyle(color: Color(0xFF6B7280)),
                        filled: true,
                        fillColor: const Color(0xFF1A1A2E),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
                        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
                        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF7C6CFF))),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: _submitting ? null : _submitComment,
                    child: Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: _submitting
                          ? const Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}