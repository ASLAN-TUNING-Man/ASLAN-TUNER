from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QApplication
from ui.topbar import ASLANTopBar

WINDOW_FLAGS = (
    Qt.Window
    | Qt.FramelessWindowHint
    | Qt.WindowMinimizeButtonHint
    | Qt.WindowMaximizeButtonHint
    | Qt.WindowCloseButtonHint
)


class ASLANDialog(QDialog):
    """Base window for calculators and ECU tools opened as dialogs."""

    def __init__(
        self,
        parent=None,
        title="ASLAN TUNING",
        window_title=None,
        minimum_size=(900, 650),
        size=(1100, 800),
    ):
        super().__init__(parent)
        self.setWindowTitle(window_title or title)
        self._requested_minimum = minimum_size
        self._requested_size = size
        self.setMinimumSize(1, 1)
        self.resize(*size)
        self.setWindowFlags(WINDOW_FLAGS)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = ASLANTopBar(self, title)
        root.addWidget(self.title_bar)

        self.content_scroll = QScrollArea()
        self.content_scroll.setObjectName("DialogScrollArea")
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("DialogContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(22, 20, 22, 22)
        self.content_layout.setSpacing(12)
        self.content_scroll.setWidget(self.content_widget)
        root.addWidget(self.content_scroll, 1)

        self._fit_to_available_screen()

        self.setStyleSheet("""
            QDialog#ASLANDialog {
                background: #101012;
            }
            QWidget#DialogContent {
                background: #101012;
            }
            QScrollArea#DialogScrollArea {
                background: #101012;
                border: none;
            }
        """)

    def _fit_to_available_screen(self):
        screen = None
        if self.parent() is not None:
            try:
                screen = QApplication.screenAt(self.parent().mapToGlobal(self.parent().rect().center()))
            except Exception:
                screen = None
        screen = screen or QApplication.primaryScreen()
        if screen is None:
            return

        area = screen.availableGeometry()
        # Never allow a dialog's minimum size to exceed the physical screen.
        # The content area is scrollable, so small displays remain usable.
        max_w = max(520, int(area.width() * 0.94))
        max_h = max(420, int(area.height() * 0.90))
        requested_w, requested_h = self._requested_size
        requested_min_w, requested_min_h = self._requested_minimum

        # Keep the window itself inside the physical screen. Content is
        # scrollable, so a small display must never be forced to satisfy the
        # original design-time minimum size.
        min_w = min(max(420, requested_min_w), max_w)
        min_h = min(max(320, requested_min_h), max_h)
        target_w = min(max(requested_w, min_w), max_w)
        target_h = min(max(requested_h, min_h), max_h)

        # Layouts can report a larger implicit minimum. Temporarily relaxing
        # the widget minimum before resize prevents Qt from expanding the
        # top-level window beyond target_h/target_w.
        self.setMinimumSize(1, 1)
        self.resize(target_w, target_h)
        self.setMinimumSize(min_w, min_h)
        # A child layout may still advertise a larger minimum; clamp once
        # more after the resize.
        if self.width() > max_w or self.height() > max_h:
            self.setMinimumSize(1, 1)
            self.resize(min(self.width(), max_w), min(self.height(), max_h))
            self.setMinimumSize(min_w, min_h)

    def showEvent(self, event):
        # Always center dialogs on the actual screen they are being shown on.
        # Using the parent widget's geometry can place a child dialog near a
        # corner when the parent is a nested/scrollable widget.
        self._fit_to_available_screen()
        screen = None
        try:
            screen = QApplication.screenAt(self.mapToGlobal(self.rect().center()))
        except Exception:
            screen = None
        screen = screen or QApplication.primaryScreen()
        if screen is not None:
            frame = self.frameGeometry()
            frame.moveCenter(screen.availableGeometry().center())
            self.move(frame.topLeft())
        super().showEvent(event)


class ASLANMainWindow(QMainWindow):
    """Base frameless main window shared by ASLAN TUNER."""

    def __init__(
        self,
        title="ASLAN TUNING",
        window_title=None,
        minimum_size=(1100, 700),
        size=(1250, 800),
    ):
        super().__init__()
        self.setWindowTitle(window_title or title)
        self.setMinimumSize(*minimum_size)
        self.resize(*size)
        self.setWindowFlags(WINDOW_FLAGS)

        self.root_widget = QWidget()
        self.root_widget.setObjectName("ASLANRoot")
        self.root_layout = QVBoxLayout(self.root_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.title_bar = ASLANTopBar(self, title)
        self.root_layout.addWidget(self.title_bar)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("MainContent")
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.root_layout.addWidget(self.content_widget, 1)

        self.setCentralWidget(self.root_widget)
