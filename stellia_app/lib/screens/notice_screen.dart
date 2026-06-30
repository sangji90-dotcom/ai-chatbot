import 'package:flutter/material.dart';
import '../services/api_service.dart';

class NoticeScreen extends StatefulWidget {
  const NoticeScreen({super.key});

  @override
  State<NoticeScreen> createState() => _NoticeScreenState();
}

class _NoticeScreenState extends State<NoticeScreen> {
  List<dynamic> _notices = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadNotices();
  }

  Future<void> _loadNotices() async {
    try {
      final data = await ApiService.getNotices();
      setState(() => _notices = data);
    } catch (e) {
      debugPrint('공지 로드 실패: $e');
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
        title: const Text('공지사항', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
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
              onRefresh: _loadNotices,
              child: _notices.isEmpty
                  ? const Center(
                      child: Text('공지사항이 없어요.', style: TextStyle(color: Color(0xFF6B7280))),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _notices.length,
                      itemBuilder: (context, i) {
                        final notice = _notices[i];
                        final isPinned = notice['is_pinned'] == 1;
                        return GestureDetector(
                          onTap: () => _showDetail(notice),
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 8),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: isPinned
                                  ? const Color(0xFF7C6CFF).withOpacity(0.08)
                                  : const Color(0xFF0F0F18),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: isPinned
                                    ? const Color(0xFF7C6CFF).withOpacity(0.3)
                                    : const Color(0xFF1F1F2E),
                              ),
                            ),
                            child: Row(
                              children: [
                                if (isPinned)
                                  const Padding(
                                    padding: EdgeInsets.only(right: 8),
                                    child: Icon(Icons.push_pin_rounded, color: Color(0xFF7C6CFF), size: 16),
                                  ),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        notice['title'] ?? '',
                                        style: TextStyle(
                                          color: isPinned ? Colors.white : Colors.white70,
                                          fontWeight: isPinned ? FontWeight.w700 : FontWeight.w600,
                                          fontSize: 14,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        notice['created_at']?.toString().substring(0, 10) ?? '',
                                        style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12),
                                      ),
                                    ],
                                  ),
                                ),
                                const Icon(Icons.chevron_right_rounded, color: Color(0xFF6B7280), size: 18),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
    );
  }

  void _showDetail(Map<String, dynamic> notice) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F0F18),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      isScrollControlled: true,
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        builder: (_, controller) => Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1F1F2E),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                notice['title'] ?? '',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18),
              ),
              const SizedBox(height: 8),
              Text(
                notice['created_at']?.toString().substring(0, 10) ?? '',
                style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13),
              ),
              const SizedBox(height: 16),
              const Divider(color: Color(0xFF1F1F2E)),
              const SizedBox(height: 16),
              Expanded(
                child: SingleChildScrollView(
                  controller: controller,
                  child: Text(
                    notice['content'] ?? '',
                    style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.7),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}