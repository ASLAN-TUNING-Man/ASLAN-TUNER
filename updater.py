import json
import os
import subprocess
import tempfile
import urllib.request
from PySide6.QtCore import Qt, QObject, Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QProgressBar, QApplication

# Replace with your public GitHub repository, e.g. "ali-zmax/ASLAN-TUNER".
GITHUB_REPOSITORY = os.environ.get("ASLAN_GITHUB_REPOSITORY", "YOUR_GITHUB_USERNAME/ASLAN-TUNER")


def version_tuple(value):
    value = str(value or "0").strip().lstrip("vV")
    parts = []
    for item in value.split("."):
        digits = "".join(ch for ch in item if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple((parts + [0, 0, 0, 0])[:4])


def is_newer_version(remote, local):
    return version_tuple(remote) > version_tuple(local)


class _Worker(QObject):
    finished = Signal(dict)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, current_version, download_url=None):
        super().__init__()
        self.current_version = current_version
        self.download_url = download_url

    def check(self):
        try:
            if "YOUR_GITHUB_USERNAME" in GITHUB_REPOSITORY:
                raise RuntimeError("GitHub repository is not configured yet.")
            url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ASLAN-TUNER"})
            with urllib.request.urlopen(req, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
            remote = data.get("tag_name", "").lstrip("vV")
            setup = next((asset for asset in data.get("assets", []) if asset.get("name", "").lower().endswith("-setup.exe")), None)
            self.finished.emit({"version": remote, "name": data.get("name") or remote, "body": data.get("body") or "", "html_url": data.get("html_url") or "", "setup": setup})
        except Exception as exc:
            self.failed.emit(str(exc))

    def download(self):
        try:
            req = urllib.request.Request(self.download_url, headers={"User-Agent": "ASLAN-TUNER"})
            with urllib.request.urlopen(req, timeout=120) as response:
                total = int(response.headers.get("Content-Length") or 0)
                fd, path = tempfile.mkstemp(prefix="ASLAN-TUNER-update-", suffix="-Setup.exe")
                os.close(fd)
                received = 0
                with open(path, "wb") as target:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        target.write(chunk)
                        received += len(chunk)
                        if total:
                            self.progress.emit(min(100, int(received * 100 / total)))
            self.finished.emit({"path": path})
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdatePage(QWidget):
    verification_changed = Signal(bool)

    def __init__(self, language_manager, current_version, parent=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.current_version = current_version
        self.latest = None
        self._thread = None
        self._worker = None
        self.setObjectName("UpdatePage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 30, 38, 30)
        layout.setSpacing(12)
        self.title = QLabel("Software Update")
        self.title.setObjectName("PageTitle")
        layout.addWidget(self.title)
        self.subtitle = QLabel(f"Installed version: v{current_version}")
        self.subtitle.setObjectName("Subtitle")
        layout.addWidget(self.subtitle)

        self.card = QFrame()
        self.card.setObjectName("SettingsOption")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)
        self.status = QLabel("Checking for updates…")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setMinimumHeight(80)
        card_layout.addWidget(self.status)
        self.detail = QLabel("")
        self.detail.setWordWrap(True)
        self.detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.detail)
        row = QHBoxLayout()
        row.addStretch()
        self.check_btn = QPushButton("Check again")
        self.check_btn.clicked.connect(self.check_for_updates)
        self.update_btn = QPushButton("Update now")
        self.update_btn.clicked.connect(self.start_download)
        self.update_btn.setEnabled(False)
        row.addWidget(self.check_btn)
        row.addWidget(self.update_btn)
        row.addStretch()
        card_layout.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        card_layout.addWidget(self.progress)
        layout.addWidget(self.card)
        layout.addStretch()
        self.setStyleSheet("""
            #UpdatePage QPushButton { padding:10px 18px; border-radius:8px; }
            #UpdatePage #SettingsOption { background:#15181d; border:1px solid #292d34; border-radius:12px; }
            #UpdatePage QProgressBar { height:8px; border:0; background:#20242b; border-radius:4px; }
            #UpdatePage QProgressBar::chunk { background:#ff1026; border-radius:4px; }
        """)

    def check_for_updates(self):
        self.check_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.status.setStyleSheet("color:#d8dbe0;font-size:18px;font-weight:800;")
        self.status.setText("Checking for updates…")
        self._thread = QThread(self)
        self._worker = _Worker(self.current_version)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.check)
        self._worker.finished.connect(self._checked)
        self._worker.failed.connect(self._failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _checked(self, data):
        self.latest = data
        remote = data.get("version", "")
        newer = is_newer_version(remote, self.current_version)
        self.check_btn.setEnabled(True)
        if not newer:
            self.status.setText("برنامه آپدیت است")
            self.status.setStyleSheet("color:#4ade80;font-size:20px;font-weight:900;")
            self.detail.setText(f"نسخه نصب‌شده: v{self.current_version}  •  آخرین نسخه: v{remote}")
            self.update_btn.setEnabled(False)
            self.verification_changed.emit(True)
        else:
            self.status.setText("شما آپدیت نیستید")
            self.status.setStyleSheet("color:#ff3045;font-size:20px;font-weight:900;")
            self.detail.setText(f"نسخه نصب‌شده: v{self.current_version}\nنسخه جدید: v{remote}\nبرای ادامه کار باید برنامه را بروزرسانی کنید.")
            self.update_btn.setEnabled(bool(data.get("setup")))
            self.verification_changed.emit(False)

    def _failed(self, message):
        self.check_btn.setEnabled(True)
        self.status.setText("بررسی بروزرسانی ناموفق بود")
        self.status.setStyleSheet("color:#ff3045;font-size:18px;font-weight:900;")
        self.detail.setText(message)
        self.verification_changed.emit(False)

    def start_download(self):
        if not self.latest or not self.latest.get("setup"):
            return
        url = self.latest["setup"].get("browser_download_url")
        if not url:
            return
        self.update_btn.setEnabled(False)
        self.check_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status.setText("در حال دریافت نسخه جدید…")
        self._thread = QThread(self)
        self._worker = _Worker(self.current_version, url)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.download)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished.connect(self._downloaded)
        self._worker.failed.connect(self._download_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _downloaded(self, data):
        path = data.get("path")
        if not path:
            self._download_failed("Installer path is missing.")
            return
        try:
            subprocess.Popen([path], close_fds=True)
            QApplication.instance().quit()
        except Exception as exc:
            self._download_failed(str(exc))

    def _download_failed(self, message):
        self.progress.setVisible(False)
        self.check_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.status.setText("دانلود بروزرسانی ناموفق بود")
        self.status.setStyleSheet("color:#ff3045;font-size:18px;font-weight:900;")
        self.detail.setText(message)
