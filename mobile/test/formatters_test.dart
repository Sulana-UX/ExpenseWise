import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/utils/formatters.dart';

void main() {
  group('Formatters Unit Tests', () {
    test('formatCurrency formats Sri Lankan Rupees with standard comma separation', () {
      expect(Formatters.formatCurrency(0), 'Rs. 0.00');
      expect(Formatters.formatCurrency(500), 'Rs. 500.00');
      expect(Formatters.formatCurrency(12500.5), 'Rs. 12,500.50');
      expect(Formatters.formatCurrency(1000000), 'Rs. 1,000,000.00');
      expect(Formatters.formatCurrency(null), 'Rs. 0.00');
      expect(Formatters.formatCurrency("4500.75"), 'Rs. 4,500.75');
    });

    test('formatPercentage formats decimal percentages with 1 decimal place', () {
      expect(Formatters.formatPercentage(0), '0.0%');
      expect(Formatters.formatPercentage(85.456), '85.5%');
      expect(Formatters.formatPercentage(100), '100.0%');
      expect(Formatters.formatPercentage(null), '0.00%');
    });

    test('formatMonthYear formats year and month accurately', () {
      expect(Formatters.formatMonthYear(2026, 10), 'October 2026');
      expect(Formatters.formatShortMonth(2026, 10), 'Oct 2026');
    });
  });
}
