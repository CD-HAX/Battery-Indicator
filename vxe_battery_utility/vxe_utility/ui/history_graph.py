 
import time
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath, QLinearGradient, QPen, QBrush
from PyQt6.QtWidgets import QWidget

from vxe_utility.backend.hid_monitor import VXEHardwareMonitor


class HistoryGraphWidget(QWidget):
    def __init__(self, monitor: VXEHardwareMonitor):
        super().__init__()
        self.monitor = monitor
        self.hours_window = 24
        self.hover_x = None
        self.setMouseTracking(True)
        self.setFixedHeight(150)

    def set_window_hours(self, hours: int):
        self.hours_window = hours
        self.update()

    def leaveEvent(self, event):
        self.hover_x = None
        self.update()

    def mouseMoveEvent(self, event):
        self.hover_x = event.position().x()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, 12, 12)
        p.fillPath(bg_path, QColor(22, 26, 30))
        p.setPen(QPen(QColor(42, 48, 56), 1))
        p.drawPath(bg_path)

        pad_l, pad_r, pad_t, pad_b = 38, 16, 18, 26
        plot_w = self.width() - pad_l - pad_r
        plot_h = self.height() - pad_t - pad_b

        p.setFont(QFont("Segoe UI", 8))
        for pct in (100, 50, 0):
            y = pad_t + plot_h * (1.0 - pct / 100.0)
            p.setPen(QPen(QColor(45, 52, 60), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(pad_l, y), QPointF(pad_l + plot_w, y))
            p.setPen(QColor(130, 140, 152))
            p.drawText(
                QRectF(4, y - 8, 30, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{pct}%",
            )

        now = time.time()
        start_ts = now - (self.hours_window * 3600)
        for frac in (0.2, 0.5, 0.8):
            tx = pad_l + plot_w * frac
            t_struct = time.localtime(start_ts + (now - start_ts) * frac)
            label = time.strftime("%H:%M", t_struct)
            p.setPen(QColor(130, 140, 152))
            p.drawText(QRectF(tx - 24, self.height() - 22, 48, 18), Qt.AlignmentFlag.AlignCenter, label)

        pts = [pt for pt in self.monitor.history if pt["ts"] >= start_ts]
        if not pts:
            pts = [{"ts": now, "pct": self.monitor.battery}]
        if len(pts) == 1:
            pts = [{"ts": start_ts, "pct": pts[0]["pct"]}, pts[0]]

        screen_pts = []
        for pt in pts:
            x = pad_l + ((pt["ts"] - start_ts) / (now - start_ts)) * plot_w
            x = max(pad_l, min(pad_l + plot_w, x))
            y = pad_t + plot_h * (1.0 - (pt["pct"] / 100.0))
            screen_pts.append((QPointF(x, y), pt["ts"], pt["pct"]))

        area = QPainterPath()
        area.moveTo(screen_pts[0][0].x(), pad_t + plot_h)
        for qp, _, _ in screen_pts:
            area.lineTo(qp)
        area.lineTo(screen_pts[-1][0].x(), pad_t + plot_h)
        area.closeSubpath()

        fill_grad = QLinearGradient(0, pad_t, 0, pad_t + plot_h)
        fill_grad.setColorAt(0.0, QColor(52, 224, 120, 75))
        fill_grad.setColorAt(1.0, QColor(52, 224, 120, 4))
        p.fillPath(area, QBrush(fill_grad))

        line = QPainterPath()
        line.moveTo(screen_pts[0][0])
        for qp, _, _ in screen_pts[1:]:
            line.lineTo(qp)
        p.setPen(QPen(QColor(62, 228, 128), 2.2))
        p.drawPath(line)

        for qp, _, _ in screen_pts:
            p.setPen(QPen(QColor(22, 26, 30), 1.5))
            p.setBrush(QColor(135, 250, 180))
            p.drawEllipse(qp, 3.2, 3.2)

        if self.hover_x is not None and pad_l <= self.hover_x <= pad_l + plot_w:
            nearest = min(screen_pts, key=lambda item: abs(item[0].x() - self.hover_x))
            nqp, nts, npct = nearest
            p.setPen(QPen(QColor(140, 160, 180, 140), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(nqp.x(), pad_t), QPointF(nqp.x(), pad_t + plot_h))

            p.setBrush(QColor(62, 228, 128))
            p.setPen(QPen(QColor(255, 255, 255), 2))
            p.drawEllipse(nqp, 5.0, 5.0)

            tip_str = f"{time.strftime('%H:%M', time.localtime(nts))} · {npct}%"
            tip_w, tip_h = 88, 22
            tip_x = max(pad_l, min(nqp.x() - tip_w / 2, self.width() - tip_w - 8))
            tip_y = max(6, nqp.y() - 30)
            tip_rect = QRectF(tip_x, tip_y, tip_w, tip_h)

            p.setPen(QPen(QColor(75, 90, 105), 1))
            p.setBrush(QColor(30, 36, 44, 240))
            p.drawRoundedRect(tip_rect, 6, 6)
            p.setPen(QColor(240, 245, 250))
            p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            p.drawText(tip_rect, Qt.AlignmentFlag.AlignCenter, tip_str)