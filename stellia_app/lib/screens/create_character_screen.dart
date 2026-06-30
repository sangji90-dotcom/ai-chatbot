import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';

class CreateCharacterScreen extends StatefulWidget {
  const CreateCharacterScreen({super.key});

  @override
  State<CreateCharacterScreen> createState() => _CreateCharacterScreenState();
}

class _CreateCharacterScreenState extends State<CreateCharacterScreen> {
  int _currentStep = 0;
  bool _loading = false;
  String _message = '';

  // 폼 데이터
  final _nameController = TextEditingController();
  final _descController = TextEditingController();
  final _personalityController = TextEditingController();
  final _likesController = TextEditingController();
  final _dislikesController = TextEditingController();
  final _speechController = TextEditingController();
  final _firstMessageController = TextEditingController();
  final _situationController = TextEditingController();
  int _age = 20;
  String _job = '';
  String _visibility = 'public';
  int _isAdult = 0;
  bool _aiLoading = false;
  File? _selectedImage;

  Future<void> _autoComplete() async {
    if (_nameController.text.isEmpty) return;
    setState(() => _aiLoading = true);
    try {
      final res = await ApiService.autoComplete(
        name: _nameController.text,
        description: _descController.text,
        job: _job,
        age: _age,
      );
      setState(() {
        if (res['personality'] != null) _personalityController.text = res['personality'];
        if (res['speech_style'] != null) _speechController.text = res['speech_style'];
        if (res['likes'] != null) _likesController.text = res['likes'];
        if (res['dislikes'] != null) _dislikesController.text = res['dislikes'];
        if (res['first_message'] != null) _firstMessageController.text = res['first_message'];
        if (res['situation'] != null) _situationController.text = res['situation'];
      });
    } catch (e) {
      setState(() => _message = 'AI 자동완성에 실패했어요.');
    } finally {
      setState(() => _aiLoading = false);
    }
  }

  Future<void> _submit() async {
    if (_nameController.text.isEmpty || _personalityController.text.isEmpty || _speechController.text.isEmpty) {
      setState(() => _message = '이름, 성격, 말투는 필수예요.');
      return;
    }
  setState(() { _loading = true; _message = ''; });
    try {
      final res = await ApiService.createCharacter(
        name: _nameController.text,
        description: _descController.text,
        age: _age,
        job: _job,
        personality: _personalityController.text,
        likes: _likesController.text,
        dislikes: _dislikesController.text,
        speechStyle: _speechController.text,
        firstMessage: _firstMessageController.text,
        situation: _situationController.text,
      visibility: _visibility,
        isAdult: _isAdult,
      );

      if (_selectedImage != null) {
        await ApiService.uploadCharacterImage(res['id'], _selectedImage!);
      }

      if (mounted) {
        Navigator.pop(context);
      }
    } catch (e) {
      setState(() => _message = '캐릭터 생성에 실패했어요.');
    } finally {
      setState(() => _loading = false);
    }
  }

