import 'package:flutter/material.dart';
import '../services/api_service.dart';

class TokenScreen extends StatefulWidget {
  const TokenScreen({super.key});

  @override
  State<TokenScreen> createState() => _TokenScreenState();
}

class _TokenScreenState extends State<TokenScreen> {
  Map<String, dynamic>? _coinData;
  List<dynamic> _history = [];
  bool _loading = true;
  bool _purchasing = false;
  String _message = '';

  final List<Map<String, dynamic>> _packages = [
    {'id': 1, 'price': 1900, 'token_amount': 2000, 'label': '2,000 금화'},
    {
      'id': 2,
      'price': 3800,
      'token_amount': 4200,
      'label': '4,200 금화',
      'bonus': '+200 보너스',
    },
    {
      'id': 3,
      'price': 9500,
      'token_amount': 11000,
      'label': '11,000 금화',
      'bonus': '+1,000 보너스',
    },
    {
      'id': 4,
      'price': 19000,
      'token_amount': 23000,
      'label': '23,000 금화',
      'bonus': '+3,000 보너스',
    },
  ];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final coin = await ApiService.getTokens();
      final history = await ApiService.getTokenHistory();
      setState(() {
        _coinData = coin;
        _history = history['items'] ?? [];
      });
    } catch (e) {
      debugPrint('토큰 로드 실패: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _purchase(int packageId) async {
    setState(() {
      _purchasing = true;
      _message = '';
    });
    try {
      final res = await ApiService.purchaseToken(packageId);
      setState(() => _message = res['message'] ?? '구매 완료!');
      await _loadData();
    } catch (e) {
      setState(() => _message = '구매에 실패했어요.');
    } finally {
      setState(() => _purchasing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: const Color(0xFF0A0A0F),
        appBar: AppBar(
          backgroundColor: const Color(0xFF0A0A0F),
          elevation: 0,
          title: const Text(
            '럭키 코인',
            style: TextStyle(
              color: Color(0xFFFFD700),
              fontWeight: FontWeight.w700,
            ),
          ),
          bottom: const TabBar(
            indicatorColor: Color(0xFF7C6CFF),
            labelColor: Colors.white,
            unselectedLabelColor: Color(0xFF6B7280),
            tabs: [
              Tab(text: '내 코인'),
              Tab(text: '충전소'),
              Tab(text: '메모리 패스'),
            ],
          ),
        ),
        body: _loading
            ? const Center(
                child: CircularProgressIndicator(color: Color(0xFF7C6CFF)),
              )
            : TabBarView(
                children: [
                  // 내 코인 탭
                  ListView(
                    padding: const EdgeInsets.all(20),
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [
                                    const Color(0xFFFFD700).withOpacity(0.18),
                                    const Color(0xFFFFD700).withOpacity(0.05),
                                  ],
                                ),
                                borderRadius: BorderRadius.circular(18),
                                border: Border.all(
                                  color: const Color(
                                    0xFFFFD700,
                                  ).withOpacity(0.3),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '🥇 금화',
                                    style: TextStyle(
                                      color: Color(0xFF6B7280),
                                      fontSize: 12,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    '${_coinData?['token_purchased'] ?? 0}',
                                    style: const TextStyle(
                                      color: Color(0xFFFFD700),
                                      fontWeight: FontWeight.w700,
                                      fontSize: 22,
                                    ),
                                  ),
                                  const Text(
                                    '만료 없음',
                                    style: TextStyle(
                                      color: Color(0xFF6B7280),
                                      fontSize: 11,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(18),
                              decoration: BoxDecoration(
                                color: const Color(0xFF0F0F18),
                                borderRadius: BorderRadius.circular(18),
                                border: Border.all(
                                  color: const Color(0xFF1F1F2E),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    '🥈 은화',
                                    style: TextStyle(
                                      color: Color(0xFF6B7280),
                                      fontSize: 12,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    '${_coinData?['token_event'] ?? 0}',
                                    style: const TextStyle(
                                      color: Color(0xFFC0C0C0),
                                      fontWeight: FontWeight.w700,
                                      fontSize: 22,
                                    ),
                                  ),
                                  const Text(
                                    '21일 만료',
                                    style: TextStyle(
                                      color: Color(0xFF6B7280),
                                      fontSize: 11,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 18,
                          vertical: 14,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F0F18),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFF1F1F2E)),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              '총 잔액',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 14,
                              ),
                            ),
                            Text(
                              '✦ ${_coinData?['token_balance'] ?? 0}',
                              style: const TextStyle(
                                color: Color(0xFFFFD700),
                                fontWeight: FontWeight.w700,
                                fontSize: 18,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        '토큰 내역',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ..._history.map(
                        (h) => Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0F0F18),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFF1F1F2E)),
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      h['reason'] ?? '',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w600,
                                        fontSize: 13,
                                      ),
                                    ),
                                    const SizedBox(height: 3),
                                    Text(
                                      h['created_at']?.toString().substring(
                                            0,
                                            10,
                                          ) ??
                                          '',
                                      style: const TextStyle(
                                        color: Color(0xFF6B7280),
                                        fontSize: 11,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Text(
                                '${h['amount'] > 0 ? '+' : ''}${h['amount']}',
                                style: TextStyle(
                                  color: h['amount'] > 0
                                      ? const Color(0xFF49D89A)
                                      : const Color(0xFFFF6B8A),
                                  fontWeight: FontWeight.w700,
                                  fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),

                  // 충전소 탭
                  ListView(
                    padding: const EdgeInsets.all(20),
                    children: [
                      if (_message.isNotEmpty)
                        Container(
                          margin: const EdgeInsets.only(bottom: 16),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFF49D89A).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: const Color(0xFF49D89A).withOpacity(0.3),
                            ),
                          ),
                          child: Text(
                            _message,
                            style: const TextStyle(
                              color: Color(0xFF49D89A),
                              fontSize: 13,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      const Text(
                        '※ 현재 테스트 모드 — 실제 결제 없이 지급',
                        style: TextStyle(
                          color: Color(0xFFFF6B8A),
                          fontSize: 12,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ..._packages.map(
                        (pkg) => GestureDetector(
                          onTap: _purchasing
                              ? null
                              : () => _purchase(pkg['id']),
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(18),
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  const Color(0xFFFFD700).withOpacity(0.08),
                                  const Color(0xFFFFD700).withOpacity(0.03),
                                ],
                              ),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: const Color(0xFFFFD700).withOpacity(0.3),
                              ),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '🥇 ${pkg['label']}',
                                        style: const TextStyle(
                                          color: Color(0xFFFFD700),
                                          fontWeight: FontWeight.w700,
                                          fontSize: 15,
                                        ),
                                      ),
                                      if (pkg['bonus'] != null)
                                        Text(
                                          pkg['bonus'],
                                          style: const TextStyle(
                                            color: Color(0xFF49D89A),
                                            fontSize: 12,
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 14,
                                    vertical: 8,
                                  ),
                                  decoration: BoxDecoration(
                                    color: const Color(
                                      0xFFFFD700,
                                    ).withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    '${pkg['price'].toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]},')}원',
                                    style: const TextStyle(
                                      color: Color(0xFFFFD700),
                                      fontWeight: FontWeight.w700,
                                      fontSize: 14,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),

                  // 메모리 패스 탭
                  ListView(
                    padding: const EdgeInsets.all(20),
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F0F18),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: const Color(0xFF7C6CFF).withOpacity(0.3),
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Text('🧠 ', style: TextStyle(fontSize: 28)),
                                SizedBox(width: 8),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '메모리 패스',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w700,
                                        fontSize: 16,
                                      ),
                                    ),
                                    Text(
                                      '비활성화',
                                      style: TextStyle(
                                        color: Color(0xFF6B7280),
                                        fontSize: 13,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              '• AI가 중요한 대화 내용을 자동으로 기억해요',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 13,
                                height: 1.7,
                              ),
                            ),
                            const Text(
                              '• 메모리 청크 최대 20개 저장',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 13,
                                height: 1.7,
                              ),
                            ),
                            const Text(
                              '• 장기 대화에서도 맥락을 유지해요',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 13,
                                height: 1.7,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F0F18),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFF1F1F2E)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '💳 현금 구매',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w700,
                                        fontSize: 15,
                                      ),
                                    ),
                                    Text(
                                      '30일권',
                                      style: TextStyle(
                                        color: Color(0xFF6B7280),
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                                Text(
                                  '9,900원',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 18,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            const Text(
                              '• 메모리 청크 20개',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 12,
                              ),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: () {},
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF1F1F2E),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                                child: const Text(
                                  '구매하기',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: const Color(0xFFFFD700).withOpacity(0.4),
                          ),
                          gradient: LinearGradient(
                            colors: [
                              const Color(0xFFFFD700).withOpacity(0.1),
                              const Color(0xFFFFD700).withOpacity(0.04),
                            ],
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '🥇 금화 구매',
                                      style: TextStyle(
                                        color: Color(0xFFFFD700),
                                        fontWeight: FontWeight.w700,
                                        fontSize: 15,
                                      ),
                                    ),
                                    Text(
                                      '30일권 + 보너스',
                                      style: TextStyle(
                                        color: Color(0xFF6B7280),
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '24,900 금화',
                                      style: TextStyle(
                                        color: Color(0xFFFFD700),
                                        fontWeight: FontWeight.w700,
                                        fontSize: 16,
                                      ),
                                    ),
                                    Text(
                                      '≈ 약 8,200원 상당',
                                      style: TextStyle(
                                        color: Color(0xFF49D89A),
                                        fontSize: 11,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 10),
                            const Text(
                              '• 메모리 청크 20개 기본',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 12,
                              ),
                            ),
                            const Text(
                              '• 보너스 청크 5개 추가 지급',
                              style: TextStyle(
                                color: Color(0xFF49D89A),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const Text(
                              '• 현금보다 약 17% 저렴',
                              style: TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 12,
                              ),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: () {},
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(
                                    0xFFFFD700,
                                  ).withOpacity(0.3),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                ),
                                child: const Text(
                                  '구매하기 + 청크 5개',
                                  style: TextStyle(
                                    color: Color(0xFFFFD700),
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
      ),
    );
  }
}
