from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPainterPath, QLinearGradient, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame,
)

from vxe_utility.config import PANEL_WIDTH, PANEL_HEIGHT, EST_MAX_RUNTIME_HOURS, get_battery_palette
from vxe_utility.backend.hid_monitor import VXEHardwareMonitor
from vxe_utility.ui.history_graph import HistoryGraphWidget


class DetailPanel(QWidget):
    def __init__(self, monitor: VXEHardwareMonitor):
        super().__init__()
        self.monitor = monitor
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(PANEL_WIDTH, PANEL_HEIGHT)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.bat_glyph = QLabel()
        self.bat_glyph.setFixedSize(28, 44)
        header_layout.addWidget(self.bat_glyph)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.lbl_model = QLabel("VXE R1 PRO MAX")
        self.lbl_model.setStyleSheet("color: #F3F6FA; font-family: 'Segoe UI'; font-size: 13px; font-weight: 600;")
        self.lbl_main_stat = QLabel("75%  Discharging")
        self.lbl_main_stat.setStyleSheet("color: #FFFFFF; font-family: 'Segoe UI'; font-size: 20px; font-weight: 700;")
        title_col.addWidget(self.lbl_model)
        title_col.addWidget(self.lbl_main_stat)
        header_layout.addLayout(title_col)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # 6-Card Telemetry Grid
        grid = QGridLayout()
        grid.setSpacing(8)
        self.card_health = self._make_stat_card("Health", "100%")
        self.card_cap = self._make_stat_card("Capacity", f"{self.monitor.capacity_mah}mAh")
        self.card_draw = self._make_stat_card("Power Draw", "~8.5mA")
        self.card_volt = self._make_stat_card("Voltage", "3.980V")
        self.card_status = self._make_stat_card("Status", "Active")
        self.card_runtime = self._make_stat_card("Est. runtime", "35h")

        grid.addWidget(self.card_health[0], 0, 0)
        grid.addWidget(self.card_cap[0], 0, 1)
        grid.addWidget(self.card_draw[0], 0, 2)
        grid.addWidget(self.card_volt[0], 1, 0)
        grid.addWidget(self.card_status[0], 1, 1)
        grid.addWidget(self.card_runtime[0], 1, 2)
        main_layout.addLayout(grid)

        # Profile Selector Row
        prof_row = QHBoxLayout()
        lbl_prof = QLabel("Profile")
        lbl_prof.setStyleSheet("color: #9AA4B2; font-family: 'Segoe UI'; font-size: 12px;")
        prof_row.addWidget(lbl_prof)
        prof_row.addStretch()

        self.prof_btns = []
        for name in ("Low Power", "Balanced", "Performance"):
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self._select_profile(n))
            self.prof_btns.append((name, btn))
            prof_row.addWidget(btn)
        self._select_profile("Balanced")
        main_layout.addLayout(prof_row)

        # History Header & 12h / 24h Toggle Row
        hist_row = QHBoxLayout()
        lbl_hist = QLabel("Battery History")
        lbl_hist.setStyleSheet("color: #9AA4B2; font-family: 'Segoe UI'; font-size: 12px;")
        hist_row.addWidget(lbl_hist)
        hist_row.addStretch()

        self.btn_12h = QPushButton("12h")
        self.btn_24h = QPushButton("24h")
        for b, hrs in ((self.btn_12h, 12), (self.btn_24h, 24)):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda checked, h=hrs: self._select_window(h))
            hist_row.addWidget(b)
        main_layout.addLayout(hist_row)

        # Graph Widget
        self.graph = HistoryGraphWidget(self.monitor)
        main_layout.addWidget(self.graph)
        self._select_window(24)

    def _make_stat_card(self, title: str, value: str):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #21262D;
                border: 1px solid #30363D;
                border-radius: 10px;
            }
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)
        lbl_t = QLabel(title)
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t.setStyleSheet("color: #8B949E; font-family: 'Segoe UI'; font-size: 11px; border: none;")
        lbl_v = QLabel(value)
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_v.setStyleSheet("color: #F0F6FC; font-family: 'Segoe UI'; font-size: 13px; font-weight: 600; border: none;")
        lay.addWidget(lbl_t)
        lay.addWidget(lbl_v)
        return frame, lbl_v

    def _select_profile(self, selected: str):
        for name, btn in self.prof_btns:
            if name == selected:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #388BFD; color: #FFFFFF;
                        border: none; border-radius: 11px;
                        padding: 4px 11px; font-family: 'Segoe UI'; font-size: 11px; font-weight: 600;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #21262D; color: #9AA4B2;
                        border: 1px solid #30363D; border-radius: 11px;
                        padding: 4px 11px; font-family: 'Segoe UI'; font-size: 11px;
                    }
                    QPushButton:hover { background-color: #292F36; color: #FFFFFF; }
                """)

    def _select_window(self, hours: int):
        self.graph.set_window_hours(hours)
        for hrs, btn in ((12, self.btn_12h), (24, self.btn_24h)):
            if hrs == hours:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #388BFD; color: #FFFFFF;
                        border: none; border-radius: 10px;
                        padding: 3px 10px; font-family: 'Segoe UI'; font-size: 11px; font-weight: 600;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #21262D; color: #9AA4B2;
                        border: 1px solid #30363D; border-radius: 10px;
                        padding: 3px 10px; font-family: 'Segoe UI'; font-size: 11px;
                    }
                """)

    def refresh_ui(self):
        pct = self.monitor.battery
        if not self.monitor.connected:
            state_str = "Disconnected"
        elif self.monitor.is_charging:
            state_str = "Charging"
        elif self.monitor.is_asleep:
            state_str = "Sleeping (Cached)"
        else:
            state_str = "Discharging"

        self.lbl_main_stat.setText(f"{pct}%  {state_str}")

        draw_str, runtime_str = self.monitor.get_live_drain_and_runtime()
        self.card_health[1].setText(f"{self.monitor.health_pct}%")
        self.card_cap[1].setText(f"{self.monitor.remaining_mah} / {self.monitor.capacity_mah}mAh")
        self.card_draw[1].setText(draw_str)
        self.card_volt[1].setText(f"{self.monitor.voltage:.3f}V")
        self.card_status[1].setText(
            "Offline" if not self.monitor.connected
            else ("Charging" if self.monitor.is_charging else ("Asleep" if self.monitor.is_asleep else "Active (Wireless)"))
        )
        self.card_runtime[1].setText(runtime_str)

        # Render vertical battery glyph synced to the shared Green->Amber->Red gradient
        top_col, bot_col, _, crest_col, _ = get_battery_palette(pct)
        pix = QPixmap(28, 44)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(120, 130, 140))
        p.drawRoundedRect(QRectF(9, 2, 10, 4), 1.5, 1.5)
        p.setPen(QPen(crest_col, 1.6))
        p.setBrush(QColor(20, 26, 32))
        p.drawRoundedRect(QRectF(4, 6, 20, 35), 4, 4)

        fill_h = max(2.0, (pct / 100.0) * 29.0)
        top_y = 6 + 32 - fill_h
        grad = QLinearGradient(0, top_y, 0, 38)
        grad.setColorAt(0.0, top_col)
        grad.setColorAt(1.0, bot_col)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(QRectF(7, top_y, 14, fill_h), 2.5, 2.5)
        p.end()

        self.bat_glyph.setPixmap(pix)
        self.graph.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        p.fillPath(path, QColor(15, 18, 22, 250))
        p.setPen(QPen(QColor(52, 60, 70), 1.5))
        p.drawPath(path)
