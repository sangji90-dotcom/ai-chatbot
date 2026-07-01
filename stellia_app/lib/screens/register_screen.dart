import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _emailController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordConfirmController = TextEditingController();
  bool _loading = false;
  String? _error;

  Future<void> _register() async {
    if (_passwordController.text != _passwordConfirmController.text) {
      setState(() => _error = '비밀번호가 일치하지 않아요.');
      return;
    }
    setState(() { _loading = true; _error = null; });
    try {
      final dio = Dio(BaseOptions(baseUrl: ApiService.baseUrl));
      final res = await dio.post('/auth/register', data: {
        'email': _emailController.text.trim(),
        'username': _usernameController.text.trim(),
        'password': _passwordController.text.trim(),
      });
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', res.data['access_token']);
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const HomeScreen()),
        );
      }
    } on DioException catch (e) {
      setState(() => _error = e.response?.data['detail'] ?? '회원가입에 실패했어요.');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment.topCenter,
            radius: 1.5,
            colors: [Color(0xFF1A0F3C), Color(0xFF0A0A0F)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // 뒤로가기
                  Align(
                    alignment: Alignment.centerLeft,
                    child: GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F0F18),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF1F1F2E)),
                        ),
                        child: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 20),
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),

                  // 로고
                  ShaderMask(
                    shaderCallback: (bounds) => const LinearGradient(
                      colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                    ).createShader(bounds),
                    child: const Text(
                      'Stellia',
                      style: TextStyle(
                        fontSize: 48, fontWeight: FontWeight.w800,
                        color: Colors.white, letterSpacing: -1,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '새로운 세계로의 첫 걸음',
                    style: TextStyle(color: Color(0xFF6B7280), fontSize: 14),
                  ),
                  const SizedBox(height: 40),

                  // 이메일
                  _InputField(controller: _emailController, hint: '이메일', keyboardType: TextInputType.emailAddress),
                  const SizedBox(height: 12),

                  // 닉네임
                  _InputField(controller: _usernameController, hint: '닉네임'),
                  const SizedBox(height: 12),

                  // 비밀번호
                  _InputField(controller: _passwordController, hint: '비밀번호', obscure: true),
                  const SizedBox(height: 12),

                  // 비밀번호 확인
                  _InputField(controller: _passwordConfirmController, hint: '비밀번호 확인', obscure: true),
                  const SizedBox(height: 16),

                  // 에러
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(_error!, style: const TextStyle(color: Color(0xFFFF6B8A), fontSize: 13)),
                    ),

                  // 회원가입 버튼
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF7C6CFF), Color(0xFF5FD6FF)],
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ElevatedButton(
                        onPressed: _loading ? null : _register,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        child: _loading
                            ? const SizedBox(
                                width: 20, height: 20,
                                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                              )
                            : const Text(
                                '회원가입',
                                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white),
                              ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _InputField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final bool obscure;
  final TextInputType? keyboardType;

  const _InputField({
    required this.controller,
    required this.hint,
    this.obscure = false,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      keyboardType: keyboardType ?? TextInputType.text,
      style: const TextStyle(color: Colors.white, fontSize: 15),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: Color(0xFF6B7280)),
        filled: true,
        fillColor: const Color(0xFF0F0F18),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFF1F1F2E)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFF1F1F2E)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFF7C6CFF)),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      ),
    );
  }
}