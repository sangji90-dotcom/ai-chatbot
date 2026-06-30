import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/character.dart';
import 'character_profile_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _controller = TextEditingController();
  List<Character> _results = [];
  bool _loading = false;
  bool _searched = false;

  Future<void> _search(String q) async {
    if (q.trim().isEmpty) return;
    setState(() { _loading = true; _searched = true; });
    try {
      final data = await ApiService.searchCharacters(q);
      setState(() => _results = data.map((e) => Character.fromJson(e)).toList());
    } catch (e) {
      debugPrint('검색 실패: $e');
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
        title: TextField(
          controller: _controller,
          autofocus: true,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: '캐릭터 검색...',
            hintStyle: const TextStyle(color: Color(0xFF6B7280)),
            border: InputBorder.none,
            suffixIcon: IconButton(
              icon: const Icon(Icons.search_rounded, color: Color(0xFF7C6CFF)),
              onPressed: () => _search(_controller.text),
            ),
          ),
          onSubmitted: _search,
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C6CFF)))
          : !_searched
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.search_rounded, color: Color(0xFF6B7280), size: 60),
                      SizedBox(height: 16),
                      Text('캐릭터를 검색해보세요', style: TextStyle(color: Color(0xFF6B7280), fontSize: 15)),
                    ],
                  ),
                )
              : _results.isEmpty
                  ? const Center(
                      child: Text('검색 결과가 없어요.', style: TextStyle(color: Color(0xFF6B7280))),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _results.length,
                      itemBuilder: (context, i) {
                        final char = _results[i];
                        return GestureDetector(
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => CharacterProfileScreen(character: char)),
                          ),
                          child: Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0F0F18),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFF1F1F2E)),
                            ),
                            child: Row(
                              children: [
                                ClipRRect(
                                  borderRadius: BorderRadius.circular(10),
                                  child: char.imageUrl.isNotEmpty
                                      ? Image.network(char.imageUrl, width: 52, height: 52, fit: BoxFit.cover,
                                          errorBuilder: (_, __, ___) => _placeholder(char.name))
                                      : _placeholder(char.name),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(char.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                                      const SizedBox(height: 4),
                                      Text(char.description, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13), maxLines: 1, overflow: TextOverflow.ellipsis),
                                    ],
                                  ),
                                ),
                                const Icon(Icons.chevron_right_rounded, color: Color(0xFF6B7280)),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
    );
  }

  Widget _placeholder(String name) => Container(
    width: 52, height: 52,
    decoration: BoxDecoration(
      gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
      borderRadius: BorderRadius.circular(10),
    ),
    child: Center(child: Text(name[0], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 20))),
  );
}