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
from PySide6.QtWidgets import QFrame, QPushButton

APP_RED = "#e40018"


class ASLANTopBar(QFrame):
    """ASLAN TUNING custom title bar drawn entirely with QPainter."""

    maximize_requested = Signal()
    BAR_HEIGHT = 56

    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.parent_window = parent
        self._title = title
        self._dragging = False
        self._drag_position = None

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
            QPushButton#CloseButton:hover {
                background: #c90012;
            }
        """)
        self._position_buttons()

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

        w = self.width()
        h = self.height()
        red = QColor("#e90018")
        red2 = QColor("#ff172b")
        dark_red = QColor("#74000d")

        # Dark metallic background instead of a flat black rectangle.
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0.00, QColor("#12151a"))
        bg.setColorAt(0.22, QColor("#0d1014"))
        bg.setColorAt(0.72, QColor("#090b0e"))
        bg.setColorAt(1.00, QColor("#07080a"))
        p.fillRect(self.rect(), bg)

        # Soft red glow behind the center upper edge.
        glow = QRadialGradient(QPointF(w * .50, 0), 190)
        glow.setColorAt(0.00, QColor(255, 0, 25, 115))
        glow.setColorAt(0.22, QColor(230, 0, 20, 42))
        glow.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.fillRect(QRectF(w * .34, 0, w * .32, 12), glow)

        # Thin metallic outer frame.
        p.setPen(QPen(QColor("#363a40"), 1))
        p.drawLine(2, 1, w - 3, 1)
        p.drawLine(2, 2, 2, h - 1)
        p.drawLine(w - 3, 2, w - 3, h - 1)
        p.setPen(QPen(QColor("#202328"), 1))
        p.drawLine(3, h - 2, w - 4, h - 2)

        # Main red geometry. Coordinates are based on the reference and
        # scale around the center so it stays correct on different widths.
        cx = w / 2
        y = 29

        # Left horizontal rail and its angular break.
        p.setPen(QPen(red, 2))
        path = QPainterPath()
        path.moveTo(27, y)
        path.lineTo(cx - 194, y)
        path.lineTo(cx - 151, y)
        path.lineTo(cx - 112, h - 1)
        path.lineTo(cx - 79, h - 1)
        p.drawPath(path)

        # Left upper dark-red diagonal, like the recessed panel in image.
        p.setPen(QPen(dark_red, 1.2))
        path = QPainterPath()
        path.moveTo(cx - 194, y)
        path.lineTo(cx - 151, 4)
        path.lineTo(cx - 98, 4)
        p.drawPath(path)

        # Right mirror geometry, stopping before the controls.
        p.setPen(QPen(red, 2))
        path = QPainterPath()
        path.moveTo(cx + 79, h - 1)
        path.lineTo(cx + 112, h - 1)
        path.lineTo(cx + 151, y)
        path.lineTo(cx + 194, y)
        path.lineTo(w - 226, y)
        p.drawPath(path)

        p.setPen(QPen(dark_red, 1.2))
        path = QPainterPath()
        path.moveTo(cx + 194, y)
        path.lineTo(cx + 151, 4)
        path.lineTo(cx + 98, 4)
        p.drawPath(path)

        # Long outer rails toward the controls.
        p.setPen(QPen(red, 2))
        p.drawLine(w - 226, y, w - 184, y)
        p.drawLine(w - 184, y, w - 161, y + 18)
        p.drawLine(w - 161, y + 18, w - 84, y + 18)

        # Center bottom chevron / shield point.
        path = QPainterPath()
        path.moveTo(cx - 79, h - 1)
        path.lineTo(cx - 20, h - 1)
        path.lineTo(cx, h + 10)
        path.lineTo(cx + 20, h - 1)
        path.lineTo(cx + 79, h - 1)
        p.setPen(QPen(red, 2))
        p.drawPath(path)

        # Thin echo line under the center point.
        p.setPen(QPen(QColor("#8f0010"), 1))
        path = QPainterPath()
        path.moveTo(cx - 21, h - 1)
        path.lineTo(cx, h + 8)
        path.lineTo(cx + 21, h - 1)
        p.drawPath(path)

        # Fine red highlight along the very top center.
        top = QLinearGradient(cx - 100, 0, cx + 100, 0)
        top.setColorAt(0.0, QColor(0, 0, 0, 0))
        top.setColorAt(0.34, QColor(255, 0, 20, 70))
        top.setColorAt(0.50, QColor(255, 35, 55, 210))
        top.setColorAt(0.66, QColor(255, 0, 20, 70))
        top.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(QPen(top, 2))
        p.drawLine(int(cx - 100), 1, int(cx + 100), 1)

        # Left brand.
        brand_font = QFont("DejaVu Sans", 12)
        brand_font.setBold(True)
        brand_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.7)
        p.setFont(brand_font)
        p.setPen(red2)

        # Center title: real text, no image. A wide bold font + spacing gives
        # the same compact/futuristic treatment as the reference.
        title_font = QFont("DejaVu Sans", 17)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        p.setFont(title_font)
        p.setPen(red2)
        p.drawText(QRectF(cx - 230, 3, 460, 42),
                   Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                   self._title)

        p.end()

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
