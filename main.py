import sys
import os
import time
import subprocess
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QObject,
    Signal,
    QSettings,
    QRectF,
    QPointF,
)
from PySide6.QtGui import (
    QPixmap,
    QIcon,
    QPainter,
    QPen,
    QBrush,
    QColor,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QCheckBox,
    QScrollArea,
    QDialog,
    QMessageBox,
)


# ============================================================
# ASLAN BASE WINDOW
# ============================================================

from ui.base_window import ASLANMainWindow
from auth import AuthDialog, is_session_active, logout as auth_logout
from updater import UpdatePage
from vehicle_manager import VEHICLE_MANAGER, VehicleInfoDialog, CustomEngineDialog, prepare_calculator, CUSTOM_KEY, blank_custom


# ============================================================
# APP
# ============================================================

APP_NAME = "ASLAN TUNER"

_PROFILE = os.environ.get("ASLAN_PROFILE") == "1"


def _load_app_version():

    candidates = [
        Path(__file__).resolve().with_name("version.txt"),
        Path(sys.executable).resolve().with_name("version.txt"),
    ]

    for path in candidates:

        try:

            value = path.read_text(
                encoding="utf-8"
            ).strip()

            if value:
                return value

        except (OSError, UnicodeError):

            pass

    return "1.0.0"


APP_VERSION = _load_app_version()


# ============================================================
# LOGO IMAGE
# ============================================================

def _load_logo():
    # Assets are bundled by PyInstaller under _MEIPASS/assets.
    base_dirs = [Path(__file__).resolve().parent / "assets", Path(__file__).resolve().parent]
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        base_dirs = [meipass / "assets", meipass, Path(sys.executable).resolve().parent / "assets", Path(sys.executable).resolve().parent] + base_dirs
    for base in base_dirs:
        try:
            path = base / "1000026088.png"
            if path.exists():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    return pixmap
        except Exception:
            pass
    return QPixmap()


# ============================================================
# COLORS - DARK
# ============================================================

DARK_RED = "#ff1026"
DARK_RED_DARK = "#a80012"
DARK_RED_GLOW = "#ff2638"

DARK_BG = "#08090b"
DARK_PANEL = "#0d0f12"
DARK_PANEL_2 = "#111419"
DARK_PANEL_3 = "#15181d"

DARK_WHITE = "#f4f5f7"
DARK_TEXT = "#d8dbe0"
DARK_MUTED = "#8c939d"

DARK_BORDER = "#292d34"


# ============================================================
# COLORS - LIGHT
# ============================================================

LIGHT_RED = "#e50920"
LIGHT_RED_DARK = "#b50015"
LIGHT_RED_GLOW = "#ff3045"

LIGHT_BG = "#eef0f3"
LIGHT_PANEL = "#ffffff"
LIGHT_PANEL_2 = "#f7f8fa"
LIGHT_PANEL_3 = "#e9ebef"

LIGHT_WHITE = "#17191d"
LIGHT_TEXT = "#30343a"
LIGHT_MUTED = "#6d737c"

LIGHT_BORDER = "#d5d8de"


# ============================================================
# VECTOR ICONS
# ============================================================

ICON_RED = "#ff1026"
_ICON_CACHE = {}


