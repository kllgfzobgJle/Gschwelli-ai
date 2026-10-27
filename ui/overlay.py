"""Mode A: Lightweight PyQt6 Floating Command Bar + System Tray Icon (`Ctrl+Space` Global Summon)."""

from __future__ import annotations

import sys
import threading
import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from core.router import AetherRouter, RouteResult
from core.undo import undo_last
from engines.voice_engine import VoiceDaemon
from server.api import start_background_server


class _OverlayBridge(QObject):
    summon_requested = pyqtSignal()
    route_completed = pyqtSignal(object)
    voice_state_changed = pyqtSignal(str)


def _create_reactor_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#00d4ff"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(8, 8, 48, 48)
    painter.setBrush(QColor("#060a10"))
    painter.drawEllipse(18, 18, 28, 28)
    painter.setBrush(QColor("#00d4ff"))
    painter.drawEllipse(24, 24, 16, 16)
    painter.end()
    return QIcon(pix)


class AetherOverlayWindow(QWidget):
    """Frameless Spotlight/Raycast-style floating command bar for Windows 11."""

    def __init__(
        self,
        router: AetherRouter,
        voice_daemon: VoiceDaemon,
        dashboard_url: str = "http://127.0.0.1:8765",
    ) -> None:
        super().__init__()
        self.router = router
        self.voice_daemon = voice_daemon
        self.dashboard_url = dashboard_url
        self._bridge = _OverlayBridge()
        self._bridge.summon_requested.connect(self.toggle_summon)
        self._bridge.route_completed.connect(self._on_route_done)
        self._bridge.voice_state_changed.connect(self._on_voice_state)

        self.router.add_listener(lambda res: self._bridge.route_completed.emit(res))

        self.setWindowTitle("AETHER Command Bar")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(720, 118)

        self._build_ui()
        self._center_top()

    def _center_top(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + int(geo.height() * 0.16)
            self.move(x, y)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        container = QWidget(self)
        container.setObjectName("aetherBar")
        container.setStyleSheet(
            """
            QWidget#aetherBar {
                background-color: rgba(11, 18, 28, 242);
                border: 1.5px solid #00d4ff;
                border-radius: 12px;
            }
            QLineEdit {
                background-color: #101a28;
                color: #f8fafc;
                border: 1px solid #1b2a3e;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QPushButton {
                background-color: rgba(0, 212, 255, 0.14);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.45);
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(0, 212, 255, 0.28);
            }
            """
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.brand_lbl = QLabel("AETHER // 4-TIER ROUTER")
        self.brand_lbl.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.brand_lbl.setStyleSheet("color: #00d4ff;")

        self.tier_badge = QLabel("READY (Ctrl+Space)")
        self.tier_badge.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        self.tier_badge.setStyleSheet("color: #10b981;")

        self.btn_undo = QPushButton("UNDO")
        self.btn_undo.clicked.connect(self._handle_undo)

        self.btn_dash = QPushButton("DASHBOARD")
        self.btn_dash.clicked.connect(lambda: webbrowser.open(self.dashboard_url))

        self.btn_hide = QPushButton("×")
        self.btn_hide.setFixedWidth(28)
        self.btn_hide.clicked.connect(self.hide)

        top_row.addWidget(self.brand_lbl)
        top_row.addStretch()
        top_row.addWidget(self.tier_badge)
        top_row.addWidget(self.btn_undo)
        top_row.addWidget(self.btn_dash)
        top_row.addWidget(self.btn_hide)

        cmd_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type an automation command and press Enter (Esc to hide)...")
        self.input_box.returnPressed.connect(self._submit_command)

        self.btn_run = QPushButton("RUN")
        self.btn_run.setFixedHeight(36)
        self.btn_run.clicked.connect(self._submit_command)

        cmd_row.addWidget(self.input_box, stretch=1)
        cmd_row.addWidget(self.btn_run)

        layout.addLayout(top_row)
        layout.addLayout(cmd_row)
        outer.addWidget(container)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def request_summon_from_thread(self) -> None:
        self._bridge.summon_requested.emit()

    def notify_voice_state_from_thread(self, state: str) -> None:
        self._bridge.voice_state_changed.emit(state)

    def toggle_summon(self) -> None:
        if self.isVisible():
            self.activateWindow()
            self.raise_()
            self.input_box.setFocus()
        else:
            self._center_top()
            self.show()
            self.activateWindow()
            self.raise_()
            self.input_box.setFocus()

    def _submit_command(self) -> None:
        text = self.input_box.text().strip()
        if not text:
            return
        self.input_box.clear()
        self.tier_badge.setText("ROUTING...")
        self.tier_badge.setStyleSheet("color: #f59e0b;")
        threading.Thread(target=self.router.route, args=(text,), daemon=True).start()

    def _handle_undo(self) -> None:
        msg = undo_last(1)
        self.tier_badge.setText("UNDO OK" if "status=done" in msg else "NO UNDO")

    def _on_route_done(self, res: RouteResult) -> None:
        colors = {0: "#00d4ff", 1: "#10b981", 2: "#f59e0b", 3: "#d946ef"}
        col = colors.get(res.active_tier, "#ffffff")
        status = "OK" if res.success else "ERR"
        self.tier_badge.setText(f"T{res.active_tier} // {res.elapsed_ms:.0f} ms [{status}]")
        self.tier_badge.setStyleSheet(f"color: {col};")

    def _on_voice_state(self, state: str) -> None:
        if state != "idle":
            self.tier_badge.setText(f"VOICE: {state.upper()}")


def run_dual_mode_gui(
    router: Optional[AetherRouter] = None,
    port: int = 8765,
    open_dashboard_on_start: bool = False,
) -> int:
    """Launch Mode A (Floating Overlay + System Tray) and Mode B (Background FastAPI + WebSocket Dashboard)."""
    active_router = router or AetherRouter()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    icon = _create_reactor_icon()
    app.setWindowIcon(icon)

    voice_daemon = VoiceDaemon(router=active_router)
    dashboard_url = f"http://127.0.0.1:{port}"
    overlay = AetherOverlayWindow(
        router=active_router,
        voice_daemon=voice_daemon,
        dashboard_url=dashboard_url,
    )

    voice_daemon._on_overlay_summon = overlay.request_summon_from_thread
    voice_daemon._on_status_change = overlay.notify_voice_state_from_thread
    voice_daemon.start()

    start_background_server(
        router=active_router,
        voice_daemon=voice_daemon,
        port=port,
        open_browser=open_dashboard_on_start,
    )

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("AETHER — 4-Tier Hybrid Automation Router (Ctrl+Space)")
    menu = QMenu()

    act_show = QAction("Toggle Command Bar (Ctrl+Space)", menu)
    act_show.triggered.connect(overlay.toggle_summon)
    menu.addAction(act_show)

    act_dash = QAction("Open Full Control Center Dashboard", menu)
    act_dash.triggered.connect(lambda: webbrowser.open(dashboard_url))
    menu.addAction(act_dash)

    act_undo = QAction("Undo Last Action", menu)
    act_undo.triggered.connect(lambda: undo_last(1))
    menu.addAction(act_undo)

    menu.addSeparator()
    act_quit = QAction("Quit AETHER", menu)
    act_quit.triggered.connect(app.quit)
    menu.addAction(act_quit)

    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: overlay.toggle_summon()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()

    overlay.show()
    QTimer.singleShot(100, overlay.toggle_summon)
    return app.exec()
