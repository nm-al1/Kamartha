String formatRupiah(Object? value) {
  final text = value?.toString() ?? '';
  final amount = value is int ? value : int.tryParse(text);
  if (amount == null) return 'Rp—';
  final digits = amount.abs().toString();
  final grouped = StringBuffer();
  for (var index = 0; index < digits.length; index++) {
    if (index > 0 && (digits.length - index) % 3 == 0) grouped.write('.');
    grouped.write(digits[index]);
  }
  return '${amount < 0 ? '-' : ''}Rp$grouped';
}
