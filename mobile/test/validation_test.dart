import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Input Validation Logic Tests', () {
    test('Email validator accepts valid emails and rejects invalid ones', () {
      bool isValidEmail(String email) {
        return email.contains('@') && email.contains('.') && email.trim().length >= 5;
      }

      expect(isValidEmail('student@university.ac.lk'), isTrue);
      expect(isValidEmail('user.name@example.com'), isTrue);
      expect(isValidEmail('invalid-email'), isFalse);
      expect(isValidEmail('plainaddress'), isFalse);
      expect(isValidEmail(''), isFalse);
    });

    test('Password complexity validator enforces 8+ chars with digits and letters', () {
      bool isStrongPassword(String pwd) {
        if (pwd.length < 8) return false;
        final hasDigit = pwd.contains(RegExp(r'[0-9]'));
        final hasLetter = pwd.contains(RegExp(r'[a-zA-Z]'));
        return hasDigit && hasLetter;
      }

      expect(isStrongPassword('SecurePass123'), isTrue);
      expect(isStrongPassword('p@ssw0rd1'), isTrue);
      expect(isStrongPassword('short1'), isFalse); // < 8 chars
      expect(isStrongPassword('onlylettershere'), isFalse); // no numbers
      expect(isStrongPassword('1234567890'), isFalse); // no letters
    });

    test('Transaction amount validator rejects 0 and negative amounts', () {
      bool isValidAmount(dynamic amt) {
        final val = double.tryParse(amt.toString());
        return val != null && val > 0;
      }

      expect(isValidAmount(100.50), isTrue);
      expect(isValidAmount("5000"), isTrue);
      expect(isValidAmount(0), isFalse);
      expect(isValidAmount(-250), isFalse);
      expect(isValidAmount("invalid"), isFalse);
    });
  });
}