def create_vector_icon(
    icon_type,
    color=ICON_RED,
    size=42,
):
    """
    Creates clean vector icons using QPainter.
    No emoji or external image files are used.
    """

    cache_key = (str(icon_type), str(color), int(size))
    cached = _ICON_CACHE.get(cache_key)
    if cached is not None:
        return QIcon(cached)

    pixmap = QPixmap(
        size,
        size
    )

    pixmap.fill(
        Qt.GlobalColor.transparent
    )

    painter = QPainter(
        pixmap
    )

    painter.setRenderHint(
        QPainter.RenderHint.Antialiasing,
        True
    )

    painter.setRenderHint(
        QPainter.RenderHint.SmoothPixmapTransform,
        True
    )

    icon_color = QColor(
        color
    )

    pen = QPen(
        icon_color,
        2.4,
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin
    )

    painter.setPen(
        pen
    )

    painter.setBrush(
        Qt.BrushStyle.NoBrush
    )

    center = size / 2

    # ========================================================
    # HOME
    # ========================================================

    if icon_type == "home":

        path = QPainterPath()

        path.moveTo(
            QPointF(
                size * 0.16,
                size * 0.46
            )
        )

        path.lineTo(
            QPointF(
                center,
                size * 0.16
            )
        )

        path.lineTo(
            QPointF(
                size * 0.84,
                size * 0.46
            )
        )

        path.moveTo(
            QPointF(
                size * 0.25,
                size * 0.42
            )
        )

        path.lineTo(
            QPointF(
                size * 0.25,
                size * 0.82
            )
        )

        path.lineTo(
            QPointF(
                size * 0.75,
                size * 0.82
            )
        )

        path.lineTo(
            QPointF(
                size * 0.75,
                size * 0.42
            )
        )

        painter.drawPath(
            path
        )

        painter.drawLine(
            QPointF(
                center,
                size * 0.82
            ),
            QPointF(
                center,
                size * 0.60
            )
        )

        painter.drawLine(
            QPointF(
                center,
                size * 0.60
            ),
            QPointF(
                size * 0.58,
                size * 0.60
            )
        )

    # ========================================================
    # CALCULATOR
    # ========================================================

    elif icon_type == "calculator":

        body = QRectF(
            size * 0.20,
            size * 0.10,
            size * 0.60,
            size * 0.80
        )

        painter.drawRoundedRect(
            body,
            size * 0.08,
            size * 0.08
        )

        display = QRectF(
            size * 0.29,
            size * 0.20,
            size * 0.42,
            size * 0.16
        )

        painter.drawRoundedRect(
            display,
            size * 0.025,
            size * 0.025
        )

        button_size = size * 0.085

        positions = [
            (0.30, 0.47),
            (0.46, 0.47),
            (0.62, 0.47),

            (0.30, 0.63),
            (0.46, 0.63),
            (0.62, 0.63),

            (0.30, 0.79),
            (0.46, 0.79),
            (0.62, 0.79),
        ]

        for x, y in positions:

            painter.setBrush(
                QBrush(
                    icon_color
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    size * x,
                    size * y,
                    button_size,
                    button_size
                ),
                1.5,
                1.5
            )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

    # ========================================================
    # ECU
    # ========================================================

    elif icon_type == "ecu":

        chip = QRectF(
            size * 0.25,
            size * 0.23,
            size * 0.50,
            size * 0.54
        )

        painter.drawRoundedRect(
            chip,
            3,
            3
        )

        # Pins - left/right

        for y in (
            0.31,
            0.43,
            0.55,
            0.67,
        ):

            painter.drawLine(
                QPointF(
                    size * 0.13,
                    size * y
                ),
                QPointF(
                    size * 0.25,
                    size * y
                )
            )

            painter.drawLine(
                QPointF(
                    size * 0.75,
                    size * y
                ),
                QPointF(
                    size * 0.87,
                    size * y
                )
            )

        # Pins - top/bottom

        for x in (
            0.34,
            0.50,
            0.66,
        ):

            painter.drawLine(
                QPointF(
                    size * x,
                    size * 0.13
                ),
                QPointF(
                    size * x,
                    size * 0.23
                )
            )

            painter.drawLine(
                QPointF(
                    size * x,
                    size * 0.77
                ),
                QPointF(
                    size * x,
                    size * 0.87
                )
            )

        # Inner circuit

        painter.drawRect(
            QRectF(
                size * 0.39,
                size * 0.37,
                size * 0.22,
                size * 0.26
            )
        )

        painter.drawLine(
            QPointF(
                size * 0.44,
                size * 0.43
            ),
            QPointF(
                size * 0.56,
                size * 0.43
            )
        )

        painter.drawLine(
            QPointF(
                size * 0.44,
                size * 0.50
            ),
            QPointF(
                size * 0.56,
                size * 0.50
            )
        )

        painter.drawLine(
            QPointF(
                size * 0.44,
                size * 0.57
            ),
            QPointF(
                size * 0.56,
                size * 0.57
            )
        )

    # ========================================================
    # VEHICLE
    # ========================================================

    elif icon_type == "vehicle":

        path = QPainterPath()

        path.moveTo(
            QPointF(
                size * 0.13,
                size * 0.62
            )
        )

        path.lineTo(
            QPointF(
                size * 0.20,
                size * 0.43
            )
        )

        path.lineTo(
            QPointF(
                size * 0.34,
                size * 0.36
            )
        )

        path.lineTo(
            QPointF(
                size * 0.63,
                size * 0.36
            )
        )

        path.lineTo(
            QPointF(
                size * 0.78,
                size * 0.46
            )
        )

        path.lineTo(
            QPointF(
                size * 0.86,
                size * 0.62
            )
        )

        path.lineTo(
            QPointF(
                size * 0.86,
                size * 0.73
            )
        )

        path.lineTo(
            QPointF(
                size * 0.13,
                size * 0.73
            )
        )

        path.closeSubpath()

        painter.drawPath(
            path
        )

        # Windows

        window_path = QPainterPath()

        window_path.moveTo(
            QPointF(
                size * 0.29,
                size * 0.42
            )
        )

        window_path.lineTo(
            QPointF(
                size * 0.40,
                size * 0.42
            )
        )

        window_path.lineTo(
            QPointF(
                size * 0.40,
                size * 0.53
            )
        )

        window_path.lineTo(
            QPointF(
                size * 0.25,
                size * 0.53
            )
        )

        window_path.closeSubpath()

        painter.drawPath(
            window_path
        )

        window_path2 = QPainterPath()

        window_path2.moveTo(
            QPointF(
                size * 0.44,
                size * 0.42
            )
        )

        window_path2.lineTo(
            QPointF(
                size * 0.61,
                size * 0.42
            )
        )

        window_path2.lineTo(
            QPointF(
                size * 0.72,
                size * 0.53
            )
        )

        window_path2.lineTo(
            QPointF(
                size * 0.44,
                size * 0.53
            )
        )

        window_path2.closeSubpath()

        painter.drawPath(
            window_path2
        )

        # Wheels

        painter.setBrush(
            QBrush(
                icon_color
            )
        )

        painter.drawEllipse(
            QRectF(
                size * 0.22,
                size * 0.64,
                size * 0.15,
                size * 0.15
            )
        )

        painter.drawEllipse(
            QRectF(
                size * 0.63,
                size * 0.64,
                size * 0.15,
                size * 0.15
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

    # ========================================================
    # CALCULATOR / UPDATE VECTOR ICONS
    # ========================================================

    elif icon_type in {"lambda", "stoich", "ve", "injector", "throttle", "runner", "power", "turbo", "header", "update"}:
        painter.save()
        painter.setPen(QPen(icon_color, max(2.0, size * 0.075), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if icon_type == "lambda":
            painter.drawArc(QRectF(size*.22,size*.16,size*.56,size*.68),205*16,130*16)
            painter.drawLine(QPointF(size*.38,size*.24),QPointF(size*.50,size*.70)); painter.drawLine(QPointF(size*.50,size*.70),QPointF(size*.67,size*.24))
        elif icon_type == "stoich":
            painter.drawEllipse(QRectF(size*.25,size*.25,size*.50,size*.50)); painter.drawLine(QPointF(size*.50,size*.17),QPointF(size*.50,size*.83)); painter.drawLine(QPointF(size*.17,size*.50),QPointF(size*.83,size*.50))
        elif icon_type == "ve":
            pts=[(.18,.72,.36,.52),(.36,.52,.50,.63),(.50,.63,.82,.25)]; [painter.drawLine(QPointF(size*a,size*b),QPointF(size*c,size*d)) for a,b,c,d in pts]
            painter.drawLine(QPointF(size*.72,size*.25),QPointF(size*.82,size*.25)); painter.drawLine(QPointF(size*.82,size*.25),QPointF(size*.82,size*.35))
        elif icon_type == "injector":
            painter.drawRoundedRect(QRectF(size*.34,size*.18,size*.32,size*.44),size*.05,size*.05); painter.drawLine(QPointF(size*.50,size*.62),QPointF(size*.50,size*.78)); painter.drawLine(QPointF(size*.40,size*.78),QPointF(size*.60,size*.78)); painter.drawLine(QPointF(size*.44,size*.83),QPointF(size*.56,size*.83))
        elif icon_type == "throttle":
            painter.drawEllipse(QRectF(size*.18,size*.18,size*.64,size*.64)); painter.drawLine(QPointF(size*.24,size*.70),QPointF(size*.76,size*.30)); painter.drawEllipse(QRectF(size*.44,size*.44,size*.12,size*.12))
        elif icon_type == "runner":
            path=QPainterPath(); path.moveTo(size*.18,size*.70); path.cubicTo(size*.30,size*.70,size*.30,size*.30,size*.45,size*.30); path.lineTo(size*.76,size*.30); painter.drawPath(path); painter.drawLine(QPointF(size*.60,size*.22),QPointF(size*.76,size*.30)); painter.drawLine(QPointF(size*.60,size*.38),QPointF(size*.76,size*.30))
        elif icon_type == "power":
            painter.drawArc(QRectF(size*.20,size*.20,size*.60,size*.60),35*16,290*16); painter.drawLine(QPointF(size*.50,size*.12),QPointF(size*.50,size*.50)); painter.drawLine(QPointF(size*.50,size*.50),QPointF(size*.70,size*.50))
        elif icon_type == "turbo":
            painter.drawEllipse(QRectF(size*.18,size*.18,size*.64,size*.64)); painter.drawEllipse(QRectF(size*.38,size*.38,size*.24,size*.24)); painter.drawLine(QPointF(size*.50,size*.10),QPointF(size*.50,size*.22)); painter.drawLine(QPointF(size*.50,size*.78),QPointF(size*.50,size*.90))
        elif icon_type == "header":
            for off in (.0,.18,.36):
                path=QPainterPath(); path.moveTo(size*(.25+off),size*.18); path.cubicTo(size*(.18+off),size*.42,size*(.34+off),size*.56,size*(.28+off),size*.82); painter.drawPath(path)
        elif icon_type == "update":
            painter.drawArc(QRectF(size*.20,size*.20,size*.60,size*.60),45*16,260*16); path=QPainterPath(); path.moveTo(size*.68,size*.20); path.lineTo(size*.82,size*.22); path.lineTo(size*.75,size*.34); painter.drawPath(path)
        painter.restore()

    # SETTINGS / GEAR
    # ========================================================

    elif icon_type == "settings":

        painter.save()

        painter.translate(
            center,
            center
        )

        # Gear teeth

        painter.setBrush(
            QBrush(
                icon_color
            )
        )

        for i in range(8):

            painter.save()

            painter.rotate(
                i * 45
            )

            painter.drawRoundedRect(
                QRectF(
                    -size * 0.065,
                    -size * 0.43,
                    size * 0.13,
                    size * 0.19
                ),
                2,
                2
            )

            painter.restore()

        # Gear body

        painter.drawEllipse(
            QRectF(
                -size * 0.30,
                -size * 0.30,
                size * 0.60,
                size * 0.60
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    color
                ),
                2.5
            )
        )

        painter.drawEllipse(
            QRectF(
                -size * 0.12,
                -size * 0.12,
                size * 0.24,
                size * 0.24
            )
        )

        painter.restore()

    painter.end()

    _ICON_CACHE[cache_key] = QPixmap(pixmap)
    return QIcon(pixmap)


# ============================================================
# LANGUAGE MANAGER
# ============================================================

class LanguageManager(QObject):

    language_changed = Signal(str)

    def __init__(self):

        super().__init__()

        self._language = "en"

    @property
    def language(self):

        return self._language

    def set_language(self, language):

        if language not in ("en", "fa"):

            return

        if language == self._language:

            return

        self._language = language

        self.language_changed.emit(
            language
        )

    def is_persian(self):

        return self._language == "fa"

    def text(self, en, fa):

        if self._language == "fa":

            return fa

        return en


# ============================================================
# LOGO WIDGET
# ============================================================

class AslanLogo(QLabel):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setMinimumSize(
            150,
            190
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.setFixedHeight(
            190
        )

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setStyleSheet(
            "background: transparent;"
        )

        pixmap = _load_logo()

        if not pixmap.isNull():

            scaled_pixmap = pixmap.scaled(
                150,
                150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.setPixmap(
                scaled_pixmap
            )


# ============================================================
# SIDEBAR MENU BUTTON
# ============================================================

class SidebarButton(QPushButton):

    def __init__(
        self,
        icon,
        english,
        persian,
        language_manager,
        parent=None,
    ):

        super().__init__(parent)

        self.icon_type = icon

        self.english_text = english
        self.persian_text = persian

        self.language_manager = language_manager

        self.setMinimumHeight(
            52
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.setObjectName(
            "SidebarButton"
        )

        self.setIcon(
            create_vector_icon(
                self.icon_type,
                ICON_RED,
                26
            )
        )

        self.setIconSize(
            self.iconSize()
        )

        self.update_text()

        self.language_manager.language_changed.connect(
            self.update_text
        )

    def update_text(self, *_):

        text = self.language_manager.text(
            self.english_text,
            self.persian_text
        )

        self.setText(
            text
        )


# ============================================================
# DASHBOARD CARD
# ============================================================

class DashboardCard(QFrame):

    clicked = Signal()

    def __init__(
        self,
        icon,
        english_title,
        persian_title,
        english_description,
        persian_description,
        language_manager,
        parent=None,
    ):

        super().__init__(parent)

        self.icon_type = icon

        self.english_title = english_title
        self.persian_title = persian_title

        self.english_description = english_description
        self.persian_description = persian_description

        self.language_manager = language_manager

        self.setObjectName(
            "DashboardCard"
        )

        self.setMinimumHeight(
            215
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            22,
            20,
            22,
            18
        )

        layout.setSpacing(
            8
        )

        # ----------------------------------------------------
        # ICON
        # ----------------------------------------------------

        self.icon_label = QLabel()

        self.icon_label.setObjectName(
            "CardIcon"
        )

        self.icon_label.setFixedHeight(
            42
        )

        self.icon_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        self.icon_label.setPixmap(
            create_vector_icon(
                self.icon_type,
                ICON_RED,
                42
            ).pixmap(
                42,
                42
            )
        )

        layout.addWidget(
            self.icon_label
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.title_label = QLabel()

        self.title_label.setObjectName(
            "CardTitle"
        )

        self.title_label.setWordWrap(
            True
        )

        self.title_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        layout.addWidget(
            self.title_label
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        self.description_label = QLabel()

        self.description_label.setObjectName(
            "CardDescription"
        )

        self.description_label.setWordWrap(
            True
        )

        self.description_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        layout.addWidget(
            self.description_label
        )

        layout.addStretch()

        # ----------------------------------------------------
        # ARROW
        # ----------------------------------------------------

        bottom_layout = QHBoxLayout()

        bottom_layout.setContentsMargins(
            0,
            5,
            0,
            0
        )

        bottom_layout.addStretch()

        self.arrow = QLabel(
            "→"
        )

        self.arrow.setObjectName(
            "CardArrow"
        )

        self.arrow.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.arrow.setFixedSize(
            36,
            36
        )

        self.arrow.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True
        )

        bottom_layout.addWidget(
            self.arrow
        )

        layout.addLayout(
            bottom_layout
        )

        # ----------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------

        self.language_manager.language_changed.connect(
            self.update_language
        )

        self.update_language(
            self.language_manager.language
        )

    # ========================================================
    # LANGUAGE
    # ========================================================

    def update_language(self, language):

        self.title_label.setText(
            self.language_manager.text(
                self.english_title,
                self.persian_title
            )
        )

        self.description_label.setText(
            self.language_manager.text(
                self.english_description,
                self.persian_description
            )
        )

        self.arrow.setText(
            "←"
            if language == "fa"
            else "→"
        )

    # ========================================================
    # CLICK
    # ========================================================

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.clicked.emit()

            event.accept()

            return

        super().mousePressEvent(
            event
        )


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(QWidget):

    navigate = Signal(str)

    def __init__(
        self,
        language_manager,
        parent=None,
    ):

        super().__init__(parent)

        self.language_manager = language_manager

        self.setObjectName(
            "Dashboard"
        )

        self.build_ui()

        self.language_manager.language_changed.connect(
            self.update_language
        )

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            38,
            30,
            38,
            30
        )

        main_layout.setSpacing(
            0
        )

        # ----------------------------------------------------
        # WELCOME
        # ----------------------------------------------------

        self.welcome_label = QLabel()

        self.welcome_label.setObjectName(
            "WelcomeLabel"
        )

        main_layout.addWidget(
            self.welcome_label
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.title_label = QLabel()

        self.title_label.setObjectName(
            "DashboardTitle"
        )

        main_layout.addWidget(
            self.title_label
        )

        # ----------------------------------------------------
        # SUBTITLE
        # ----------------------------------------------------

        self.subtitle_label = QLabel()

        self.subtitle_label.setObjectName(
            "DashboardSubtitle"
        )

        main_layout.addWidget(
            self.subtitle_label
        )

        # ----------------------------------------------------
        # RED LINE
        # ----------------------------------------------------

        self.red_line = QFrame()

        self.red_line.setObjectName(
            "RedLine"
        )

        self.red_line.setFixedSize(
            66,
            4
        )

        main_layout.addSpacing(
            17
        )

        main_layout.addWidget(
            self.red_line
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        self.description_label = QLabel()

        self.description_label.setObjectName(
            "DashboardDescription"
        )

        self.description_label.setWordWrap(
            True
        )

        main_layout.addSpacing(
            20
        )

        main_layout.addWidget(
            self.description_label
        )

        # ----------------------------------------------------
        # CARDS
        # ----------------------------------------------------

        main_layout.addSpacing(
            28
        )

        self.cards_layout = QGridLayout()

        self.cards_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.cards_layout.setHorizontalSpacing(
            16
        )

        self.cards_layout.setVerticalSpacing(
            16
        )

        main_layout.addLayout(
            self.cards_layout
        )

        main_layout.addStretch()

        # ----------------------------------------------------
        # CREATE CARDS
        # ----------------------------------------------------

        self.calculators_card = DashboardCard(
            "calculator",
            "Calculators",
            "محاسبات",
            "Engine, turbo, injector, VE and more...",
            "محاسبات موتور، توربو، انژکتور، VE و موارد دیگر",
            self.language_manager,
        )

        self.ecu_card = DashboardCard(
            "ecu",
            "ECU Tools",
            "ابزار ECU",
            "Read, write, map and analyze ECU data.",
            "خواندن، نوشتن، مپ و تحلیل اطلاعات ECU",
            self.language_manager,
        )

        self.vehicles_card = DashboardCard(
            "vehicle",
            "Vehicles",
            "خودروها",
            "Vehicle presets and configuration.",
            "پروفایل و تنظیمات خودروها",
            self.language_manager,
        )

        self.settings_card = DashboardCard(
            "settings",
            "Settings",
            "تنظیمات",
            "App preferences, appearance and language.",
            "تنظیمات برنامه، ظاهر و زبان",
            self.language_manager,
        )

        cards = [
            self.calculators_card,
            self.ecu_card,
            self.vehicles_card,
            self.settings_card,
        ]

        # ----------------------------------------------------
        # HOME CARD LAYOUT
        #
        # Kept exactly as the Home layout.
        # Home responsiveness is intentionally untouched.
        # ----------------------------------------------------

        for index, card in enumerate(cards):

            row = index // 4
            column = index % 4

            self.cards_layout.addWidget(
                card,
                row,
                column
            )

        for column in range(4):

            self.cards_layout.setColumnStretch(
                column,
                1
            )

        # ====================================================
        # CONNECT DASHBOARD CARDS
        # ====================================================

        self.calculators_card.clicked.connect(
            lambda: self.navigate.emit("calculators")
        )

        self.ecu_card.clicked.connect(
            lambda: self.navigate.emit("ecu")
        )

        self.vehicles_card.clicked.connect(
            lambda: self.navigate.emit("vehicles")
        )

        self.settings_card.clicked.connect(
            lambda: self.navigate.emit("settings")
        )

        self.update_language(
            self.language_manager.language
        )

    # ========================================================
    # LANGUAGE
    # ========================================================

    def update_language(self, language):

        self.welcome_label.setText(
            self.language_manager.text(
                "Welcome to",
                "خوش آمدید به"
            )
        )

        self.title_label.setText(
            "ASLAN TUNER"
        )

        self.subtitle_label.setText(
            self.language_manager.text(
                "Professional Engine & ECU Tuning Suite",
                "مجموعه حرفه‌ای تیونینگ موتور و ECU"
            )
        )

        self.description_label.setText(
            self.language_manager.text(
                "Optimize your engine performance, calculate with "
                "precision, and take control of your ECU.",
                "عملکرد موتور خود را بهینه کنید، محاسبات را با دقت "
                "انجام دهید و کنترل ECU را در اختیار بگیرید."
            )
        )


# ============================================================
# RESPONSIVE PAGE SCROLL CONTAINER
# ============================================================

class ResponsivePage(QWidget):

    """
    Container used only by internal pages.

    Home is NOT using this class.
    It allows internal pages to remain usable when the
    application becomes short or narrow.
    """

    def __init__(
        self,
        language_manager,
        parent=None,
    ):

        super().__init__(parent)

        self.language_manager = language_manager

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer_layout.setSpacing(
            0
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_area.setWidget(
            self.create_content()
        )

        outer_layout.addWidget(
            self.scroll_area
        )

    def create_content(self):

        content = QWidget()

        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        return content


# ============================================================
# CALCULATORS
# ============================================================

class Calculators(QWidget):

    def __init__(
        self,
        language_manager,
        parent=None,
    ):

        super().__init__(parent)

        self.language_manager = language_manager

        self.setObjectName(
            "CalculatorsPage"
        )

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer_layout.setSpacing(
            0
        )

        # ====================================================
        # SCROLL AREA
        # ====================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        # ====================================================
        # CONTENT
        # ====================================================

        self.content_widget = QWidget()

        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QVBoxLayout(
            self.content_widget
        )

        layout.setContentsMargins(
            38,
            30,
            38,
            30
        )

        self.title = QLabel()

        self.title.setObjectName(
            "PageTitle"
        )

        layout.addWidget(
            self.title
        )

        self.subtitle = QLabel()

        self.subtitle.setObjectName(
            "Subtitle"
        )

        self.subtitle.setWordWrap(
            True
        )

        layout.addWidget(
            self.subtitle
        )

        layout.addSpacing(
            20
        )

        # ====================================================
        # RESPONSIVE CALCULATOR GRID
        # ====================================================

        self.calculator_grid = QGridLayout()

        self.calculator_grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.calculator_grid.setHorizontalSpacing(
            12
        )

        self.calculator_grid.setVerticalSpacing(
            12
        )

        layout.addLayout(
            self.calculator_grid
        )

        self.calculator_buttons = []

        calculators = [
            ("lambda", "LAMBDA"),
            ("stoich", "STOICHIOMETRIC"),
            ("ve", "VE"),
            ("injector", "INJECTOR FLOW"),
            ("throttle", "THROTTLE BODY"),
            ("runner", "INTAKE RUNNER"),
            ("power", "POWER / TORQUE"),
            ("turbo", "TURBO SIZING"),
            ("header", "HEADER SIZE"),
        ]

        for icon, name in calculators:

            button = QPushButton(name)
            button.setIcon(create_vector_icon(icon, ICON_RED, 28))
            button.setIconSize(button.icon().actualSize(button.iconSize()))

            button.setMinimumHeight(
                52
            )

            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )

            button.setObjectName(
                "ToolButton"
            )

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            if name == "LAMBDA":

                button.clicked.connect(
                    self.open_afr_calculator
                )

            elif name == "STOICHIOMETRIC":

                button.clicked.connect(
                    self.open_stoich_calculator
                )

            elif name == "VE":

                button.clicked.connect(
                    self.open_ve_calculator
                )

            elif name == "INJECTOR FLOW":

                button.clicked.connect(
                    self.open_injector_flow
                )

            elif name == "THROTTLE BODY":

                button.clicked.connect(
                    self.open_throttle_body
                )

            elif name == "INTAKE RUNNER":

                button.clicked.connect(
                    self.open_runner_calculator
                )

            elif name == "POWER / TORQUE":

                button.clicked.connect(
                    self.open_power_torque
                )

            elif name == "TURBO SIZING":

                button.clicked.connect(
                    self.open_turbo_calculator
                )

            elif name == "HEADER SIZE":

                button.clicked.connect(
                    self.open_header
                )

            self.calculator_buttons.append(
                button
            )

        # ====================================================
        # KEEP BOTTOM SPACE
        # ====================================================

        layout.addSpacing(
            20
        )

        self.scroll_area.setWidget(
            self.content_widget
        )

        # ====================================================
        # INITIAL GRID
        # ====================================================

        self._calculator_columns = 0

        self.update_calculator_grid()

        self.language_manager.language_changed.connect(
            self.update_language
        )

        self.update_language(
            self.language_manager.language
        )

    # ========================================================
    # CALCULATOR RESPONSIVENESS
    # ========================================================

    def resizeEvent(self, event):

        super().resizeEvent(
            event
        )

        self.update_calculator_grid()

    def update_calculator_grid(self):

        available_width = (
            self.width()
            - 76
        )

        if available_width >= 900:

            columns = 3

        elif available_width >= 580:

            columns = 2

        else:

            columns = 1

        if columns == self._calculator_columns:

            return

        self._calculator_columns = columns

        # ----------------------------------------------------
        # Remove existing items
        # ----------------------------------------------------

        while self.calculator_grid.count():

            item = self.calculator_grid.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.setParent(
                    self.content_widget
                )

        # ----------------------------------------------------
        # Reset stretches
        # ----------------------------------------------------

        for column in range(4):

            self.calculator_grid.setColumnStretch(
                column,
                0
            )

        # ----------------------------------------------------
        # Add buttons
        # ----------------------------------------------------

        for index, button in enumerate(
            self.calculator_buttons
        ):

            row = index // columns
            column = index % columns

            self.calculator_grid.addWidget(
                button,
                row,
                column
            )

        # ----------------------------------------------------
        # Equal width columns
        # ----------------------------------------------------

        for column in range(columns):

            self.calculator_grid.setColumnStretch(
                column,
                1
            )

    # ========================================================
    # LANGUAGE
    # ========================================================

    def update_language(self, language):

        self.title.setText(
            self.language_manager.text(
                "ENGINE CALCULATORS",
                "محاسبات موتور"
            )
        )

        self.subtitle.setText(
            self.language_manager.text(
                "Engine and fuel system calculations",
                "محاسبات موتور و سیستم سوخت‌رسانی"
            )
        )

    # ========================================================
    # CALCULATORS
    # ========================================================

    def open_afr_calculator(self):

        from calculators.afr_lambda import AFRLambdaCalculator

        calculator = AFRLambdaCalculator(self)
        prepare_calculator(calculator, "AFR / LAMBDA")
        calculator.exec()

    def open_stoich_calculator(self):

        from calculators.stoich import StoichCalculator

        calculator = StoichCalculator(self)
        prepare_calculator(calculator, "STOICHIOMETRIC RATIO")
        calculator.exec()

    def open_ve_calculator(self):

        from calculators.ve import VECalculator

        params = {
            "displacement": 2000,
            "torque": 170,
            "idle_rpm": 800,
            "rpm_torque": 3000,
            "rpm_power": 5000,
            "cutoff": 7000,
            "rows": 16,
            "columns": 16,
        }

        calculator = VECalculator(params=params, parent=self)
        prepare_calculator(calculator, "VE ENGINE")
        calculator.exec()

    def open_injector_flow(self):

        from calculators.injector_flow import InjectorFlowCalculator

        calculator = InjectorFlowCalculator(parent=self)
        prepare_calculator(calculator, "INJECTOR FLOW")
        calculator.exec()

    def open_throttle_body(self):

        from calculators.throttle import ThrottleBodyCalculator

        calculator = ThrottleBodyCalculator(parent=self)
        prepare_calculator(calculator, "THROTTLE BODY")
        calculator.exec()

    def open_runner_calculator(self):

        from calculators.runner import RunnerCalculator

        calculator = RunnerCalculator(parent=self)
        prepare_calculator(calculator, "INTAKE RUNNER")
        calculator.exec()

    def open_power_torque(self):

        from calculators.power_torque import PowerTorqueCalculator

        calculator = PowerTorqueCalculator(parent=self)
        prepare_calculator(calculator, "POWER / TORQUE")
        calculator.exec()

    def open_turbo_calculator(self):

        from calculators.turbo import TurboCalculator

        calculator = TurboCalculator(parent=self)
        prepare_calculator(calculator, "TURBO SIZING")
        calculator.exec()

    def open_header(self):

        from calculators.header import HeaderCalculator

        calculator = HeaderCalculator(self)
        prepare_calculator(calculator, "HEADER ENGINEERING")
        calculator.exec()


# ============================================================
# ECU TOOLS
# ============================================================

class ECUTools(QWidget):

    def __init__(
        self,
        language_manager,
        parent=None,
    ):

        super().__init__(parent)

        self.language_manager = language_manager

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer_layout.setSpacing(
            0
        )

        # ====================================================
        # SCROLL AREA
        # ====================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        # ====================================================
        # CONTENT
        # ====================================================

        self.content_widget = QWidget()

        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        layout = QVBoxLayout(
            self.content_widget
        )

        layout.setContentsMargins(
            38,
            30,
            38,
            30
        )

        self.title = QLabel()

        self.title.setObjectName(
            "PageTitle"
        )

        layout.addWidget(
            self.title
        )

        self.subtitle = QLabel()

        self.subtitle.setObjectName(
            "Subtitle"
        )

        self.subtitle.setWordWrap(
            True
        )

        layout.addWidget(
            self.subtitle
        )

        layout.addSpacing(
            20
        )

        button = QPushButton(
            "ENGINE DYNO SIMULATOR"
        )

        button.setMinimumHeight(
            52
        )

        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        button.setObjectName(
            "ToolButton"
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            self.open_engine_dyno
        )

        layout.addWidget(
            button
        )

        self.warning = QLabel()

        self.warning.setObjectName(
            "Warning"
        )

        self.warning.setWordWrap(
            True
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            self.warning
        )

        layout.addSpacing(
            20
        )

        self.scroll_area.setWidget(
            self.content_widget
        )

        self.language_manager.language_changed.connect(
            self.update_language
        )

        self.update_language(
            self.language_manager.language
        )

    def update_language(self, language):

        self.title.setText(
            self.language_manager.text(
                "ECU TOOLS",
                "ابزارهای ECU"
            )
        )

        self.subtitle.setText(
            self.language_manager.text(
                "Tools for ECU analysis and file management",
                "ابزارهای تحلیل و مدیریت فایل ECU"
            )
        )

        self.warning.setText(
            self.language_manager.text(
                "⚠ ECU editing will only be enabled when "
                "the ECU definition is verified.",
                "⚠ ویرایش ECU تنها پس از تأیید تعریف ECU فعال خواهد شد."
            )
        )

    def open_engine_dyno(self):

        from ecu_tools.engine_dyno import EngineDynoSimulator

        calculator = EngineDynoSimulator(parent=self)
        prepare_calculator(calculator, "ENGINE DYNO SIMULATOR")
        calculator.exec()

        # Keep the dyno result available to the same vehicle context.
        # Calculator formulas remain untouched; only their input source is updated.
        if VEHICLE_MANAGER.selected_params and getattr(calculator, "last_result", None):
            result = calculator.last_result
            peak_hp = result.get("peak_hp") or {}
            peak_torque = result.get("peak_torque") or {}
            if peak_hp.get("hp") is not None:
                VEHICLE_MANAGER.selected_params["dyno_peak_power"] = peak_hp["hp"]
                VEHICLE_MANAGER.selected_params["dyno_peak_power_rpm"] = peak_hp.get("rpm", 0)
            if peak_torque.get("torque_nm") is not None:
                VEHICLE_MANAGER.selected_params["dyno_peak_torque"] = peak_torque["torque_nm"]
                VEHICLE_MANAGER.selected_params["dyno_peak_torque_rpm"] = peak_torque.get("rpm", 0)
            self.update_active_vehicle_badge()
            if hasattr(self, "vehicles_page"):
                self.vehicles_page.update_active()


# ============================================================
# VEHICLES
# ============================================================

class Vehicles(QWidget):

    def __init__(self, language_manager, parent=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.cards = {}

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(34, 28, 34, 34)
        layout.setSpacing(14)

        self.title = QLabel()
        self.title.setObjectName("PageTitle")
        layout.addWidget(self.title)

        self.subtitle = QLabel()
        self.subtitle.setObjectName("Subtitle")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)

        self.active_banner = QFrame()
        self.active_banner.setObjectName("ActiveVehicleBanner")
        banner = QHBoxLayout(self.active_banner)
        banner.setContentsMargins(16, 12, 16, 12)
        self.active_label = QLabel("NO ACTIVE VEHICLE")
        self.active_label.setObjectName("ActiveVehicleText")
        banner.addWidget(self.active_label)
        banner.addStretch()
        self.clear_button = QPushButton("CLEAR")
        self.clear_button.setObjectName("ToolButton")
        self.clear_button.clicked.connect(self.clear_active)
        banner.addWidget(self.clear_button)
        layout.addWidget(self.active_banner)

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setContentsMargins(0, 4, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        layout.addWidget(self.grid_widget)
        layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        outer_layout.addWidget(self.scroll_area)

        self.language_manager.language_changed.connect(self.update_language)
        self.update_language(self.language_manager.language)
        self.refresh_cards()

        self.setStyleSheet("""
            QWidget#Vehicles { background:#090b0e; }
            QFrame#ActiveVehicleBanner {
                background:#111419;
                border:1px solid #3a2025;
                border-radius:14px;
            }
            QLabel#ActiveVehicleText { color:#ff3045; font-size:12px; font-weight:800; }
            QFrame#VehicleCard {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #15191f, stop:0.55 #101318, stop:1 #0c0f13);
                border:1px solid #2d333c;
                border-radius:16px;
            }
            QFrame#VehicleCard:hover {
                border:1px solid #e90018;
                background:#15171c;
            }
            QFrame#VehicleCard[selected="true"] {
                border:1px solid #ff1730;
                background:#1a1014;
            }
            QFrame#VehicleCard[custom="true"] {
                border:1px solid #7d1825;
            }
            QLabel#VehicleName { color:#f2f3f5; font-size:17px; font-weight:800; }
            QLabel#VehicleEngine { color:#8f97a1; font-size:11px; }
            QLabel#VehicleSpec { color:#c8ccd2; font-size:11px; }
            QLabel#CustomBadge { color:#ff3145; font-size:10px; font-weight:900; }
            QPushButton#VehicleAction {
                background:#161a20; color:#e3e5e8; border:1px solid #303640;
                border-radius:9px; padding:8px 10px; font-weight:700;
            }
            QPushButton#VehicleAction:hover { border-color:#e90018; background:#1e2229; }
            QPushButton#VehicleUse {
                background:#c90017; color:white; border:1px solid #ff3045;
                border-radius:9px; padding:8px 10px; font-weight:800;
            }
            QPushButton#VehicleUse:hover { background:#ff172b; }
            QPushButton#VehicleDelete {
                background:#171116; color:#ff5363; border:1px solid #5a2029;
                border-radius:9px; padding:7px 10px; font-weight:800;
            }
            QPushButton#VehicleDelete:hover { background:#2a1117; border-color:#ef1730; color:#ff7b88; }
        """)

    def refresh_cards(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.cards.clear()

        profiles = VEHICLE_MANAGER.all_profiles()
        if CUSTOM_KEY not in profiles:
            profiles[CUSTOM_KEY] = blank_custom()
        keys = list(profiles.keys())
        columns = self._vehicle_columns()
        self._vehicle_keys = keys
        for index, key in enumerate(keys):
            card = self._make_card(key, profiles[key])
            self.cards[key] = card
            self.grid.addWidget(card, index // columns, index % columns)
        for c in range(columns):
            self.grid.setColumnStretch(c, 1)

    def _vehicle_columns(self):
        width = max(360, self.width() - 80)
        if width >= 1150:
            return 3
        if width >= 720:
            return 2
        return 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_vehicle_keys"):
            self.refresh_cards()

    def _make_card(self, key, params):
        card = QFrame()
        card.setObjectName("VehicleCard")
        card.setProperty("selected", key == VEHICLE_MANAGER.selected_key)
        card.setProperty("custom", key == CUSTOM_KEY or key.startswith("CUSTOM::"))
        card.setMinimumHeight(170)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 16, 18, 16)
        box.setSpacing(7)

        top = QHBoxLayout()
        name = QLabel(params.get("display_name", key))
        name.setObjectName("VehicleName")
        top.addWidget(name)
        top.addStretch()
        if key.startswith("CUSTOM::") or key == CUSTOM_KEY:
            badge = QLabel("CUSTOM")
            badge.setObjectName("CustomBadge")
            top.addWidget(badge)
        box.addLayout(top)

        engine = QLabel(params.get("engine_name", "—"))
        engine.setObjectName("VehicleEngine")
        box.addWidget(engine)

        spec = QLabel(
            f"{params.get('displacement', '—')} cc  •  "
            f"{params.get('cylinders', '—')} cyl  •  "
            f"{params.get('power', '—')} hp  •  "
            f"{params.get('torque', '—')} Nm"
        )
        spec.setObjectName("VehicleSpec")
        box.addWidget(spec)

        box.addStretch()

        actions = QHBoxLayout()
        info = QPushButton("VIEW INFORMATION")
        info.setObjectName("VehicleAction")
        use = QPushButton("USE PARAMETERS")
        use.setObjectName("VehicleUse")
        is_saved_custom = key.startswith("CUSTOM::")
        if key == CUSTOM_KEY:
            info.setText("ADD / EDIT ENGINE")
            use.setText("CREATE PROFILE")
            info.clicked.connect(lambda _=False: self.edit_custom())
            use.clicked.connect(lambda _=False: self.edit_custom())
            actions.addWidget(info)
            actions.addWidget(use)
        elif is_saved_custom:
            info.setText("EDIT PROFILE")
            info.clicked.connect(lambda _=False, k=key: self.edit_custom(k))
            use.clicked.connect(lambda _=False, k=key: self.use_vehicle(k))
            actions.addWidget(info)
            actions.addWidget(use)
            box.addLayout(actions)

            delete_row = QHBoxLayout()
            delete_row.setContentsMargins(0, 0, 0, 0)
            delete_btn = QPushButton("DELETE PROFILE")
            delete_btn.setObjectName("VehicleDelete")
            delete_btn.clicked.connect(lambda _=False, k=key: self.delete_custom(k))
            delete_row.addWidget(delete_btn)
            box.addLayout(delete_row)
            # The custom card has already been laid out.
            card.mousePressEvent = lambda event, k=key: self.card_clicked(event, k)
            return card
        else:
            info.clicked.connect(lambda _=False, k=key: self.show_info(k))
            use.clicked.connect(lambda _=False, k=key: self.use_vehicle(k))
            actions.addWidget(info)
            actions.addWidget(use)
        box.addLayout(actions)

        # Clicking anywhere on the card opens the two-choice action sheet.
        card.mousePressEvent = lambda event, k=key: self.card_clicked(event, k)
        return card

    def card_clicked(self, event, key):
        if event.button() == Qt.MouseButton.LeftButton:
            self.show_vehicle_actions(key)

    def show_vehicle_actions(self, key):
        if key == CUSTOM_KEY:
            self.edit_custom()
            return
        params = VEHICLE_MANAGER.get(key)
        if not params:
            return
        box = QMessageBox(self)
        box.setWindowTitle(params.get("display_name", key))
        box.setText("Choose what you want to do with this vehicle.")
        box.setInformativeText("Vehicle information or load its tuning parameters into ASLAN TUNER.")
        info = box.addButton("VIEW INFORMATION", QMessageBox.ButtonRole.AcceptRole)
        use = box.addButton("USE PARAMETERS", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("CANCEL", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is info:
            self.show_info(key)
        elif box.clickedButton() is use:
            self.use_vehicle(key)

    def edit_custom(self, key=None):
        existing = VEHICLE_MANAGER.custom_profiles.get(key) if key else None
        existing_key = key if existing is not None else None
        if existing is None and VEHICLE_MANAGER.custom_profiles:
            # Backward-compatible shortcut: the generic CUSTOM ENGINE card
            # opens the most recently created profile for editing.
            existing_key = list(VEHICLE_MANAGER.custom_profiles.keys())[-1]
            existing = VEHICLE_MANAGER.custom_profiles[existing_key]
        dialog = CustomEngineDialog(existing=existing, parent=self, existing_key=existing_key)
        if dialog.exec():
            self.refresh_cards()

    def delete_custom(self, key):
        params = VEHICLE_MANAGER.custom_profiles.get(key)
        if not params:
            return
        name = params.get("display_name", key.replace("CUSTOM::", ""))
        box = QMessageBox(self)
        box.setWindowTitle("Delete custom profile")
        box.setText(f'Delete custom profile "{name}"?')
        box.setInformativeText("This removes the saved profile from this computer. It does not affect built-in vehicles.")
        yes = box.addButton("DELETE", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("CANCEL", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is yes:
            VEHICLE_MANAGER.delete_custom(key)
            self.refresh_cards()
            window = self.window()
            if hasattr(window, "update_active_vehicle_badge"):
                window.update_active_vehicle_badge()

    def show_info(self, key):
        params = VEHICLE_MANAGER.get(key)
        if params:
            VehicleInfoDialog(key, params, self).exec()

    def use_vehicle(self, key):
        if VEHICLE_MANAGER.select(key):
            self.update_active()
            self.refresh_cards()
            window = self.window()
            if hasattr(window, "update_active_vehicle_badge"):
                window.update_active_vehicle_badge()

    def clear_active(self):
        VEHICLE_MANAGER.clear()
        self.update_active()
        self.refresh_cards()
        window = self.window()
        if hasattr(window, "update_active_vehicle_badge"):
            window.update_active_vehicle_badge()

    def update_active(self):
        key = VEHICLE_MANAGER.selected_key
        params = VEHICLE_MANAGER.selected_params
        if key and params:
            self.active_label.setText(
                f"ACTIVE VEHICLE  •  {params.get('display_name', key)}  •  "
                f"{params.get('engine_name', '—')}  •  PARAMETERS LOADED"
            )
        else:
            self.active_label.setText("NO ACTIVE VEHICLE  •  CALCULATORS USE THEIR NORMAL INPUTS")

    def update_language(self, language):
        self.title.setText(
            self.language_manager.text("VEHICLE PROFILES", "پروفایل خودروها")
        )
        self.subtitle.setText(
            self.language_manager.text(
                "Select a vehicle to inspect it or load its parameters into all compatible calculators.",
                "خودرو را برای مشاهده اطلاعات یا بارگذاری پارامترها در محاسبات انتخاب کنید."
            )
        )
        self.update_active()


# ============================================================
# SETTINGS PAGE
# ============================================================

class SettingsPage(QWidget):

    theme_changed = Signal(str)

    def __init__(
        self,
        language_manager,
        initial_theme="dark",
        parent=None,
    ):

        super().__init__(parent)

        self.language_manager = language_manager

        self.current_theme = initial_theme

        self.setObjectName(
            "SettingsPage"
        )

        # ====================================================
        # OUTER
        # ====================================================

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer_layout.setSpacing(
            0
        )

        # ====================================================
        # SCROLL
        # ====================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        # ====================================================
        # CONTENT
        # ====================================================

        self.content_widget = QWidget()

        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )

        self.build_ui()

        self.scroll_area.setWidget(
            self.content_widget
        )

        self.language_manager.language_changed.connect(
            self.update_language
        )

        self.update_language(
            self.language_manager.language
        )

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        main_layout = QVBoxLayout(
            self.content_widget
        )

        main_layout.setContentsMargins(
            38,
            30,
            38,
            30
        )

        main_layout.setSpacing(
            0
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.title = QLabel()

        self.title.setObjectName(
            "PageTitle"
        )

        main_layout.addWidget(
            self.title
        )

        self.subtitle = QLabel()

        self.subtitle.setObjectName(
            "Subtitle"
        )

        self.subtitle.setWordWrap(
            True
        )

        main_layout.addSpacing(
            5
        )

        main_layout.addWidget(
            self.subtitle
        )

        # ----------------------------------------------------
        # APPEARANCE
        # ----------------------------------------------------

        main_layout.addSpacing(
            30
        )

        self.appearance_title = QLabel()

        self.appearance_title.setObjectName(
            "SettingsSectionTitle"
        )

        main_layout.addWidget(
            self.appearance_title
        )

        self.appearance_description = QLabel()

        self.appearance_description.setObjectName(
            "SettingsSectionDescription"
        )

        self.appearance_description.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.appearance_description
        )

        main_layout.addSpacing(
            14
        )

        # ----------------------------------------------------
        # THEME CARD
        # ----------------------------------------------------

        self.theme_frame = QFrame()

        self.theme_frame.setObjectName(
            "SettingsOption"
        )

        theme_layout = QHBoxLayout(
            self.theme_frame
        )

        theme_layout.setContentsMargins(
            18,
            16,
            18,
            16
        )

        theme_layout.setSpacing(
            15
        )

        self.theme_icon = QLabel(
            "☾"
        )

        self.theme_icon.setObjectName(
            "SettingsOptionIcon"
        )

        self.theme_icon.setFixedWidth(
            42
        )

        theme_layout.addWidget(
            self.theme_icon
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            3
        )

        self.theme_title = QLabel()

        self.theme_title.setObjectName(
            "SettingsOptionTitle"
        )

        self.theme_description = QLabel()

        self.theme_description.setObjectName(
            "SettingsOptionDescription"
        )

        self.theme_description.setWordWrap(
            True
        )

        text_layout.addWidget(
            self.theme_title
        )

        text_layout.addWidget(
            self.theme_description
        )

        theme_layout.addLayout(
            text_layout,
            1
        )

        # ----------------------------------------------------
        # THEME SWITCH
        # ----------------------------------------------------

        self.theme_switch = QCheckBox()

        self.theme_switch.setObjectName(
            "ThemeSwitch"
        )

        self.theme_switch.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.theme_switch.setChecked(
            self.current_theme == "light"
        )

        self.theme_switch.stateChanged.connect(
            self.on_theme_switch
        )

        theme_layout.addWidget(
            self.theme_switch
        )

        main_layout.addWidget(
            self.theme_frame
        )

        # ----------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------

        main_layout.addSpacing(
            28
        )

        self.language_section_title = QLabel()

        self.language_section_title.setObjectName(
            "SettingsSectionTitle"
        )

        main_layout.addWidget(
            self.language_section_title
        )

        self.language_section_description = QLabel()

        self.language_section_description.setObjectName(
            "SettingsSectionDescription"
        )

        self.language_section_description.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.language_section_description
        )

        main_layout.addSpacing(
            14
        )

        self.language_frame = QFrame()

        self.language_frame.setObjectName(
            "SettingsOption"
        )

        language_layout = QHBoxLayout(
            self.language_frame
        )

        language_layout.setContentsMargins(
            18,
            16,
            18,
            16
        )

        language_layout.setSpacing(
            15
        )

        self.language_icon = QLabel(
            "文"
        )

        self.language_icon.setObjectName(
            "SettingsOptionIcon"
        )

        self.language_icon.setFixedWidth(
            42
        )

        language_layout.addWidget(
            self.language_icon
        )

        language_text_layout = QVBoxLayout()

        language_text_layout.setSpacing(
            3
        )

        self.language_title = QLabel()

        self.language_title.setObjectName(
            "SettingsOptionTitle"
        )

        self.language_description = QLabel()

        self.language_description.setObjectName(
            "SettingsOptionDescription"
        )

        self.language_description.setWordWrap(
            True
        )

        language_text_layout.addWidget(
            self.language_title
        )

        language_text_layout.addWidget(
            self.language_description
        )

        language_layout.addLayout(
            language_text_layout,
            1
        )

        # ----------------------------------------------------
        # LANGUAGE BUTTONS
        # ----------------------------------------------------

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(
            7
        )

        self.english_button = QPushButton(
            "English"
        )

        self.persian_button = QPushButton(
            "فارسی"
        )

        for button in (
            self.english_button,
            self.persian_button,
        ):

            button.setObjectName(
                "SettingsLanguageButton"
            )

            button.setFixedSize(
                90,
                38
            )

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

        self.english_button.clicked.connect(
            lambda: self.language_manager.set_language("en")
        )

        self.persian_button.clicked.connect(
            lambda: self.language_manager.set_language("fa")
        )

        buttons_layout.addWidget(
            self.english_button
        )

        buttons_layout.addWidget(
            self.persian_button
        )

        language_layout.addLayout(
            buttons_layout
        )

        main_layout.addWidget(
            self.language_frame
        )

        # ----------------------------------------------------
        # APP INFO
        # ----------------------------------------------------

        main_layout.addSpacing(
            28
        )

        self.info_title = QLabel()

        self.info_title.setObjectName(
            "SettingsSectionTitle"
        )

        main_layout.addWidget(
            self.info_title
        )

        self.info_label = QLabel(
            f"ASLAN TUNER\nv{APP_VERSION}"
        )

        self.info_label.setObjectName(
            "SettingsInfo"
        )

        main_layout.addWidget(
            self.info_label
        )

        main_layout.addSpacing(
            20
        )

        self.update_theme_ui()

    # ========================================================
    # THEME SWITCH
    # ========================================================

    def on_theme_switch(self, state):

        if state == Qt.CheckState.Checked.value:

            self.current_theme = "light"

        else:

            self.current_theme = "dark"

        self.update_theme_ui()

        self.theme_changed.emit(
            self.current_theme
        )

    # ========================================================
    # UPDATE THEME UI
    # ========================================================

    def update_theme_ui(self):

        if self.current_theme == "light":

            self.theme_icon.setText(
                "☀"
            )

        else:

            self.theme_icon.setText(
                "☾"
            )

    # ========================================================
    # LANGUAGE
    # ========================================================

    def update_language(self, language):

        self.title.setText(
            self.language_manager.text(
                "SETTINGS",
                "تنظیمات"
            )
        )

        self.subtitle.setText(
            self.language_manager.text(
                "Customize ASLAN TUNER appearance and preferences.",
                "ظاهر و تنظیمات ASLAN TUNER را شخصی‌سازی کنید."
            )
        )

        self.appearance_title.setText(
            self.language_manager.text(
                "APPEARANCE",
                "ظاهر"
            )
        )

        self.appearance_description.setText(
            self.language_manager.text(
                "Choose how ASLAN TUNER looks.",
                "ظاهر برنامه را انتخاب کنید."
            )
        )

        self.theme_title.setText(
            self.language_manager.text(
                "Theme",
                "حالت نمایش"
            )
        )

        if self.current_theme == "light":

            self.theme_description.setText(
                self.language_manager.text(
                    "Light mode is currently active.",
                    "حالت روز در حال حاضر فعال است."
                )
            )

        else:

            self.theme_description.setText(
                self.language_manager.text(
                    "Dark mode is currently active.",
                    "حالت شب در حال حاضر فعال است."
                )
            )

        self.language_section_title.setText(
            self.language_manager.text(
                "LANGUAGE",
                "زبان"
            )
        )

        self.language_section_description.setText(
            self.language_manager.text(
                "Select the application language.",
                "زبان برنامه را انتخاب کنید."
            )
        )

        self.language_title.setText(
            self.language_manager.text(
                "Application Language",
                "زبان برنامه"
            )
        )

        self.language_description.setText(
            self.language_manager.text(
                "English or Persian interface.",
                "رابط کاربری انگلیسی یا فارسی."
            )
        )

        self.info_title.setText(
            self.language_manager.text(
                "ABOUT",
                "درباره برنامه"
            )
        )

        self.update_language_buttons(
            language
        )

    # ========================================================
    # LANGUAGE BUTTON STATE
    # ========================================================

    def update_language_buttons(self, language):

        self.english_button.setProperty(
            "active",
            language == "en"
        )

        self.persian_button.setProperty(
            "active",
            language == "fa"
        )

        self.english_button.style().unpolish(
            self.english_button
        )

        self.english_button.style().polish(
            self.english_button
        )

        self.persian_button.style().unpolish(
            self.persian_button
        )

        self.persian_button.style().polish(
            self.persian_button
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(ASLANMainWindow):

    def __init__(self):

        super().__init__(
            title="ASLAN TUNING",
            window_title="ASLAN TUNING",
            minimum_size=(980, 620),
            size=(1250, 800),
        )

        # ====================================================
        # SETTINGS STORAGE
        # ====================================================

        self.settings = QSettings(
            "ASLAN",
            "ASLAN_TUNER"
        )

        self.title_bar.logout_requested.connect(self._logout_account)

        # ====================================================
        # LANGUAGE
        # ====================================================

        self.language_manager = LanguageManager()

        saved_language = self.settings.value(
            "language",
            "en"
        )

        if saved_language not in ("en", "fa"):

            saved_language = "en"

        self.language_manager._language = saved_language

        # ====================================================
        # THEME
        # ====================================================

        self.current_theme = self.settings.value(
            "theme",
            "dark"
        )

        if self.current_theme not in (
            "dark",
            "light",
        ):

            self.current_theme = "dark"

        # ====================================================
        # RESPONSIVE WINDOW
        # ====================================================

        self.setup_responsive_window()

        # ====================================================
        # MAIN CONTENT
        # ====================================================

        main_layout = self.content_layout

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 18, 10, 12)
        sidebar_layout.setSpacing(8)

        # Keep the logo fixed. Menu items and status information scroll below it
        # so they can never overlap the logo on short/small windows.
        self.logo = AslanLogo()
        sidebar_layout.addWidget(self.logo)
        sidebar_layout.addSpacing(6)

        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setObjectName("SidebarScroll")
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.sidebar_content = QWidget()
        self.sidebar_content.setObjectName("SidebarContent")
        sidebar_content_layout = QVBoxLayout(self.sidebar_content)
        sidebar_content_layout.setContentsMargins(0, 0, 5, 0)
        sidebar_content_layout.setSpacing(8)

        # ====================================================
        # MENU
        # ====================================================

        self.dashboard_button = SidebarButton("home", "Home", "خانه", self.language_manager)
        self.calculators_button = SidebarButton("calculator", "Calculators", "محاسبات", self.language_manager)
        self.ecu_button = SidebarButton("ecu", "ECU Tools", "ابزار ECU", self.language_manager)
        self.vehicles_button = SidebarButton("vehicle", "Vehicles", "خودروها", self.language_manager)
        self.settings_button = SidebarButton("settings", "Settings", "تنظیمات", self.language_manager)
        self.update_button = SidebarButton("update", "Updates", "بروزرسانی", self.language_manager)

        self.menu_buttons = [
            self.dashboard_button, self.calculators_button, self.ecu_button,
            self.vehicles_button, self.settings_button, self.update_button,
        ]

        for button in self.menu_buttons:
            sidebar_content_layout.addWidget(button)

        sidebar_content_layout.addSpacing(8)
        sidebar_content_layout.addStretch(1)

        self.active_vehicle_badge = QLabel("NO ACTIVE VEHICLE")
        self.active_vehicle_badge.setObjectName("ActiveVehicleBadge")
        self.active_vehicle_badge.setWordWrap(True)
        self.active_vehicle_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_content_layout.addWidget(self.active_vehicle_badge)
        self.update_active_vehicle_badge()

        self.version = QLabel(f"ASLAN TUNER\nv{APP_VERSION}")
        self.version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version.setObjectName("Version")
        sidebar_content_layout.addWidget(self.version)

        self.sidebar_scroll.setWidget(self.sidebar_content)
        sidebar_layout.addWidget(self.sidebar_scroll, 1)

        # ====================================================
        # PAGES
        # ====================================================

        self.pages = QStackedWidget()

        self.pages.setObjectName(
            "Pages"
        )

        self.dashboard_page = Dashboard(
            self.language_manager
        )

        self.calculators_page = Calculators(
            self.language_manager
        )

        self.ecu_page = ECUTools(
            self.language_manager
        )

        self.vehicles_page = Vehicles(
            self.language_manager
        )

        self.settings_page = SettingsPage(
            self.language_manager,
            self.current_theme
        )

        self.update_page = UpdatePage(
            self.language_manager,
            APP_VERSION,
            self
        )

        # ----------------------------------------------------
        # ADD PAGES
        # ----------------------------------------------------

        self.pages.addWidget(
            self.dashboard_page
        )

        self.pages.addWidget(
            self.calculators_page
        )

        self.pages.addWidget(
            self.ecu_page
        )

        self.pages.addWidget(
            self.vehicles_page
        )

        self.pages.addWidget(
            self.settings_page
        )

        self.pages.addWidget(
            self.update_page
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

        self.dashboard_button.clicked.connect(
            lambda: self.go_to_page(0)
        )

        self.calculators_button.clicked.connect(
            lambda: self.go_to_page(1)
        )

        self.ecu_button.clicked.connect(
            lambda: self.go_to_page(2)
        )

        self.vehicles_button.clicked.connect(
            lambda: self.go_to_page(3)
        )

        self.settings_button.clicked.connect(
            lambda: self.go_to_page(4)
        )

        self.update_button.clicked.connect(
            lambda: self.go_to_page(5)
        )

        # ----------------------------------------------------
        # DASHBOARD CARDS
        # ----------------------------------------------------

        self.dashboard_page.navigate.connect(
            self.navigate_from_dashboard
        )

        # ----------------------------------------------------
        # THEME
        # ----------------------------------------------------

        self.settings_page.theme_changed.connect(
            self.change_theme
        )

        # ====================================================
        # ADD WIDGETS
        # ====================================================

        main_layout.addWidget(
            self.sidebar
        )

        main_layout.addWidget(
            self.pages,
            1
        )

        # ====================================================
        # STYLE
        # ====================================================

        self.apply_style()

        # ====================================================
        # LANGUAGE SIGNAL
        # ====================================================

        self.language_manager.language_changed.connect(
            self.on_language_changed
        )

        # ====================================================
        # INITIAL LANGUAGE
        # ====================================================

        self.on_language_changed(
            self.language_manager.language
        )

        # ====================================================
        # INITIAL PAGE
        # ====================================================

        self.pages.setCurrentIndex(
            0
        )

        # ====================================================
        # UPDATE GATE
        # ====================================================
        # Fail-open when the network/update service is unavailable so the
        # application remains usable offline. A background retry locks the UI
        # only when a newer release is actually confirmed.
        self._update_verified = True
        self.update_page.verification_changed.connect(self._on_update_verification)

        from PySide6.QtCore import QTimer
        self._update_retry_timer = QTimer(self)
        self._update_retry_timer.setInterval(45000)
        self._update_retry_timer.timeout.connect(self._retry_update_check)
        self._update_retry_timer.start()
        # Let the main window render first; the network check then runs in its
        # own worker without delaying the initial visual response.
        QTimer.singleShot(650, self.update_page.check_for_updates)

    # ========================================================
    # NAVIGATION
    # ========================================================

    def _on_update_verification(self, verified):
        self._update_verified = bool(verified)
        for button in self.menu_buttons[:-1]:
            button.setEnabled(self._update_verified)
        if not self._update_verified:
            self.pages.setCurrentIndex(5)
        elif self.pages.currentIndex() == 5:
            self.pages.setCurrentIndex(0)

    def _retry_update_check(self):
        # The updater itself performs the network request in a worker thread,
        # so this retry never blocks the UI thread.
        if getattr(self.update_page, "_checking", False):
            return
        self.update_page.check_for_updates(silent=True)

    def update_active_vehicle_badge(self):

        if not hasattr(self, "active_vehicle_badge"):
            return

        params = VEHICLE_MANAGER.selected_params
        if params:
            self.active_vehicle_badge.setText(
                "ACTIVE VEHICLE\\n" +
                str(params.get("display_name", VEHICLE_MANAGER.selected_key)) +
                "\\nPARAMETERS LOADED"
            )
        else:
            self.active_vehicle_badge.setText("NO ACTIVE VEHICLE")

    def go_to_page(self, index):

        if index != 5 and not getattr(self, "_update_verified", False):
            self.pages.setCurrentIndex(5)
            return

        if 0 <= index < self.pages.count():

            self.pages.setCurrentIndex(
                index
            )

    def navigate_from_dashboard(self, page_name):

        pages = {
            "calculators": 1,
            "ecu": 2,
            "vehicles": 3,
            "settings": 4,
        }

        index = pages.get(
            page_name
        )

        if index is not None:

            self.go_to_page(
                index
            )

    # ========================================================
    # THEME
    # ========================================================

    def change_theme(self, theme):

        if theme not in (
            "dark",
            "light",
        ):

            return

        self.current_theme = theme

        self.settings.setValue(
            "theme",
            theme
        )

        self.apply_style()

        self.settings_page.current_theme = theme

        self.settings_page.update_theme_ui()

        self.settings_page.update_language(
            self.language_manager.language
        )

        self.update()

    # ========================================================
    # RESPONSIVE WINDOW
    # ========================================================

    def _logout_account(self):
        auth_logout(self.settings)
        self.close()

    def setup_responsive_window(self):

        screen = QApplication.primaryScreen()

        if screen is None:

            return

        geometry = screen.availableGeometry()

        screen_width = geometry.width()
        screen_height = geometry.height()

        # Keep the main window proportional to the actual display.  Do not
        # enforce a fixed 980x620 minimum on small laptops/monitors.
        target_width = int(screen_width * 0.84)
        target_height = int(screen_height * 0.84)

        target_width = max(760, min(target_width, screen_width - 24))
        target_height = max(500, min(target_height, screen_height - 36))
        target_width = min(target_width, screen_width)
        target_height = min(target_height, screen_height)

        self.resize(
            target_width,
            target_height
        )

        x = (
            geometry.x()
            + (
                geometry.width()
                - self.width()
            ) // 2
        )

        y = (
            geometry.y()
            + (
                geometry.height()
                - self.height()
            ) // 2
        )

        self.move(
            x,
            y
        )

    # ========================================================
    # LANGUAGE CHANGE
    # ========================================================

    def on_language_changed(self, language):

        self.settings.setValue(
            "language",
            language
        )

        if language == "fa":

            QApplication.instance().setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
            )

            self.content_layout.setDirection(
                QHBoxLayout.Direction.RightToLeft
            )

        else:

            QApplication.instance().setLayoutDirection(
                Qt.LayoutDirection.LeftToRight
            )

            self.content_layout.setDirection(
                QHBoxLayout.Direction.LeftToRight
            )

        # Settings language buttons

        self.settings_page.update_language_buttons(
            language
        )

        # Re-polish

        self.style().unpolish(
            self
        )

        self.style().polish(
            self
        )

        self.update()

    # ========================================================
    # STYLE
    # ========================================================

    def apply_style(self):

        if self.current_theme == "light":

            RED = LIGHT_RED
            RED_DARK = LIGHT_RED_DARK
            RED_GLOW = LIGHT_RED_GLOW

            BG = LIGHT_BG
            PANEL = LIGHT_PANEL
            PANEL_2 = LIGHT_PANEL_2
            PANEL_3 = LIGHT_PANEL_3

            WHITE = LIGHT_WHITE
            TEXT = LIGHT_TEXT
            MUTED = LIGHT_MUTED

            BORDER = LIGHT_BORDER

            sidebar_bg = "#e5e7eb"
            sidebar_border = "#d2d5db"

            card_top = "#ffffff"
            card_bottom = "#f3f4f6"

            card_hover_top = "#ffffff"
            card_hover_bottom = "#eceef1"

            tool_bg = "#ffffff"
            tool_hover = "#f0f2f5"

        else:

            RED = DARK_RED
            RED_DARK = DARK_RED_DARK
            RED_GLOW = DARK_RED_GLOW

            BG = DARK_BG
            PANEL = DARK_PANEL
            PANEL_2 = DARK_PANEL_2
            PANEL_3 = DARK_PANEL_3

            WHITE = DARK_WHITE
            TEXT = DARK_TEXT
            MUTED = DARK_MUTED

            BORDER = DARK_BORDER

            sidebar_bg = "#0a0c0f"
            sidebar_border = "#24272c"

            card_top = "#11151a"
            card_bottom = "#0b0d10"

            card_hover_top = "#171b21"
            card_hover_bottom = "#0d0f13"

            tool_bg = "#121518"
            tool_hover = "#191d22"

        self.setStyleSheet(
            f"""

            /* =================================================
               MAIN WINDOW
               ================================================= */

            QMainWindow {{
                background: {BG};
            }}

            QWidget {{
                color: {WHITE};
                font-family: "Segoe UI";
                font-size: 14px;
            }}

            /* =================================================
               SCROLL AREAS
               ================================================= */

            QScrollArea {{
                background: {BG};
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background: {BG};
            }}

            QScrollBar:vertical {{
                background: transparent;

                width: 7px;

                margin: 2px;
            }}

            QScrollBar::handle:vertical {{
                background: #383d45;

                border-radius: 3px;

                min-height: 35px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {RED};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            /* =================================================
               SIDEBAR
               ================================================= */

            #Sidebar {{
                background: {sidebar_bg};

                border-right: 1px solid {sidebar_border};
            }}

            #SidebarScroll {{
                background: transparent;
                border: none;
            }}

            #SidebarScroll > QWidget > QWidget#SidebarContent {{
                background: transparent;
            }}

            #SidebarScroll QScrollBar:vertical {{
                width: 6px;
                background: transparent;
                margin: 2px 0 2px 0;
            }}

            #SidebarScroll QScrollBar::handle:vertical {{
                background: #3b4048;
                border-radius: 3px;
                min-height: 28px;
            }}

            #SidebarScroll QScrollBar::handle:vertical:hover {{
                background: {RED};
            }}

            #SidebarScroll QScrollBar::add-line:vertical,
            #SidebarScroll QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            #SidebarScroll QScrollBar::add-page:vertical,
            #SidebarScroll QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            /* =================================================
               SIDEBAR BUTTON
               ================================================= */

            #SidebarButton {{
                background: transparent;

                border: 1px solid transparent;

                border-radius: 9px;

                padding: 8px 12px;

                text-align: left;

                color: {MUTED};

                font-size: 14px;
                font-weight: 600;
            }}

            #SidebarButton:hover {{
                background: {PANEL_3};

                border: 1px solid #5b151d;

                color: {WHITE};
            }}

            #SidebarButton:pressed {{
                background: #351016;

                border: 1px solid {RED};
            }}

            #ActiveVehicleBadge {{
                background: #151015;
                border: 1px solid #4a2028;
                border-radius: 10px;
                padding: 9px 8px;
                color: #ff3045;
                font-size: 10px;
                font-weight: 800;
            }}

            /* =================================================
               VERSION
               ================================================= */

            #Version {{
                color: {MUTED};

                font-size: 10px;
            }}

            /* =================================================
               DASHBOARD
               ================================================= */

            #Dashboard {{
                background: {BG};
            }}

            #WelcomeLabel {{
                color: {MUTED};

                font-size: 18px;
                font-weight: 500;
            }}

            #DashboardTitle {{
                color: {WHITE};

                font-size: 42px;
                font-weight: 900;

                letter-spacing: 1px;
            }}

            #DashboardSubtitle {{
                color: {TEXT};

                font-size: 18px;
                font-weight: 500;
            }}

            #RedLine {{
                background: {RED};

                border-radius: 2px;
            }}

            #DashboardDescription {{
                color: {MUTED};

                font-size: 14px;
                font-weight: 500;

                max-width: 720px;
            }}

            /* =================================================
               DASHBOARD CARD
               ================================================= */

            #DashboardCard {{
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 0,
                    y2: 1,

                    stop: 0 {card_top},
                    stop: 1 {card_bottom}
                );

                border: 1px solid #65121b;

                border-radius: 13px;

                padding: 0px;
            }}

            #DashboardCard:hover {{
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 0,
                    y2: 1,

                    stop: 0 {card_hover_top},
                    stop: 1 {card_hover_bottom}
                );

                border: 1px solid {RED};
            }}

            #DashboardCard:pressed {{
                border: 1px solid {RED_GLOW};
            }}

            #CardIcon {{
                color: {RED};

                font-size: 34px;
                font-weight: 700;

                padding: 0px;
            }}

            #CardTitle {{
                color: {WHITE};

                font-size: 20px;
                font-weight: 800;
            }}

            #CardDescription {{
                color: {MUTED};

                font-size: 12px;
                font-weight: 500;
            }}

            #CardArrow {{
                color: {RED};

                background: {PANEL_2};

                border: 1px solid {RED};

                border-radius: 18px;

                font-size: 20px;
                font-weight: 700;
            }}

            /* =================================================
               OTHER PAGES
               ================================================= */

            #PageTitle {{
                color: {WHITE};

                font-size: 30px;
                font-weight: 850;
            }}

            #Subtitle {{
                color: {MUTED};

                font-size: 15px;
            }}

            /* =================================================
               TOOL BUTTON
               ================================================= */

            #ToolButton {{
                background: {tool_bg};

                border: 1px solid {BORDER};

                border-radius: 9px;

                padding: 8px 16px;

                text-align: left;

                color: {WHITE};

                font-size: 14px;
                font-weight: 650;
            }}

            #ToolButton:hover {{
                background: {tool_hover};

                border: 1px solid {RED};

                color: {WHITE};
            }}

            #ToolButton:pressed {{
                background: #351016;

                border: 1px solid {RED};
            }}

            /* =================================================
               WARNING
               ================================================= */

            #Warning {{
                color: #ffbd67;

                background: #17130d;

                border: 1px solid #49351b;

                border-radius: 8px;

                padding: 10px;
            }}

            /* =================================================
               SETTINGS PAGE
               ================================================= */

            #SettingsPage {{
                background: {BG};
            }}

            #SettingsSectionTitle {{
                color: {WHITE};

                font-size: 16px;
                font-weight: 800;

                letter-spacing: 0.5px;
            }}

            #SettingsSectionDescription {{
                color: {MUTED};

                font-size: 13px;
            }}

            #SettingsOption {{
                background: {PANEL};

                border: 1px solid {BORDER};

                border-radius: 12px;
            }}

            #SettingsOption:hover {{
                border: 1px solid #5a1a22;
            }}

            #SettingsOptionIcon {{
                color: {RED};

                font-size: 27px;
                font-weight: 700;
            }}

            #SettingsOptionTitle {{
                color: {WHITE};

                font-size: 15px;
                font-weight: 750;
            }}

            #SettingsOptionDescription {{
                color: {MUTED};

                font-size: 12px;
            }}

            /* =================================================
               THEME SWITCH
               ================================================= */

            #ThemeSwitch {{
                min-width: 54px;
                max-width: 54px;

                min-height: 28px;
                max-height: 28px;
            }}

            #ThemeSwitch::indicator {{
                width: 50px;
                height: 26px;

                border-radius: 13px;

                background: #343941;

                border: 1px solid #4a4f57;
            }}

            #ThemeSwitch::indicator:checked {{
                background: {RED};

                border: 1px solid {RED_GLOW};
            }}

            /* =================================================
               LANGUAGE BUTTONS
               ================================================= */

            #SettingsLanguageButton {{
                background: {PANEL_2};

                border: 1px solid {BORDER};

                border-radius: 8px;

                color: {MUTED};

                font-size: 11px;
                font-weight: 700;
            }}

            #SettingsLanguageButton:hover {{
                border: 1px solid {RED};

                color: {WHITE};
            }}

            #SettingsLanguageButton[active="true"] {{
                background: {RED};

                border: 1px solid {RED_GLOW};

                color: #ffffff;
            }}

            /* =================================================
               SETTINGS INFO
               ================================================= */

            #SettingsInfo {{
                color: {MUTED};

                font-size: 12px;

                padding-top: 4px;
            }}

            """
        )


# ============================================================
# APPLICATION ENTRY
# ============================================================

def main():

    startup_started = time.perf_counter()

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    app.setApplicationVersion(
        APP_VERSION
    )

    app.setOrganizationName(
        "ASLAN"
    )

    # --------------------------------------------------------
    # Default direction
    # --------------------------------------------------------

    app.setLayoutDirection(
        Qt.LayoutDirection.LeftToRight
    )

    # --------------------------------------------------------
    # Local account gate
    # --------------------------------------------------------

    account_settings = QSettings("ASLAN", "ASLAN_TUNER")
    if not is_session_active(account_settings):
        auth = AuthDialog(account_settings)
        if auth.exec() != QDialog.DialogCode.Accepted:
            return 0

    # --------------------------------------------------------
    # Main Window
    # --------------------------------------------------------

    window = MainWindow()

    # --------------------------------------------------------
    # Show
    # --------------------------------------------------------

    window.show()

    # --------------------------------------------------------
    # Startup profiling
    # --------------------------------------------------------

    if _PROFILE:

        elapsed_ms = (
            time.perf_counter()
            - startup_started
        ) * 1000.0

        try:

            profile_path = (
                Path(
                    sys.executable
                    if getattr(
                        sys,
                        "frozen",
                        False
                    )
                    else __file__
                )
                .resolve()
                .with_name(
                    "aslan_startup_profile.txt"
                )
            )

            profile_path.write_text(
                f"startup_to_window_show_ms={elapsed_ms:.2f}\n",
                encoding="utf-8",
            )

        except OSError:

            pass

    # --------------------------------------------------------
    # Event Loop
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()