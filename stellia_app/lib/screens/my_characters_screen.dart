import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/character.dart';
import 'character_profile_screen.dart';

class MyCharactersScreen extends StatefulWidget {
  const MyCharactersScreen({super.key});

  @override
  State<MyCharactersScreen> createState() => _MyCharactersScreenState();
}

class _MyCharactersScreenState extends State<MyCharactersScreen> {
  List<Character> _characters = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ApiService.getMyCharacters();
      setState(() => _characters = data.map((e) => Character.fromJson(e)).toList());
    } catch (e) {
      debugPrint('내 캐릭터 로드 실패: $e');
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
        title: const Text('내 캐릭터', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        bottom: PreferredSize(preferredSize: const Size.fromHeight(1), child: Container(color: const Color(0xFF1F1F2E), height: 1)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C6CFF)))
          : _characters.isEmpty
              ? const Center(child: Text('아직 만든 캐릭터가 없어요.', style: TextStyle(color: Color(0xFF6B7280))))
              : RefreshIndicator(
                  color: const Color(0xFF7C6CFF),
                  backgroundColor: const Color(0xFF0F0F18),
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _characters.length,
                    itemBuilder: (context, i) {
                      final char = _characters[i];
                      return GestureDetector(
                        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => CharacterProfileScreen(character: char))),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0F0F18),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: const Color(0xFF1F1F2E)),
                          ),
                          child: Row(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: char.imageUrl.isNotEmpty
                                    ? Image.network(char.imageUrl, width: 56, height: 56, fit: BoxFit.cover, errorBuilder: (_, __, ___) => _placeholder(char.name))
                                    : _placeholder(char.name),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(char.name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15)),
                                    const SizedBox(height: 4),
                                    Text(char.description, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 13), maxLines: 1, overflow: TextOverflow.ellipsis),
                                    const SizedBox(height: 6),
                                    Row(
                                      children: [
                                        const Icon(Icons.favorite_rounded, color: Color(0xFFFF6B8A), size: 12),
                                        const SizedBox(width: 4),
                                        Text('${char.likeCount}', style: const TextStyle(color: Color(0xFFFF6B8A), fontSize: 12)),
                                        const SizedBox(width: 12),
                                        const Icon(Icons.chat_bubble_rounded, color: Color(0xFF5FD6FF), size: 12),
                                        const SizedBox(width: 4),
                                        Text('${char.chatCount}', style: const TextStyle(color: Color(0xFF5FD6FF), fontSize: 12)),
                                      ],
                                    ),
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
                ),
    );
  }

  Widget _placeholder(String name) => Container(
    width: 56, height: 56,
    decoration: BoxDecoration(
      gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Center(child: Text(name[0], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 22))),
  );
}