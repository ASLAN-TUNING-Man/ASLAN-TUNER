import hashlib
import secrets
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QStackedWidget, QWidget


def _derive(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 180_000).hex()


def is_session_active(settings):
    return bool(settings.value("account/session_active", False, type=bool)) and bool(settings.value("account/username", ""))


def logout(settings):
    settings.setValue("account/session_active", False)
    settings.sync()


class AuthDialog(QDialog):
    """Local account gate. Passwords are stored as salted PBKDF2 hashes."""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("ASLAN TUNER • Account")
        self.setModal(True)
        self.setMinimumSize(430, 360)
        self.setObjectName("AuthDialog")
        self.logged_in = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(12)
        title = QLabel("ASLAN TUNER")
        title.setStyleSheet("font-size:26px;font-weight:900;color:#ff1026;")
        root.addWidget(title)
        self.subtitle = QLabel("Sign in to continue")
        self.subtitle.setStyleSheet("color:#9ca3af;font-size:13px;")
        root.addWidget(self.subtitle)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self.login_page = self._form(False)
        self.register_page = self._form(True)
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)
        row = QHBoxLayout()
        self.switch_btn = QPushButton("Create account")
        self.switch_btn.clicked.connect(self._toggle)
        self.action_btn = QPushButton("Sign in")
        self.action_btn.clicked.connect(self._submit)
        row.addWidget(self.switch_btn)
        row.addStretch()
        row.addWidget(self.action_btn)
        root.addLayout(row)
        self.setStyleSheet("""
            QDialog#AuthDialog { background:#0d0f12; color:#f4f5f7; }
            QLineEdit { background:#15181d; border:1px solid #292d34; border-radius:8px; padding:10px; color:white; }
            QLineEdit:focus { border:1px solid #ff1026; }
            QPushButton { background:#15181d; border:1px solid #3a3f48; border-radius:8px; padding:9px 14px; color:#fff; }
            QPushButton:hover { border-color:#ff1026; }
        """)

    def _form(self, register):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        username = QLineEdit()
        username.setPlaceholderText("Username")
        password = QLineEdit()
        password.setPlaceholderText("Password")
        password.setEchoMode(QLineEdit.Password)
        lay.addWidget(username)
        lay.addWidget(password)
        if register:
            confirm = QLineEdit()
            confirm.setPlaceholderText("Confirm password")
            confirm.setEchoMode(QLineEdit.Password)
            lay.addWidget(confirm)
            w.fields = (username, password, confirm)
        else:
            w.fields = (username, password)
        lay.addStretch()
        return w

    def _toggle(self):
        if self.stack.currentIndex() == 1:
            self.stack.setCurrentIndex(0)
            self.switch_btn.setText("Create account")
            self.action_btn.setText("Sign in")
            self.subtitle.setText("Sign in to continue")
        else:
            self.stack.setCurrentIndex(1)
            self.switch_btn.setText("Back to sign in")
            self.action_btn.setText("Create account")
            self.subtitle.setText("Create your local ASLAN TUNER account")

    def _submit(self):
        fields = self.stack.currentWidget().fields
        username = fields[0].text().strip()
        password = fields[1].text()
        if len(username) < 3 or len(password) < 6:
            QMessageBox.warning(self, "Account", "Username must be at least 3 characters and password at least 6 characters.")
            return
        if self.stack.currentIndex() == 1:
            if password != fields[2].text():
                QMessageBox.warning(self, "Account", "Passwords do not match.")
                return
            if self.settings.value("account/username", ""):
                QMessageBox.warning(self, "Account", "An account is already registered on this device.")
                return
            salt = secrets.token_bytes(16)
            self.settings.setValue("account/username", username)
            self.settings.setValue("account/salt", salt.hex())
            self.settings.setValue("account/hash", _derive(password, salt))
            self.settings.setValue("account/session_active", True)
            self.settings.sync()
            QMessageBox.information(self, "Account", "Account created. You are now signed in.")
            self.logged_in = True
            self.accept()
            return
        saved_user = self.settings.value("account/username", "")
        salt_hex = self.settings.value("account/salt", "")
        saved_hash = self.settings.value("account/hash", "")
        if not saved_user:
            self._toggle()
            return
        try:
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            salt = b""
        if username != saved_user or not salt or _derive(password, salt) != saved_hash:
            QMessageBox.warning(self, "Account", "Invalid username or password.")
            return
        self.settings.setValue("account/session_active", True)
        self.settings.sync()
        self.logged_in = True
        self.accept()
