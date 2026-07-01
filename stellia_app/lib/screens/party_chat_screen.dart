import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import '../services/api_service.dart';

class PartyChatScreen extends StatefulWidget {
  final String roomCode;
  const PartyChatScreen({super.key, required this.roomCode});

  @override
  State<PartyChatScreen> createState() => _PartyChatScreenState();
}

class _PartyChatScreenState extends State<PartyChatScreen> {
  WebSocketChannel? _channel;
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  bool _connected = false;
  bool _started = false;
  int? _userId;

  @override
  void initState() {
    super.initState();
    _connect();
  }

  Future<void> _connect() async {
    try {
      final token = await ApiService.getToken();
      final me = await ApiService.getMe();
      _userId = me['id'];

      final wsUrl = ApiService.baseUrl
          .replaceFirst('https://', 'wss://')
          .replaceFirst('http://', 'ws://');

      _channel = WebSocketChannel.connect(
        Uri.parse('$wsUrl/party/ws/${widget.roomCode}/$_userId'),
      );

      setState(() => _connected = true);

      _channel!.stream.listen(
        (data) {
          final msg = jsonDecode(data);
          setState(() => _messages.add(msg));
          _scrollToBottom();
        },
        onDone: () => setState(() => _connected = false),
        onError: (_) => setState(() => _connected = false),
      );
    } catch (e) {
      debugPrint('WebSocket 연결 실패: $e');
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _startGame() {
    _channel?.sink.add(jsonEncode({'type': 'start'}));
    setState(() => _started = true);
  }

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty || !_connected) return;
    _channel?.sink.add(jsonEncode({'type': 'chat', 'message': text}));
    _controller.clear();
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: Row(
          children: [
            Text(
              '파티챗 · ${widget.roomCode}',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
            ),
            const SizedBox(width: 8),
            Container(
              width: 8, height: 8,
              decoration: BoxDecoration(
                color: _connected ? const Color(0xFF49D89A) : const Color(0xFFFF6B8A),
                shape: BoxShape.circle,
              ),
            ),
          ],
        ),
        actions: [
          if (!_started)
            TextButton(
              onPressed: _startGame,
              child: const Text('시작', style: TextStyle(color: Color(0xFF7C6CFF), fontWeight: FontWeight.w700)),
            ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: Column(
        children: [
          // 메시지 영역
          Expanded(
            child: _messages.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('⚔', style: TextStyle(fontSize: 48)),
                        SizedBox(height: 16),
                        Text('시작 버튼을 눌러 파티챗을 시작하세요', style: TextStyle(color: Color(0xFF6B7280), fontSize: 14)),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, i) {
                      final msg = _messages[i];
                      final type = msg['type'] ?? 'chat';

                      if (type == 'system') {
                        return _SystemMessage(message: msg['message'] ?? '');
                      } else if (type == 'narration') {
                        return _NarrationBubble(message: msg['message'] ?? '');
                      } else {
                        return _ChatBubble(
                          username: msg['username'] ?? '',
                          message: msg['message'] ?? '',
                          isMe: msg['username'] == null,
                        );
                      }
                    },
                  ),
          ),

          // 입력창
          Container(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            decoration: const BoxDecoration(
              color: Color(0xFF0A0A0F),
              border: Border(top: BorderSide(color: Color(0xFF1F1F2E))),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F0F18),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFF1F1F2E)),
                    ),
                    child: TextField(
                      controller: _controller,
                      style: const TextStyle(color: Colors.white, fontSize: 15),
                      maxLines: null,
                      decoration: const InputDecoration(
                        hintText: '메시지 입력...',
                        hintStyle: TextStyle(color: Color(0xFF6B7280)),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: _sendMessage,
                  child: Container(
                    width: 46, height: 46,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SystemMessage extends StatelessWidget {
  final String message;
  const _SystemMessage({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Center(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
          decoration: BoxDecoration(
            color: const Color(0xFF1F1F2E),
            borderRadius: BorderRadius.circular(999),
          ),
          child: Text(message, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12)),
        ),
      ),
    );
  }
}

class _NarrationBubble extends StatelessWidget {
  final String message;
  const _NarrationBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF7C6CFF).withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF7C6CFF).withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('✦ 나레이션', style: TextStyle(color: Color(0xFF7C6CFF), fontSize: 11, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(message, style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.6)),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final String username;
  final String message;
  final bool isMe;

  const _ChatBubble({required this.username, required this.message, required this.isMe});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isMe) ...[
            Container(
              width: 30, height: 30,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Center(
                child: Text(
                  username.isNotEmpty ? username[0].toUpperCase() : '?',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12),
                ),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment: isMe ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                if (!isMe)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 4, left: 4),
                    child: Text(username, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 11)),
                  ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    gradient: isMe ? const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF6A5AE0)]) : null,
                    color: isMe ? null : const Color(0xFF0F0F18),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(isMe ? 16 : 4),
                      bottomRight: Radius.circular(isMe ? 4 : 16),
                    ),
                    border: isMe ? null : Border.all(color: const Color(0xFF1F1F2E)),
                  ),
                  child: Text(message, style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.5)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}