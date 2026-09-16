import 'package:flutter/material.dart';

import '../services/api_service.dart';

/// AI 메시지 하단의 👍/👎 + 사유 칩.
///
/// 웹(MessageFeedback.tsx)과 동일한 사유 코드를 쓴다.
/// 앱 테스터의 "기억 못함" 신고가 집계에 들어오게 하는 유일한 경로다.
class MessageFeedback extends StatefulWidget {
  final String sessionId;
  final int messageId;

  const MessageFeedback({
    super.key,
    required this.sessionId,
    required this.messageId,
  });

  @override
  State<MessageFeedback> createState() => _MessageFeedbackState();
}

class _MessageFeedbackState extends State<MessageFeedback> {
  static const _reasons = <String, String>{
    'memory': '앞서 한 얘기를 기억 못해요',
    'repetition': '같은 말을 반복해요',
    'tone': '말투가 캐릭터랑 안 맞아요',
    'offtopic': '엉뚱한 소리를 해요',
    'quality': '너무 짧거나 성의 없어요',
    'other': '기타',
  };

  String? _sent;
  bool _picking = false;

  Future<void> _send(String rating, [String reason = '']) async {
    setState(() {
      _sent = rating;
      _picking = false;
    });
    try {
      await ApiService.rateMessage(
        sessionId: widget.sessionId,
        messageId: widget.messageId,
        rating: rating,
        reason: reason,
      );
    } catch (_) {
      // 피드백 실패가 대화를 방해하면 안 된다
    }
  }

  static const _muted = Color(0xFF8A8FA3);

  @override
  Widget build(BuildContext context) {
    if (_sent == 'like') {
      return const Padding(
        padding: EdgeInsets.only(left: 40, top: 4),
        child: Text('피드백 고마워요', style: TextStyle(fontSize: 11, color: _muted)),
      );
    }
    if (_sent == 'dislike') {
      return const Padding(
        padding: EdgeInsets.only(left: 40, top: 4),
        child: Text('알려줘서 고마워요. 개선에 반영할게요',
            style: TextStyle(fontSize: 11, color: _muted)),
      );
    }

    return Padding(
      padding: const EdgeInsets.only(left: 36, top: 2),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconBtn('👍', () => _send('like')),
              _iconBtn('👎', () => setState(() => _picking = !_picking)),
            ],
          ),
          if (_picking)
            Container(
              margin: const EdgeInsets.only(top: 6),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF151828),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF2A2F45)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('어떤 점이 아쉬웠나요?',
                      style: TextStyle(fontSize: 11, color: _muted)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: _reasons.entries
                        .map((e) => GestureDetector(
                              onTap: () => _send('dislike', e.key),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: const Color(0x1F8B7CFF),
                                  borderRadius: BorderRadius.circular(999),
                                  border:
                                      Border.all(color: const Color(0x4D8B7CFF)),
                                ),
                                child: Text(e.value,
                                    style: const TextStyle(
                                        fontSize: 11, color: Colors.white)),
                              ),
                            ))
                        .toList(),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _iconBtn(String emoji, VoidCallback onTap) => GestureDetector(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
          child: Opacity(
            opacity: 0.45,
            child: Text(emoji, style: const TextStyle(fontSize: 14)),
          ),
        ),
      );
}