  InputDecoration _inputDeco(String hint) => InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: Color(0xFF6B7280)),
    filled: true,
    fillColor: const Color(0xFF0F0F18),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1F1F2E))),
    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF7C6CFF))),
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0F),
        elevation: 0,
        title: const Text('캐릭터 만들기', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: const Color(0xFF1F1F2E), height: 1),
        ),
      ),
      body: Column(
        children: [
          // 스텝 인디케이터
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: List.generate(3, (i) => Expanded(
                child: Container(
                  margin: EdgeInsets.only(right: i < 2 ? 8 : 0),
                  height: 4,
                  decoration: BoxDecoration(
                    gradient: i <= _currentStep ? const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]) : null,
                    color: i <= _currentStep ? null : const Color(0xFF1F1F2E),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              )),
            ),
          ),

          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_message.isNotEmpty)
                    Container(
                      margin: const EdgeInsets.only(bottom: 16),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFF6B8A).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFFF6B8A).withOpacity(0.3)),
                      ),
                      child: Text(_message, style: const TextStyle(color: Color(0xFFFF6B8A), fontSize: 13)),
                    ),

                  // Step 0: 프로필
                  if (_currentStep == 0) ...[
                    const Text('기본 정보', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
                    const SizedBox(height: 20),
                    Center(
                      child: GestureDetector(
                        onTap: () async {
                          final picker = ImagePicker();
                          final picked = await picker.pickImage(source: ImageSource.gallery);
                          if (picked != null) {
                            setState(() => _selectedImage = File(picked.path));
                          }
                        },
                        child: Container(
                          width: 100, height: 100,
                          decoration: BoxDecoration(
                            gradient: _selectedImage == null
                                ? const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)])
                                : null,
                            borderRadius: BorderRadius.circular(50),
                            image: _selectedImage != null
                                ? DecorationImage(image: FileImage(_selectedImage!), fit: BoxFit.cover)
                                : null,
                          ),
                          child: _selectedImage == null
                              ? const Icon(Icons.add_a_photo_rounded, color: Colors.white, size: 32)
                              : null,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Center(
                    child: Text('대표 이미지', style: TextStyle(color: Color(0xFF6B7280), fontSize: 12)),
                  ),
                  const SizedBox(height: 20),
                    const Text('이름 *', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _nameController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('캐릭터 이름')),
                    const SizedBox(height: 16),
                    const Text('소개', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _descController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('캐릭터 소개'), maxLines: 3),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('나이', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                              const SizedBox(height: 8),
                              TextField(
                                style: const TextStyle(color: Colors.white),
                                decoration: _inputDeco('20'),
                                keyboardType: TextInputType.number,
                                onChanged: (v) => _age = int.tryParse(v) ?? 20,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('직업', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                              const SizedBox(height: 8),
                              TextField(
                                style: const TextStyle(color: Colors.white),
                                decoration: _inputDeco('예: 대학생'),
                                onChanged: (v) => _job = v,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],

                  // Step 1: 상세정보
                  if (_currentStep == 1) ...[
                    const Text('상세 정보', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
                    const SizedBox(height: 16),
                    // AI 자동완성
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: OutlinedButton(
                        onPressed: _aiLoading ? null : _autoComplete,
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: Color(0xFFFFD700)),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        child: _aiLoading
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Color(0xFFFFD700), strokeWidth: 2))
                            : const Text('✦ AI 자동완성', style: TextStyle(color: Color(0xFFFFD700), fontWeight: FontWeight.w700)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text('성격 *', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _personalityController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('성격을 입력해주세요'), maxLines: 4),
                    const SizedBox(height: 16),
                    const Text('좋아하는 것', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _likesController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('예: 커피, 독서')),
                    const SizedBox(height: 16),
                    const Text('싫어하는 것', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _dislikesController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('예: 거짓말')),
                    const SizedBox(height: 16),
                    const Text('말투 *', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _speechController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('말투를 입력해주세요'), maxLines: 3),
                  ],

                  // Step 2: 설정
                  if (_currentStep == 2) ...[
                    const Text('시작 설정', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18)),
                    const SizedBox(height: 16),
                    const Text('첫 대사', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _firstMessageController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('캐릭터가 처음 건네는 말'), maxLines: 3),
                    const SizedBox(height: 16),
                    const Text('시작 상황', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    TextField(controller: _situationController, style: const TextStyle(color: Colors.white), decoration: _inputDeco('첫 만남 상황'), maxLines: 3),
                    const SizedBox(height: 20),
                    const Text('공개 범위', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _visibility = 'public'),
                            child: Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: _visibility == 'public' ? const Color(0xFF7C6CFF).withOpacity(0.12) : const Color(0xFF0F0F18),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: _visibility == 'public' ? const Color(0xFF7C6CFF) : const Color(0xFF1F1F2E)),
                              ),
                              child: Text('🟢 공개', style: TextStyle(color: _visibility == 'public' ? const Color(0xFF7C6CFF) : const Color(0xFF6B7280), fontWeight: FontWeight.w600), textAlign: TextAlign.center),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _visibility = 'private'),
                            child: Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: _visibility == 'private' ? const Color(0xFF7C6CFF).withOpacity(0.12) : const Color(0xFF0F0F18),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: _visibility == 'private' ? const Color(0xFF7C6CFF) : const Color(0xFF1F1F2E)),
                              ),
                              child: Text('🔒 비공개', style: TextStyle(color: _visibility == 'private' ? const Color(0xFF7C6CFF) : const Color(0xFF6B7280), fontWeight: FontWeight.w600), textAlign: TextAlign.center),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    const Text('이용 제한', style: TextStyle(color: Color(0xFF6B7280), fontSize: 13)),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _isAdult = 0),
                            child: Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: _isAdult == 0 ? const Color(0xFF7C6CFF).withOpacity(0.12) : const Color(0xFF0F0F18),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: _isAdult == 0 ? const Color(0xFF7C6CFF) : const Color(0xFF1F1F2E)),
                              ),
                              child: Text('전체 이용가', style: TextStyle(color: _isAdult == 0 ? const Color(0xFF7C6CFF) : const Color(0xFF6B7280), fontWeight: FontWeight.w600), textAlign: TextAlign.center),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() => _isAdult = 1),
                            child: Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: _isAdult == 1 ? const Color(0xFF7C6CFF).withOpacity(0.12) : const Color(0xFF0F0F18),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(color: _isAdult == 1 ? const Color(0xFF7C6CFF) : const Color(0xFF1F1F2E)),
                              ),
                              child: Text('🔞 성인 전용', style: TextStyle(color: _isAdult == 1 ? const Color(0xFF7C6CFF) : const Color(0xFF6B7280), fontWeight: FontWeight.w600), textAlign: TextAlign.center),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),

          // 하단 버튼
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                if (_currentStep > 0)
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => setState(() => _currentStep--),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Color(0xFF1F1F2E)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: const Text('이전', style: TextStyle(color: Color(0xFF6B7280), fontWeight: FontWeight.w600)),
                    ),
                  ),
                if (_currentStep > 0) const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: SizedBox(
                    height: 52,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)]),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: ElevatedButton(
                        onPressed: _loading ? null : () {
                          if (_currentStep < 2) {
                            setState(() => _currentStep++);
                          } else {
                            _submit();
                          }
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        ),
                        child: _loading
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                            : Text(
                                _currentStep < 2 ? '다음 →' : '캐릭터 생성',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16),
                              ),
                      ),
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