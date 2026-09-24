from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter,
    QPainterPath,
    QPen,
    QColor,
    QFont,
    QLinearGradient,
    QRadialGradient,
)
from PySide6.QtWidgets import QFrame, QPushButton, QDialog, QVBoxLayout, QLabel, QHBoxLayout, QMessageBox

APP_RED = "#e40018"


class ASLANTopBar(QFrame):
    """ASLAN TUNING custom title bar drawn entirely with QPainter."""

    maximize_requested = Signal()
    logout_requested = Signal()
    BAR_HEIGHT = 50

    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.parent_window = parent
        self._title = title
        self._dragging = False
        self._drag_position = None

        self.profile_btn = self._make_button("", "ProfileButton")
        self.profile_btn.setFixedSize(172, self.BAR_HEIGHT - 8)
        self.profile_btn.setText(self._profile_label())
        self.profile_btn.setToolTip("Open your ASLAN TUNER profile")
        self.profile_btn.clicked.connect(self._show_profile)

        self.setFixedHeight(self.BAR_HEIGHT)
        self.setObjectName("ASLANTopBar")
        self.setMouseTracking(True)

        self.min_btn = self._make_button("—", "MinimizeButton")
        self.max_btn = self._make_button("□", "MaximizeButton")
        self.close_btn = self._make_button("×", "CloseButton")

        self.min_btn.clicked.connect(self._minimize)
        self.max_btn.clicked.connect(self._maximize)
        self.close_btn.clicked.connect(self._close)

        self.setStyleSheet("""
            QFrame#ASLANTopBar {
                background: transparent;
                border: none;
            }
            QPushButton {
                border: none;
                background: transparent;
                color: #e7e7e9;
                padding: 0;
                margin: 0;
                font-family: "Segoe UI";
                font-size: 14px;
                font-weight: 400;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.055);
                color: white;
            }
            QPushButton#ProfileButton {
                background: rgba(18, 21, 26, 0.92);
                border: 1px solid #3b4048;
                border-radius: 10px;
                color: #f2f3f5;
                padding: 0 14px;
                font-size: 14px;
                font-weight: 800;
                text-align: left;
            }
            QPushButton#ProfileButton:hover {
                background: rgba(42, 19, 24, 0.96);
                border-color: #e90018;
                color: white;
            }
            QPushButton#ProfileButton:pressed {
                background: #3a0e15;
            }
            QPushButton#CloseButton:hover {
                background: #c90012;
            }
        """)
        self._position_buttons()

    def _profile_label(self):
        username = ""
        try:
            from PySide6.QtCore import QSettings
            username = str(QSettings("ASLAN", "ASLAN_TUNER").value("account/username", "")).strip()
        except Exception:
            pass
        if username:
            if len(username) > 14:
                username = username[:13] + "…"
            return f"◉  {username}"
        return "◉  PROFILE"

    def _make_button(self, text, name):
        button = QPushButton(text, self)
        button.setObjectName(name)
        button.setFixedSize(42, self.BAR_HEIGHT)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def resizeEvent(self, event):
        self._position_buttons()
        super().resizeEvent(event)

    def _position_buttons(self):
        w = self.width()
        self.profile_btn.move(10, 4)
        self.min_btn.move(w - 132, 0)
        self.max_btn.move(w - 90, 0)
        self.close_btn.move(w - 48, 0)

    # ---------------------------------------------------------
    # PAINT THE REFERENCE DESIGN
    # ---------------------------------------------------------
    def paintEvent(self, event):
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        w, h = self.width(), self.height()
        red = QColor("#ef1730")
        red_dim = QColor("#7e0b18")

        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.0, QColor("#15181d"))
        bg.setColorAt(0.45, QColor("#0e1115"))
        bg.setColorAt(1.0, QColor("#090b0e"))
        p.fillRect(self.rect(), bg)

        # Subtle red center glow and a thin motorsport-style accent line.
        glow = QRadialGradient(QPointF(w * 0.5, 0), max(80, w * 0.22))
        glow.setColorAt(0.0, QColor(239, 23, 48, 75))
        glow.setColorAt(1.0, QColor(239, 23, 48, 0))
        p.fillRect(QRectF(w * .25, 0, w * .50, h), glow)

        p.setPen(QPen(QColor("#2c3138"), 1))
        p.drawLine(0, h - 1, w, h - 1)
        p.setPen(QPen(red, 2))
        p.drawLine(12, 3, min(230, int(w * .20)), 3)
        p.drawLine(max(0, w - 230), 3, w - 12, 3)

        # Small center chevron; keeps the tuning aesthetic without a giant logo.
        cx = w / 2
        path = QPainterPath()
        path.moveTo(cx - 78, 3)
        path.lineTo(cx - 60, h - 5)
        path.lineTo(cx + 60, h - 5)
        path.lineTo(cx + 78, 3)
        p.setPen(QPen(red_dim, 1))
        p.drawPath(path)

        title_font = QFont("Segoe UI", 12)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        p.setFont(title_font)
        p.setPen(QColor("#ff4054"))
        p.drawText(QRectF(cx - 190, 0, 380, h),
                   Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                   self._title.upper())
        p.end()

    def _show_profile(self):
        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle("ASLAN TUNER • Profile")
        dialog.setModal(True)
        dialog.setMinimumSize(430, 300)
        dialog.resize(470, 340)

        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("ASLAN", "ASLAN_TUNER")
            username = str(settings.value("account/username", "")).strip() or "Local User"
        except Exception:
            username = "Local User"

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(12)

        eyebrow = QLabel("ACCOUNT CENTER")
        eyebrow.setStyleSheet("color:#ff3045;font-size:11px;font-weight:900;letter-spacing:1px;")
        layout.addWidget(eyebrow)

        title = QLabel(username)
        title.setStyleSheet("color:#f4f5f7;font-size:25px;font-weight:900;")
        layout.addWidget(title)

        status = QLabel("●  Signed in  •  Local ASLAN TUNER account")
        status.setStyleSheet("color:#73e69a;font-size:13px;font-weight:700;")
        layout.addWidget(status)

        card = QFrame()
        card.setObjectName("ProfileCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        info = QLabel(f"Username\n{username}")
        info.setStyleSheet("color:#d8dbe0;font-size:13px;line-height:1.4;")
        card_layout.addWidget(info)
        layout.addWidget(card)
        layout.addStretch()

        row = QHBoxLayout()
        row.addStretch()
        close_btn = QPushButton("Close")
        logout_btn = QPushButton("Log out")
        logout_btn.setObjectName("LogoutButton")
        close_btn.clicked.connect(dialog.reject)

        def do_logout():
            answer = QMessageBox.question(
                dialog, "Log out",
                "Log out from this device? You will need to sign in again next time.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.logout_requested.emit()
                dialog.accept()

        logout_btn.clicked.connect(do_logout)
        row.addWidget(close_btn)
        row.addWidget(logout_btn)
        layout.addLayout(row)

        dialog.setStyleSheet("""
            QDialog{background:#0d1014;color:#f4f5f7;}
            QFrame#ProfileCard{background:#15181d;border:1px solid #303640;border-radius:12px;}
            QPushButton{background:#181c22;color:white;border:1px solid #3a404a;border-radius:9px;padding:10px 18px;font-weight:700;}
            QPushButton:hover{border-color:#ff172b;background:#21161a;}
            QPushButton#LogoutButton{background:#5b0b12;border-color:#a90f1e;}
            QPushButton#LogoutButton:hover{background:#8b101b;border-color:#ff3045;}
        """)
        dialog.exec()
        self.profile_btn.setText(self._profile_label())

    # ---------------------------------------------------------
    # WINDOW ACTIONS
    # ---------------------------------------------------------
    def _minimize(self):
        self.parent_window.showMinimized()

    def _maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.max_btn.setText("□")
        else:
            self.parent_window.showMaximized()
            self.max_btn.setText("❐")
        self.maximize_requested.emit()

    def _close(self):
        self.parent_window.close()

    def set_title(self, title):
        self._title = title
        self.update()

    # ---------------------------------------------------------
    # WINDOW DRAG
    # ---------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.parent_window.isMaximized():
                self._dragging = True
                self._drag_position = (
                    event.globalPosition().toPoint()
                    - self.parent_window.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            if not self.parent_window.isMaximized():
                self.parent_window.move(
                    event.globalPosition().toPoint() - self._drag_position
                )
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self._drag_position = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
