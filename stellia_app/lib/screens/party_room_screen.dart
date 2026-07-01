import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'party_chat_screen.dart';

class PartyRoomScreen extends StatefulWidget {
  final String roomCode;
  const PartyRoomScreen({super.key, required this.roomCode});

  @override
  State<PartyRoomScreen> createState() => _PartyRoomScreenState();
}

class _PartyRoomScreenState extends State<PartyRoomScreen> {
  Map<String, dynamic>? _room;
  List<dynamic> _members = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadRoom();
  }

  Future<void> _loadRoom() async {
    try {
      final data = await ApiService.getRoomInfo(widget.roomCode);
      setState(() {
        _room = data['room'];
        _members = data['members'] ?? [];
      });
    } catch (e) {
      debugPrint('방 정보 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _leaveRoom() async {
    try {
      await ApiService.leaveRoom(widget.roomCode);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      debugPrint('방 나가기 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: Text(
          '방 코드: ${widget.roomCode}',
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        actions: [
          TextButton(
            onPressed: _leaveRoom,
            child: const Text('나가기', style: TextStyle(color: Color(0xFFFF6B8A))),
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
              onRefresh: _loadRoom,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [Color(0xFF2D1B69), Color(0xFF0F0F18)]),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFF7C6CFF).withValues(alpha: 0.3)),
                    ),
                    child: Column(
                      children: [
                        const Text('⚔', style: TextStyle(fontSize: 40)),
                        const SizedBox(height: 12),
                        const Text('방 코드', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                        const SizedBox(height: 4),
                        Text(
                          widget.roomCode,
                          style: const TextStyle(color: Color(0xFF7C6CFF), fontSize: 32, fontWeight: FontWeight.w800, letterSpacing: 8),
                        ),
                        const SizedBox(height: 8),
                        const Text('친구에게 코드를 공유해서 초대하세요', style: TextStyle(color: Color(0xFF6B7280), fontSize: 12)),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  Row(
                    children: [
                      const Text('참여자', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFF7C6CFF).withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          '${_members.length}/${_room?['max_members'] ?? 4}',
                          style: const TextStyle(color: Color(0xFF7C6CFF), fontSize: 12, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  ..._members.map((m) => Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F0F18),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFF1F1F2E)),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 40, height: 40,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Center(
                            child: Text(
                              (m['username'] ?? '?')[0].toUpperCase(),
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            m['username'] ?? '',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 15),
                          ),
                        ),
                        if (m['user_id'] == _room?['host_id'])
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFFD700).withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(999),
                              border: Border.all(color: const Color(0xFFFFD700).withValues(alpha: 0.3)),
                            ),
                            child: const Text('방장', style: TextStyle(color: Color(0xFFFFD700), fontSize: 11, fontWeight: FontWeight.w600)),
                          ),
                      ],
                    ),
                  )),

                  const SizedBox(height: 24),

                  SizedBox(
                    width: double.infinity,
                    height: 54,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ElevatedButton(
                        onPressed: _members.length < 2
                            ? null
                            : () => Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(builder: (_) => PartyChatScreen(roomCode: widget.roomCode)),
                              ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        child: Text(
                          _members.length < 2 ? '2명 이상 모이면 시작 가능해요' : '파티챗 시작',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}