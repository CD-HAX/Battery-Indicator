import math
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QLinearGradient, QPen, QBrush
from PyQt6.QtWidgets import QWidget

from vxe_utility.config import OSD_WIDTH, OSD_HEIGHT, get_battery_palette
from vxe_utility.backend.hid_monitor import VXEHardwareMonitor


class WaveOSD(QWidget):
    def __init__(self, monitor: VXEHardwareMonitor):
        super().__init__()
        self.monitor = monitor
        self.phase = 0.0
        self.displayed_pct = float(self.monitor.battery)

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(OSD_WIDTH, OSD_HEIGHT)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.tick)

    def showEvent(self, event):
        self.displayed_pct = float(self.monitor.battery)
        if not self.anim_timer.isActive():
            self.anim_timer.start(16)
        super().showEvent(event)

    def hideEvent(self, event):
        self.anim_timer.stop()
        super().hideEvent(event)

    def tick(self):
        self.phase = (self.phase + 0.09) % (2 * math.pi)
        target = float(max(0, min(100, self.monitor.battery)))
        self.displayed_pct += (target - self.displayed_pct) * 0.12
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(3, 3, self.width() - 6, self.height() - 6)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(rect, 22, 22)

        p.fillPath(clip_path, QColor(14, 18, 20, 245))
        p.save()
        p.setClipPath(clip_path)

        pct = max(0.0, min(100.0, self.displayed_pct))
        top_col, bot_col, back_col, crest_col, border_col = get_battery_palette(pct)

        fill_ratio = pct / 100.0
        base_y = rect.bottom() - (fill_ratio * rect.height())

        edge_damp = min(1.0, min(fill_ratio * 8.0, (1.0 - fill_ratio) * 8.0))
        amp_back = 4.5 * max(0.15, edge_damp)
        amp_front = 4.0 * max(0.15, edge_damp)

        if pct > 0.5:
            back_wave = QPainterPath()
            back_wave.moveTo(rect.left(), rect.bottom())
            for x in range(int(rect.left()), int(rect.right()) + 4, 4):
                y = base_y + math.sin((x * 0.022) - self.phase + 1.4) * amp_back
                back_wave.lineTo(x, y)
            back_wave.lineTo(rect.right(), rect.bottom())
            back_wave.closeSubpath()
            p.fillPath(back_wave, back_col)

            front_wave = QPainterPath()
            front_wave.moveTo(rect.left(), rect.bottom())
            for x in range(int(rect.left()), int(rect.right()) + 4, 4):
                y = base_y + math.sin((x * 0.025) + self.phase) * amp_front
                front_wave.lineTo(x, y)
            front_wave.lineTo(rect.right(), rect.bottom())
            front_wave.closeSubpath()

            grad = QLinearGradient(0, base_y - amp_front, 0, rect.bottom())
            grad.setColorAt(0.0, top_col)
            grad.setColorAt(1.0, bot_col)
            p.fillPath(front_wave, QBrush(grad))

            crest = QPainterPath()
            for i, x in enumerate(range(int(rect.left()), int(rect.right()) + 4, 4)):
                y = base_y + math.sin((x * 0.025) + self.phase) * amp_front
                if i == 0:
                    crest.moveTo(x, y)
                else:
                    crest.lineTo(x, y)
            p.setPen(QPen(crest_col, 1.8))
            p.drawPath(crest)

        circle_rect = QRectF(20, 22, 52, 52)
        p.setPen(QPen(crest_col, 1.5))
        p.setBrush(QColor(12, 20, 18, 175))
        p.drawEllipse(circle_rect)

        p.setPen(QPen(QColor(240, 250, 245), 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(36, 31, 16, 26), 7, 7)
        p.drawLine(QPointF(44, 31), QPointF(44, 40))
        p.drawLine(QPointF(36, 40), QPointF(52, 40))

        p.setBrush(top_col)
        p.setPen(QPen(QColor(14, 22, 18), 1.2))
        p.drawRoundedRect(QRectF(49, 45, 9, 14), 2, 2)

        state_word = (
            "Charging" if self.monitor.is_charging
            else ("Sleeping" if self.monitor.is_asleep else "Active")
        )
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        p.drawText(
            QRectF(86, 20, 230, 32),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{int(round(pct))}%  {state_word}",
        )

        sub_text = (
            "Connected to USB-C" if self.monitor.is_charging
            else ("Wireless (Cached State)" if self.monitor.is_asleep else "Wireless Connection")
        )
        p.setPen(QColor(230, 242, 235, 230))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        p.drawText(
            QRectF(86, 50, 230, 24),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            sub_text,
        )

        p.restore()
        p.setPen(QPen(border_col, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 22, 22)
