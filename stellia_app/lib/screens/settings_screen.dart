import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _user;
  bool _loading = true;
  String _outputLength = 'medium';
  bool _safetyMode = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final user = await ApiService.getMe();
      setState(() {
        _user = user;
        _outputLength = user['output_length'] ?? 'medium';
        _safetyMode = (user['safety_mode'] ?? 0) == 1;
      });
    } catch (e) {
      debugPrint('설정 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _saveOutputLength(String value) async {
    try {
      await ApiService.updateSettings({'output_length': value});
      setState(() => _outputLength = value);
    } catch (e) {
      debugPrint('설정 저장 실패: $e');
    }
  }

  Future<void> _saveSafetyMode(bool value) async {
    try {
      await ApiService.updateSettings({'safety_mode': value ? 1 : 0});
      setState(() => _safetyMode = value);
    } catch (e) {
      debugPrint('설정 저장 실패: $e');
    }
  }

  void _showChangeUsernameDialog() {
    final controller = TextEditingController(text: _user?['username'] ?? '');
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF0F0F18),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('닉네임 변경', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: '새 닉네임',
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
              final newName = controller.text.trim();
              if (newName.isEmpty) return;
              try {
                await ApiService.updateProfile(newName);
                setState(() => _user?['username'] = newName);
                if (mounted) Navigator.pop(context);
              } catch (e) {
                debugPrint('닉네임 변경 실패: $e');
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF7C6CFF),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('변경', style: TextStyle(color: Colors.white)),
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
        title: const Text('설정', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
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
                // 출력량 설정
                const Text('출력량 설정', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13, fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                ...[
                  {'value': 'short', 'label': '짧게', 'desc': '간결하고 빠른 응답', 'tokens': '300토큰/회'},
                  {'value': 'medium', 'label': '보통', 'desc': '적당한 길이의 응답', 'tokens': '1,000토큰/회'},
                  {'value': 'long', 'label': '길게', 'desc': '상세하고 풍부한 응답', 'tokens': '2,000토큰/회'},
                ].map((opt) => GestureDetector(
                  onTap: () => _saveOutputLength(opt['value']!),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: _outputLength == opt['value']
                          ? const Color(0xFF7C6CFF).withOpacity(0.12)
                          : const Color(0xFF0F0F18),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: _outputLength == opt['value']
                            ? const Color(0xFF7C6CFF)
                            : const Color(0xFF1F1F2E),
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                opt['label']!,
                                style: TextStyle(
                                  color: _outputLength == opt['value']
                                      ? const Color(0xFF7C6CFF)
                                      : Colors.white,
                                  fontWeight: FontWeight.w700, fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(opt['desc']!, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12)),
                            ],
                          ),
                        ),
                        Text(opt['tokens']!, style: const TextStyle(color: Color(0xFFFFD700), fontSize: 12)),
                      ],
                    ),
                  ),
                )),

                const SizedBox(height: 24),

                // 안전 모드
                const Text('콘텐츠 설정', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13, fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F0F18),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFF1F1F2E)),
                  ),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('안전 모드', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                            SizedBox(height: 2),
                            Text('성인 콘텐츠를 필터링해요', style: TextStyle(color: Color(0xFF6B7280), fontSize: 12)),
                          ],
                        ),
                      ),
                      Switch(
                        value: _safetyMode,
                        onChanged: _saveSafetyMode,
                        activeColor: const Color(0xFF7C6CFF),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // 계정 정보
                const Text('계정', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13, fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F0F18),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFF1F1F2E)),
                  ),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          const Text('이메일', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                          const Spacer(),
                          Text(_user?['email'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 13)),
                        ],
                      ),
                      const SizedBox(height: 10),
                      const Divider(color: Color(0xFF1F1F2E)),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          const Text('닉네임', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                          const Spacer(),
                          Text(_user?['username'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 13)),
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: _showChangeUsernameDialog,
                            child: const Text('변경', style: TextStyle(color: Color(0xFF7C6CFF), fontSize: 13, fontWeight: FontWeight.w600)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // 앱 정보
                const Text('앱 정보', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13, fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F0F18),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFF1F1F2E)),
                  ),
                  child: const Column(
                    children: [
                      Row(
                        children: [
                          Text('버전', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                          Spacer(),
                          Text('0.1.0 (CBT)', style: TextStyle(color: Colors.white, fontSize: 13)),
                        ],
                      ),
                      SizedBox(height: 10),
                      Divider(color: Color(0xFF1F1F2E)),
                      SizedBox(height: 10),
                      Row(
                        children: [
                          Text('개발', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                          Spacer(),
                          Text('Stellia Team', style: TextStyle(color: Colors.white, fontSize: 13)),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}