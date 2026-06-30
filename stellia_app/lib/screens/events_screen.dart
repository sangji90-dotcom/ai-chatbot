import 'package:flutter/material.dart';
import '../services/api_service.dart';

class EventsScreen extends StatefulWidget {
  const EventsScreen({super.key});

  @override
  State<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends State<EventsScreen> {
  Map<String, dynamic>? _user;
  Map<String, dynamic>? _referralInfo;
  bool _loading = true;
  bool _attendanceLoading = false;
  bool _attended = false;
  String _message = '';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final user = await ApiService.getMe();
      final today = DateTime.now().toIso8601String().substring(0, 10);
      setState(() {
        _user = user;
        _attended = user['last_attendance_date'] == today;
      });
    } catch (e) {
      debugPrint('데이터 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _attendance() async {
    setState(() { _attendanceLoading = true; _message = ''; });
    try {
      final res = await ApiService.attendance();
      setState(() {
        _message = res['message'] ?? '출석 완료!';
        _attended = true;
      });
    } catch (e) {
      setState(() => _message = '이미 출석했어요.');
    } finally {
      setState(() => _attendanceLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text('이벤트', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C6CFF)))
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                // 출석 체크
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2D1B69), Color(0xFF0F0F18)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF7C6CFF).withOpacity(0.3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Text('🎯 ', style: TextStyle(fontSize: 20)),
                          Text(
                            '출석 체크',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '매일 출석하면 은화 1,000개를 드려요',
                        style: TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                      ),
                      if (_user?['attendance_streak'] != null && _user!['attendance_streak'] > 0)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            decoration: BoxDecoration(
                              color: const Color(0xFF7C6CFF).withOpacity(0.15),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(
                              '🔥 ${_user!['attendance_streak']}일 연속',
                              style: const TextStyle(color: Color(0xFF7C6CFF), fontWeight: FontWeight.w600, fontSize: 13),
                            ),
                          ),
                        ),
                      const SizedBox(height: 16),
                      if (_message.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: Text(
                            _message,
                            style: const TextStyle(color: Color(0xFF49D89A), fontSize: 13),
                          ),
                        ),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: _attended || _attendanceLoading ? null : _attendance,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _attended ? const Color(0xFF1F1F2E) : const Color(0xFF7C6CFF),
                            disabledBackgroundColor: const Color(0xFF1F1F2E),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                          child: _attendanceLoading
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : Text(
                                  _attended ? '오늘 출석 완료 ✓' : '출석 체크 +1,000 🥈',
                                  style: TextStyle(
                                    color: _attended ? const Color(0xFF6B7280) : Colors.white,
                                    fontWeight: FontWeight.w700, fontSize: 15,
                                  ),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // 친구 초대
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F0F18),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF1F1F2E)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Text('🎁 ', style: TextStyle(fontSize: 20)),
                          Text(
                            '친구 초대',
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '친구가 초대 코드로 가입하면 은화 3,000개를 드려요',
                        style: TextStyle(color: Color(0xFF6B7280), fontSize: 13),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: OutlinedButton(
                          onPressed: () async {
                            try {
                              final res = await ApiService.getReferralCode();
                              if (context.mounted) {
                                showDialog(
                                  context: context,
                                  builder: (_) => AlertDialog(
                                    backgroundColor: const Color(0xFF0F0F18),
                                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                    title: const Text('내 초대 코드', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                                    content: Text(
                                      res['code'] ?? '',
                                      style: const TextStyle(color: Color(0xFF7C6CFF), fontSize: 24, fontWeight: FontWeight.w800, letterSpacing: 4),
                                      textAlign: TextAlign.center,
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () => Navigator.pop(context),
                                        child: const Text('닫기', style: TextStyle(color: Color(0xFF6B7280))),
                                      ),
                                    ],
                                  ),
                                );
                              }
                            } catch (e) {
                              debugPrint('초대 코드 로드 실패: $e');
                            }
                          },
                          style: OutlinedButton.styleFrom(
                            side: const BorderSide(color: Color(0xFF7C6CFF)),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          ),
                          child: const Text(
                            '내 초대 코드 보기',
                            style: TextStyle(color: Color(0xFF7C6CFF), fontWeight: FontWeight.w700),
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