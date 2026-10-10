import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/auth/screens/welcome_screen.dart';

void main() {
  testWidgets('WelcomeScreen renders onboarding branding and action buttons', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: WelcomeScreen(),
      ),
    );

    // Verify Title and Subtitle render
    expect(find.textContaining('Take Control of'), findsOneWidget);
    expect(find.textContaining('Track income and expenses'), findsOneWidget);

    // Verify Login & Register buttons are present
    expect(find.byKey(const Key('welcome_login_button')), findsOneWidget);
    expect(find.byKey(const Key('welcome_register_button')), findsOneWidget);
    expect(find.text('Sign In'), findsOneWidget);
    expect(find.text('Create New Account'), findsOneWidget);

    // Verify Security badge
    expect(find.textContaining('Argon2 & JWT Security'), findsOneWidget);
  });
}
