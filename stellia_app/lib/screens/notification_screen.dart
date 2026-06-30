import 'package:flutter/material.dart';
import '../services/api_service.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  List<dynamic> _notifications = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    try {
      final data = await ApiService.getNotifications();
      setState(() => _notifications = data);
    } catch (e) {
      debugPrint('알림 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  IconData _getIcon(String type) {
    switch (type) {
      case 'community_tag': return Icons.local_offer_rounded;
      case 'community_comment': return Icons.chat_bubble_rounded;
      case 'new_character': return Icons.star_rounded;
      case 'token_low': return Icons.warning_rounded;
      case 'token_empty': return Icons.error_rounded;
      default: return Icons.notifications_rounded;
    }
  }

  Color _getColor(String type) {
    switch (type) {
      case 'community_tag': return const Color(0xFF5FD6FF);
      case 'community_comment': return const Color(0xFF7C6CFF);
      case 'new_character': return const Color(0xFFFFD700);
      case 'token_low':
      case 'token_empty': return const Color(0xFFFF6B8A);
      default: return const Color(0xFF6B7280);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text('알림', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
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
              onRefresh: _loadNotifications,
              child: _notifications.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.notifications_off_rounded, color: Color(0xFF6B7280), size: 60),
                          SizedBox(height: 16),
                          Text('알림이 없어요.', style: TextStyle(color: Color(0xFF6B7280), fontSize: 15)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _notifications.length,
                      itemBuilder: (context, i) {
                        final n = _notifications[i];
                        final isRead = n['is_read'] == 1;
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: isRead ? const Color(0xFF0F0F18) : const Color(0xFF7C6CFF).withOpacity(0.08),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: isRead ? const Color(0xFF1F1F2E) : const Color(0xFF7C6CFF).withOpacity(0.3),
                            ),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 40, height: 40,
                                decoration: BoxDecoration(
                                  color: _getColor(n['type'] ?? '').withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Icon(_getIcon(n['type'] ?? ''), color: _getColor(n['type'] ?? ''), size: 20),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      n['title'] ?? '',
                                      style: TextStyle(
                                        color: isRead ? Colors.white70 : Colors.white,
                                        fontWeight: FontWeight.w600, fontSize: 14,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      n['message'] ?? '',
                                      style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13, height: 1.4),
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      n['created_at']?.toString().substring(0, 10) ?? '',
                                      style: const TextStyle(color: Color(0xFF6B7280), fontSize: 11),
                                    ),
                                  ],
                                ),
                              ),
                              if (!isRead)
                                Container(
                                  width: 8, height: 8,
                                  decoration: const BoxDecoration(
                                    color: Color(0xFF7C6CFF),
                                    shape: BoxShape.circle,
                                  ),
                                ),
                            ],
                          ),
                        );
                      },
                    ),
    ));
  }
}
