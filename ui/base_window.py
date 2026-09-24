from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
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
        self.setMinimumSize(*minimum_size)
        self.resize(*size)
        self.setWindowFlags(WINDOW_FLAGS)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = ASLANTopBar(self, title)
        root.addWidget(self.title_bar)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("DialogContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(22, 20, 22, 22)
        self.content_layout.setSpacing(12)
        root.addWidget(self.content_widget, 1)

        self.setStyleSheet("""
            QDialog#ASLANDialog {
                background: #101012;
            }
            QWidget#DialogContent {
                background: #101012;
            }
        """)


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
