const _months = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'Mei',
  'Jun',
  'Jul',
  'Agu',
  'Sep',
  'Okt',
  'Nov',
  'Des',
];

String shortDate(Object? value) {
  final date = DateTime.tryParse('$value');
  if (date == null) return value == null ? '—' : '$value';
  return '${date.day} ${_months[date.month - 1]} ${date.year}';
}

String rangeLabel(Object? start, Object? end) {
  final first = DateTime.tryParse('$start');
  final last = DateTime.tryParse('$end');
  if (first == null || last == null) {
    return '${shortDate(start)} – ${shortDate(end)}';
  }
  final left = '${first.day} ${_months[first.month - 1]}';
  final right = first.year == last.year
      ? '${last.day} ${_months[last.month - 1]} ${last.year}'
      : shortDate(end);
  return '$left – $right';
}
