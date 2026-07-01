import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AchievementsScreen extends StatefulWidget {
  const AchievementsScreen({super.key});

  @override
  State<AchievementsScreen> createState() => _AchievementsScreenState();
}

class _AchievementsScreenState extends State<AchievementsScreen> {
  List<dynamic> _achievements = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ApiService.getAchievements();
      setState(() => _achievements = data);
    } catch (e) {
      debugPrint('업적 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text(
          '업적',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: Color(0xFF7C6CFF)),
            )
          : _achievements.isEmpty
          ? const Center(
              child: Text(
                '아직 획득한 업적이 없어요.',
                style: TextStyle(color: Color(0xFF6B7280)),
              ),
            )
          : RefreshIndicator(
              color: const Color(0xFF7C6CFF),
              backgroundColor: const Color(0xFF0F0F18),
              onRefresh: _load,
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _achievements.length,
                itemBuilder: (context, i) {
                  final a = _achievements[i];
                  final isUnlocked = a['achieved'] == true;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: isUnlocked
                          ? const Color(0xFF7C6CFF).withOpacity(0.08)
                          : const Color(0xFF0F0F18),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isUnlocked
                            ? const Color(0xFF7C6CFF).withOpacity(0.3)
                            : const Color(0xFF1F1F2E),
                      ),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: isUnlocked
                                ? const Color(0xFF7C6CFF).withOpacity(0.2)
                                : const Color(0xFF1F1F2E),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Center(
                            child: Text(
                              a['icon'] ?? '🏆',
                              style: TextStyle(
                                fontSize: 24,
                                color: isUnlocked ? null : Colors.grey,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                a['name'] ?? '',
                                style: TextStyle(
                                  color: isUnlocked
                                      ? Colors.white
                                      : const Color(0xFF6B7280),
                                  fontWeight: FontWeight.w700,
                                  fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                a['description'] ?? '',
                                style: const TextStyle(
                                  color: Color(0xFF6B7280),
                                  fontSize: 12,
                                ),
                              ),
                              if (isUnlocked && a['achieved_at'] != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    a['achieved_at'].toString().substring(
                                      0,
                                      10,
                                    ),
                                    style: const TextStyle(
                                      color: Color(0xFF7C6CFF),
                                      fontSize: 11,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                        if (isUnlocked)
                          const Icon(
                            Icons.check_circle_rounded,
                            color: Color(0xFF7C6CFF),
                            size: 20,
                          )
                        else
                          const Icon(
                            Icons.lock_rounded,
                            color: Color(0xFF6B7280),
                            size: 20,
                          ),
                      ],
                    ),
                  );
                },
              ),
            ),
    );
  }
}
