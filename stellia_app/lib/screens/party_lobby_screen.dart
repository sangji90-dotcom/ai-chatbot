import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'party_room_screen.dart';

class PartyLobbyScreen extends StatefulWidget {
  const PartyLobbyScreen({super.key});

  @override
  State<PartyLobbyScreen> createState() => _PartyLobbyScreenState();
}

class _PartyLobbyScreenState extends State<PartyLobbyScreen> {
  List<dynamic> _stories = [];
  bool _loading = true;
  final _codeController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadStories();
  }

  Future<void> _loadStories() async {
    try {
      final data = await ApiService.getStories();
      setState(() => _stories = data);
    } catch (e) {
      debugPrint('스토리 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _showJoinDialog() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF0F0F18),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('방 코드 입력', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        content: TextField(
          controller: _codeController,
          style: const TextStyle(color: Colors.white),
          textCapitalization: TextCapitalization.characters,
          decoration: InputDecoration(
            hintText: '방 코드 6자리',
            hintStyle: const TextStyle(color: Color(0xFF6B7280)),
            filled: true,
            fillColor: const Color(0xFF1A1A2E),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF7C6CFF))),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소', style: TextStyle(color: Color(0xFF6B7280))),
          ),
          ElevatedButton(
            onPressed: () async {
              final code = _codeController.text.trim().toUpperCase();
              if (code.isEmpty) return;
              final nav = Navigator.of(context);
              nav.pop();
              try {
                await ApiService.joinRoom(code);
                nav.push(MaterialPageRoute(
                  builder: (_) => PartyRoomScreen(roomCode: code),
                ));
              } catch (e) {
                debugPrint('방 입장 실패: $e');
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF7C6CFF),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('입장', style: TextStyle(color: Colors.white)),
          ),
        ],
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
        title: const Text('파티챗', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        actions: [
          TextButton(
            onPressed: _showJoinDialog,
            child: const Text('코드 입장', style: TextStyle(color: Color(0xFF7C6CFF), fontWeight: FontWeight.w600)),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C6CFF)))
          : RefreshIndicator(
              color: const Color(0xFF7C6CFF),
              backgroundColor: const Color(0xFF0F0F18),
              onRefresh: _loadStories,
              child: _stories.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text('⚔', style: TextStyle(fontSize: 48)),
                          const SizedBox(height: 16),
                          const Text('아직 스토리가 없어요.', style: TextStyle(color: Color(0xFF6B7280), fontSize: 15)),
                          const SizedBox(height: 8),
                          const Text('코드 입장으로 친구 방에 참여해보세요!', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                          const SizedBox(height: 24),
                          ElevatedButton(
                            onPressed: _showJoinDialog,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF7C6CFF),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                            ),
                            child: const Text('코드로 입장', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _stories.length,
                      itemBuilder: (context, i) {
                        final story = _stories[i];
                        return _StoryCard(
                          story: story,
                          onCreateRoom: () async {
                            final nav = Navigator.of(context);
                            try {
                              final res = await ApiService.createRoom(
                                story['id'],
                                story['max_players'] ?? 4,
                              );
                              nav.push(MaterialPageRoute(
                                builder: (_) => PartyRoomScreen(roomCode: res['code']),
                              ));
                            } catch (e) {
                              debugPrint('방 만들기 실패: $e');
                            }
                          },
                        );
                      },
                    ),
            ),
    );
  }
}

class _StoryCard extends StatelessWidget {
  final Map<String, dynamic> story;
  final VoidCallback onCreateRoom;

  const _StoryCard({required this.story, required this.onCreateRoom});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF0F0F18),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1F1F2E)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (story['image_url'] != null && story['image_url'].toString().isNotEmpty)
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
              child: Image.network(
                story['image_url'],
                height: 140, width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _defaultImage(),
              ),
            )
          else
            _defaultImage(radius: const BorderRadius.vertical(top: Radius.circular(16))),

          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        story['title'] ?? '',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
                      ),
                    ),
                    if (story['is_official'] == true)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFD700).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(color: const Color(0xFFFFD700).withValues(alpha: 0.3)),
                        ),
                        child: const Text('공식', style: TextStyle(color: Color(0xFFFFD700), fontSize: 11, fontWeight: FontWeight.w600)),
                      ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(story['genre'] ?? '', style: const TextStyle(color: Color(0xFF7C6CFF), fontSize: 12)),
                const SizedBox(height: 8),
                Text(
                  story['background'] ?? '',
                  style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13, height: 1.5),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    const Icon(Icons.people_rounded, color: Color(0xFF6B7280), size: 14),
                    const SizedBox(width: 4),
                    Text(
                      '${story['min_players'] ?? 2}~${story['max_players'] ?? 6}명',
                      style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12),
                    ),
                    const Spacer(),
                    SizedBox(
                      height: 36,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: ElevatedButton(
                          onPressed: onCreateRoom,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.transparent,
                            shadowColor: Colors.transparent,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            padding: const EdgeInsets.symmetric(horizontal: 16),
                          ),
                          child: const Text('방 만들기', style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _defaultImage({BorderRadius? radius}) {
    return Container(
      height: 100,
      decoration: BoxDecoration(
        gradient: const LinearGradient(colors: [Color(0xFF2D1B69), Color(0xFF0F0F18)]),
        borderRadius: radius,
      ),
      child: const Center(child: Text('⚔', style: TextStyle(fontSize: 40))),
    );
  }
}