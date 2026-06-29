import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:stellia_app/main.dart';

void main() {
  testWidgets('Stellia app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const StellaApp(initialToken: null));
    expect(find.text('Stellia'), findsWidgets);
  });
}