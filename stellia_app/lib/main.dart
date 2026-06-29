import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('access_token');
  runApp(StellaApp(initialToken: token));
}

class StellaApp extends StatelessWidget {
  final String? initialToken;
  const StellaApp({super.key, this.initialToken});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Stellia',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0A0F),
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF7C6CFF),
          secondary: const Color(0xFF5FD6FF),
          surface: const Color(0xFF0F0F18),
        ),
        fontFamily: 'pretendard',
        useMaterial3: true,
      ),
      home: initialToken != null
          ? const HomeScreen()
          : const LoginScreen(),
    );
  }
}