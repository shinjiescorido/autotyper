#!/usr/bin/env python3
"""Qt window for autotyper.py: start/pause, live settings, stats and a log.

The typing and mouse threads are the ones in autotyper.py; this only edits
`autotyper.cfg`, reads `autotyper.stats` and replaces `autotyper.notify`.
Start/Stop turn the typer on and off; while started, DEL starts/pauses typing
globally, and the window keeps in sync with it.
"""

import ctypes
import os
import sys
import time

# Qt's xcb plugin needs libxcb-cursor0. If the system doesn't have it, use the
# copy unpacked into .libs/ (apt download libxcb-cursor0 + dpkg-deb -x; no sudo).
_LOCAL_XCB_CURSOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".libs", "libxcb-cursor.so.0")
try:
    ctypes.CDLL("libxcb-cursor.so.0", mode=ctypes.RTLD_GLOBAL)
except OSError:
    if os.path.exists(_LOCAL_XCB_CURSOR):
        ctypes.CDLL(_LOCAL_XCB_CURSOR, mode=ctypes.RTLD_GLOBAL)

# PySide6 (pip: dev venv, Windows build) or PyQt6 (Ubuntu's python3-pyqt6, used by
# the .deb). Same API apart from Signal; enums are written fully scoped for PyQt6.
try:
    from PySide6.QtCore import QObject, Qt, QTimer, Signal
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
        QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
    )
except ImportError:
    from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal as Signal
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
        QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
    )

import autotyper as at

