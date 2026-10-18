import sys
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF, QPointF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QCursor, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from vxe_utility.config import POLL_INTERVAL_MS, HOVER_CHECK_MS, get_battery_palette
from vxe_utility.backend.hid_monitor import VXEHardwareMonitor
from vxe_utility.ui.wave_osd import WaveOSD
from vxe_utility.ui.detail_panel import DetailPanel


class VXETrayController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.monitor = VXEHardwareMonitor()
        self.monitor.poll()

        self.osd = WaveOSD(self.monitor)
        self.panel = DetailPanel(self.monitor)

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.build_tray_icon())
        self.tray.activated.connect(self.on_tray_activated)

        menu = QMenu()
        act_open = QAction("Open Battery Plus Dashboard", menu)
        act_open.triggered.connect(self.toggle_detail_panel)
        act_refresh = QAction("Force Poll Hardware", menu)
        act_refresh.triggered.connect(self.poll_now)
        act_quit = QAction("Exit", menu)
        act_quit.triggered.connect(self.app.quit)
        menu.addAction(act_open)
        menu.addAction(act_refresh)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_now)
        self.poll_timer.start(POLL_INTERVAL_MS)

        self.hover_timer = QTimer()
        self.hover_timer.timeout.connect(self.check_tray_hover)
        self.hover_timer.start(HOVER_CHECK_MS)

    def build_tray_icon(self) -> QIcon:
        pix = QPixmap(64, 64)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pct = self.monitor.battery
        top_col, _, _, _, _ = get_battery_palette(pct)
        color = QColor(top_col)
        if self.monitor.is_asleep:
            color.setAlpha(185)

        # Mouse body silhouette
        p.setPen(QPen(color, 4.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(10, 6, 32, 48), 15, 15)
        p.drawLine(QPointF(26, 6), QPointF(26, 24))
        p.drawLine(QPointF(10, 24), QPointF(42, 24))

        # Mini battery shell + proportional fill level
        p.setPen(QPen(QColor(15, 20, 25), 2.5))
        p.setBrush(QColor(18, 24, 28))
        p.drawRoundedRect(QRectF(36, 30, 20, 28), 4, 4)

        p.setPen(QPen(color, 2.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(36, 30, 20, 28), 4, 4)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawRect(QRectF(42, 26, 8, 4))

        fill_h = max(2.0, (pct / 100.0) * 22.0)
        p.drawRoundedRect(QRectF(39, 30 + 25 - fill_h, 14, fill_h), 2, 2)

        p.end()
        return QIcon(pix)

    def poll_now(self):
        self.monitor.poll()
        self.tray.setIcon(self.build_tray_icon())
        if self.panel.isVisible():
            self.panel.refresh_ui()

    def check_tray_hover(self):
        if self.panel.isVisible():
            if self.osd.isVisible():
                self.osd.hide()
            return

        geo = self.tray.geometry()
        cursor = QCursor.pos()

        if geo.isValid():
            center = geo.center()
            icon_hitbox = QRect(center.x() - 9, center.y() - 9, 18, 18)

            if icon_hitbox.contains(cursor):
                if not self.osd.isVisible():
                    screen_right = QApplication.primaryScreen().availableGeometry().right()
                    x = max(12, min(center.x() - self.osd.width() // 2, screen_right - self.osd.width() - 12))
                    y = max(12, geo.top() - self.osd.height() - 12)
                    self.osd.move(x, y)
                    self.osd.show()
                return

        if self.osd.isVisible():
            self.osd.hide()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_detail_panel()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            if self.osd.isVisible():
                self.osd.hide()
            else:
                cursor = QCursor.pos()
                self.osd.move(cursor.x() - self.osd.width() // 2, cursor.y() - self.osd.height() - 20)
                self.osd.show()

    def toggle_detail_panel(self):
        if self.osd.isVisible():
            self.osd.hide()
        if self.panel.isVisible():
            self.panel.hide()
            return

        self.panel.refresh_ui()
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.tray.geometry()
        anchor_x = geo.center().x() if geo.isValid() else QCursor.pos().x()

        x = max(12, min(anchor_x - self.panel.width() // 2, screen.right() - self.panel.width() - 12))
        y = screen.bottom() - self.panel.height() - 12
        self.panel.move(x, y)
        self.panel.show()
        self.panel.activateWindow()

    def run(self):
        sys.exit(self.app.exec())
