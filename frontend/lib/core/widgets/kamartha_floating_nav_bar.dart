import 'package:flutter/material.dart';

import '../../app/theme/kamartha_theme.dart';

class KamarthaFloatingNavBar extends StatelessWidget {
  const KamarthaFloatingNavBar({
    super.key,
    required this.selectedIndex,
    required this.onSelected,
  });
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  static const labels = ['Beranda', 'Kamar', 'Tagihan', 'Menu'];

  @override
  Widget build(BuildContext context) => SafeArea(
    top: false,
    child: Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(32),
          boxShadow: const [
            BoxShadow(
              color: Color(0x1F142039),
              blurRadius: 16,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(32),
          clipBehavior: Clip.antiAlias,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 64),
            child: IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (var index = 0; index < labels.length; index++)
                    Expanded(
                      child: Semantics(
                        selected: selectedIndex == index,
                        button: true,
                        label: labels[index],
                        child: InkWell(
                          onTap: () => onSelected(index),
                          focusColor: KamarthaColors.chip,
                          hoverColor: Colors.transparent,
                          child: ExcludeSemantics(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 3,
                                vertical: 8,
                              ),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  CustomPaint(
                                    size: const Size(24, 24),
                                    painter: _NavPainter(
                                      index,
                                      selectedIndex == index,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    labels[index],
                                    textAlign: TextAlign.center,
                                    softWrap: true,
                                    style: TextStyle(
                                      fontSize: 13,
                                      height: 1.2,
                                      fontWeight: selectedIndex == index
                                          ? FontWeight.w600
                                          : FontWeight.w500,
                                      color: selectedIndex == index
                                          ? KamarthaColors.primary
                                          : KamarthaColors.secondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
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
    ),
  );
}

class _NavPainter extends CustomPainter {
  const _NavPainter(this.index, this.selected);
  final int index;
  final bool selected;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = selected ? KamarthaColors.primary : KamarthaColors.secondary
      ..style = PaintingStyle.stroke
      ..strokeWidth = selected ? 2.2 : 1.8
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    if (index == 0) {
      final house = Path()
        ..moveTo(3, 10)
        ..lineTo(12, 2)
        ..lineTo(21, 10)
        ..lineTo(21, 22)
        ..lineTo(15, 22)
        ..lineTo(15, 14)
        ..lineTo(9, 14)
        ..lineTo(9, 22)
        ..lineTo(3, 22)
        ..close();
      if (selected) paint.style = PaintingStyle.fill;
      canvas.drawPath(house, paint);
    } else if (index == 1) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(3, 3, 18, 10),
          const Radius.circular(3),
        ),
        paint,
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(2, 10, 20, 9),
          const Radius.circular(2),
        ),
        paint,
      );
      canvas.drawLine(const Offset(2, 16), const Offset(22, 16), paint);
      canvas.drawLine(const Offset(3, 19), const Offset(3, 22), paint);
      canvas.drawLine(const Offset(21, 19), const Offset(21, 22), paint);
    } else if (index == 2) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(4, 2, 16, 20),
          const Radius.circular(2),
        ),
        paint,
      );
      for (final y in [7.0, 12.0, 17.0]) {
        canvas.drawLine(Offset(8, y), Offset(y == 17 ? 13 : 16, y), paint);
      }
    } else {
      for (final y in [6.0, 12.0, 18.0]) {
        canvas.drawLine(Offset(3, y), Offset(21, y), paint);
      }
    }
  }

  @override
  bool shouldRepaint(_NavPainter oldDelegate) =>
      oldDelegate.index != index || oldDelegate.selected != selected;
}