class Bridge(QObject):
    """Carries autotyper.notify calls from worker threads to the Qt thread."""
    event = Signal(str, str)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Typer")

        self.bridge = Bridge()
        self.bridge.event.connect(self.on_event)
        at.notify = lambda kind, message="": self.bridge.event.emit(kind, message)

        # Status + start/stop
        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.status.setFont(font)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setToolTip("Turn the typer on. Then press DEL in your editor to type / pause.")
        self.start_btn.clicked.connect(at.start)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setToolTip("Turn the typer off: typing stops, DEL is ignored, the round and stats reset. "
                                 "The editor isn't cleared; the next run begins a fresh round on a new line.")
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        buttons = QHBoxLayout()
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.stop_btn)

        self.on_top = QCheckBox("Keep window on top")
        self.on_top.toggled.connect(self.set_on_top)

        # Settings (written straight into autotyper.cfg; locked unless stopped)
        self.text_type = QComboBox()
        self.text_type.addItems(["js", "css"])
        self.text_type.setCurrentText(at.cfg.text_type)
        self.text_type.currentTextChanged.connect(lambda v: setattr(at.cfg, "text_type", v))

        self.char_delay = self.double_spin(at.cfg.char_delay, 0.01, 5.0, 0.05, " s", "char_delay")
        self.mouse_every = self.double_spin(at.cfg.mouse_every, 1.0, 600.0, 1.0, " s", "mouse_every")

        self.inch_px = QSpinBox()
        self.inch_px.setRange(0, 2000)
        self.inch_px.setSuffix(" px")
        self.inch_px.setValue(at.cfg.inch_px)
        self.inch_px.valueChanged.connect(lambda v: setattr(at.cfg, "inch_px", v))

        self.lines_per_round = QSpinBox()
        self.lines_per_round.setRange(1, 100000)
        self.lines_per_round.setValue(at.cfg.lines_per_round)
        self.lines_per_round.valueChanged.connect(lambda v: setattr(at.cfg, "lines_per_round", v))

        self.auto_indent = QCheckBox("Editor auto-indents (VS Code, Sublime)")
        self.auto_indent.setChecked(at.cfg.editor_auto_indent)
        self.auto_indent.toggled.connect(lambda v: setattr(at.cfg, "editor_auto_indent", v))

        self.text_type.currentTextChanged.connect(self.sync_lines_enabled)
        self.sync_lines_enabled(at.cfg.text_type)

        form = QFormLayout()
        form.addRow("Text type", self.text_type)
        form.addRow("Delay per character", self.char_delay)
        form.addRow("Mouse move every", self.mouse_every)
        form.addRow("Mouse move distance", self.inch_px)
        form.addRow("CSS lines per round", self.lines_per_round)
        form.addRow("", self.auto_indent)
        self.settings = QGroupBox("Settings")
        self.settings.setLayout(form)
        settings_note = QLabel("Settings can only be changed while stopped.")
        settings_note.setWordWrap(True)
        settings_note.setStyleSheet("color: gray; font-size: 11px;")

        # Stats
        self.round_lbl, self.lines_lbl, self.chars_lbl, self.time_lbl = (QLabel() for _ in range(4))
        stats_row = QHBoxLayout()
        for title, lbl in (("Round", self.round_lbl), ("Lines", self.lines_lbl),
                           ("Chars", self.chars_lbl), ("Run time", self.time_lbl)):
            box = QVBoxLayout()
            cap = QLabel(title)
            cap.setStyleSheet("color: gray; font-size: 11px;")
            lbl.setStyleSheet("font-size: 15px; font-weight: 600;")
            box.addWidget(cap, alignment=Qt.AlignmentFlag.AlignHCenter)
            box.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
            stats_row.addLayout(box)
        stats = QGroupBox("Stats")
        stats.setLayout(stats_row)

        # Log
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        self.log.setMinimumHeight(110)

        hint = QLabel("Start turns the typer on; then DEL starts/pauses typing from anywhere. "
                      "Stop turns it off (DEL does nothing) and resets the round and stats. "
                      "Your editor isn't cleared.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addLayout(buttons)
        layout.addWidget(hint)
        layout.addWidget(self.on_top)
        layout.addWidget(self.settings)
        layout.addWidget(settings_note)
        layout.addWidget(stats)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log)

        # Run-time clock: accumulates only while running
        self.run_seconds = 0.0
        self.last_tick = time.monotonic()

        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(250)
        self.stats_timer.timeout.connect(self.refresh_stats)
        self.stats_timer.start()

        self.refresh_state()
        self.refresh_stats()
        self.append_log("Stopped. Press Start, then DEL in your editor to type.")

    def double_spin(self, value, lo, hi, step, suffix, attr):
        box = QDoubleSpinBox()
        box.setRange(lo, hi)
        box.setSingleStep(step)
        box.setDecimals(2)
        box.setSuffix(suffix)
        box.setValue(value)
        box.valueChanged.connect(lambda v: setattr(at.cfg, attr, v))
        return box

    def sync_lines_enabled(self, text_type):
        self.lines_per_round.setEnabled(text_type == "css")

    def set_on_top(self, on):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on)
        self.show()

    # --- start / stop ---

    def on_stop_clicked(self):
        at.stop()
        self.run_seconds = 0.0
        self.refresh_stats()

    def on_event(self, kind, message):
        if message:
            self.append_log(message)
        self.refresh_state()

    def refresh_state(self):
        started = at.started.is_set()
        if not started:
            self.status.setText("■ Stopped")
            self.status.setStyleSheet("color: #6b7280;")
        elif at.running.is_set():
            self.status.setText("● Typing (DEL to pause)")
            self.status.setStyleSheet("color: #16a34a;")
        elif at.stats.chars:
            self.status.setText("❚❚ Paused (DEL to resume)")
            self.status.setStyleSheet("color: #d97706;")
        else:
            self.status.setText("▶ Started (DEL to type)")
            self.status.setStyleSheet("color: #d97706;")
        self.start_btn.setEnabled(not started)
        self.settings.setEnabled(not started)
        self.stop_btn.setEnabled(started)

    def refresh_stats(self):
        now = time.monotonic()
        if at.running.is_set():
            self.run_seconds += now - self.last_tick
        self.last_tick = now
        self.round_lbl.setText(str(at.stats.round))
        self.lines_lbl.setText(f"{at.stats.lines:,}")
        self.chars_lbl.setText(f"{at.stats.chars:,}")
        s = int(self.run_seconds)
        self.time_lbl.setText(f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}")

    def append_log(self, message):
        self.log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {message}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Auto Typer")
    app.setDesktopFileName("autotyper")
    win = Window()
    at.start_workers()
    win.resize(420, 640)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
