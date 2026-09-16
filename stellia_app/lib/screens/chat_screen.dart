import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/character.dart';
import '../widgets/message_feedback.dart';

class ChatScreen extends StatefulWidget {
  final Character character;
  final bool forceNew;
  const ChatScreen({super.key, required this.character, this.forceNew = false});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  // message_id 를 함께 담아야 피드백을 보낼 수 있어 dynamic 으로 둔다
  final List<Map<String, dynamic>> _messages = [];
  bool _typing = false;
  late String _sessionId;

  @override
  void initState() {
    super.initState();
    if (widget.forceNew) {
      _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
      if (widget.character.firstMessage.isNotEmpty) {
        _messages.add({
          'sender': 'ai',
          'content': widget.character.firstMessage,
        });
      }
    } else {
      _loadExistingSession();
    }
  }

  Future<void> _loadExistingSession() async {
    try {
      final sessions = await ApiService.getChatSessions(widget.character.id);
      if (sessions.isNotEmpty) {
        final sessionId = sessions[0]['session_id'];
        setState(() => _sessionId = sessionId);

        // 채팅 기록 불러오기
        final history = await ApiService.getChatHistory(
          widget.character.id,
          sessionId,
        );
        setState(() {
          _messages.clear();
          for (final msg in history) {
            _messages.add({
              'sender': msg['role'] == 'user' ? 'user' : 'ai',
              'content': msg['content'],
              // 복원된 메시지도 피드백을 보낼 수 있게 서버 id 를 유지한다
              'message_id': msg['id'],
            });
          }
        });
      } else {
        setState(() {
          _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
          if (widget.character.firstMessage.isNotEmpty) {
            _messages.add({
              'sender': 'ai',
              'content': widget.character.firstMessage,
            });
          }
        });
      }
    } catch (e) {
      setState(() {
        _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
      });
    }
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _typing) return;

    setState(() {
      _messages.add({'sender': 'user', 'content': text});
      _typing = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      final res = await ApiService.sendMessage(
        characterId: widget.character.id,
        message: text,
        sessionId: _sessionId,
      );
      setState(() {
        _messages.add({
          'sender': 'ai',
          'content': res['message'] ?? '',
          'message_id': res['message_id'],
        });
      });
    } catch (e) {
      setState(() {
        _messages.add({'sender': 'ai', 'content': '오류가 발생했어요. 다시 시도해줘요.'});
      });
    } finally {
      setState(() => _typing = false);
      _scrollToBottom();
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: widget.character.imageUrl.isNotEmpty
                  ? Image.network(
                      widget.character.imageUrl,
                      width: 36,
                      height: 36,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                          ),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Center(
                          child: Text(
                            widget.character.name[0],
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ),
                    )
                  : Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                        ),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Center(
                        child: Text(
                          widget.character.name[0],
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.character.name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
                const Text(
                  '온라인',
                  style: TextStyle(fontSize: 11, color: Color(0xFF41D980)),
                ),
              ],
            ),
          ],
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: Column(
        children: [
          // 메시지 영역
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(20),
              itemCount: _messages.length + (_typing ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _messages.length && _typing) {
                  return _TypingIndicator(name: widget.character.name);
                }
                final msg = _messages[index];
                final isUser = msg['sender'] == 'user';
                final bubble = _MessageBubble(
                  content: msg['content'] as String? ?? '',
                  isUser: isUser,
                  characterName: widget.character.name,
                );
                // 유저 말풍선은 Row 의 우측 정렬에 의존한다.
                // Column(crossAxisAlignment: start) 로 감싸면 Row 가 shrink-wrap 돼
                // 우측 정렬이 깨지므로, 피드백이 붙는 AI 메시지만 감싼다.
                final messageId = msg['message_id'];
                if (isUser || messageId is! int) return bubble;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    bubble,
                    MessageFeedback(
                      sessionId: _sessionId,
                      messageId: messageId,
                    ),
                  ],
                );
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
                      keyboardType: TextInputType.multiline,
                      textInputAction: TextInputAction.newline,
                      enableIMEPersonalizedLearning: false,
                      decoration: InputDecoration(
                        hintText: '${widget.character.name}에게 메시지...',
                        hintStyle: const TextStyle(color: Color(0xFF6B7280)),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 18,
                          vertical: 12,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: _send,
                  child: Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(
                      Icons.send_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
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

class _MessageBubble extends StatelessWidget {
  final String content;
  final bool isUser;
  final String characterName;

  const _MessageBubble({
    required this.content,
    required this.isUser,
    required this.characterName,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment: isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Center(
                child: Text(
                  characterName[0],
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                gradient: isUser
                    ? const LinearGradient(
                        colors: [Color(0xFF7C6CFF), Color(0xFF6A5AE0)],
                      )
                    : null,
                color: isUser ? null : const Color(0xFF0F0F18),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft: Radius.circular(isUser ? 18 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 18),
                ),
                border: isUser
                    ? null
                    : Border.all(color: const Color(0xFF1F1F2E)),
              ),
              child: Text(
                content,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  height: 1.6,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TypingIndicator extends StatelessWidget {
  final String name;
  const _TypingIndicator({required this.name});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Center(
              child: Text(
                name[0],
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF0F0F18),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFF1F1F2E)),
            ),
            child: const Row(
              children: [
                _Dot(delay: 0),
                SizedBox(width: 4),
                _Dot(delay: 150),
                SizedBox(width: 4),
                _Dot(delay: 300),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Dot extends StatefulWidget {
  final int delay;
  const _Dot({required this.delay});

  @override
  State<_Dot> createState() => _DotState();
}

class _DotState extends State<_Dot> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _animation = Tween(
      begin: 0.4,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
    Future.delayed(Duration(milliseconds: widget.delay), () {
      if (mounted) _controller.repeat(reverse: true);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _animation,
      child: Container(
        width: 8,
        height: 8,
        decoration: const BoxDecoration(
          color: Color(0xFF7C6CFF),
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}
