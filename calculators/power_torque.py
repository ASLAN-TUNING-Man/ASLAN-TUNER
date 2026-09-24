import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
    QScrollArea,
)


# ============================================================
# ASLAN TUNER
# POWER / TORQUE / POWER-TO-WEIGHT CALCULATOR
# ============================================================

HP_TO_NM_CONSTANT = 7127.0


# ============================================================
# CALCULATIONS
# ============================================================

def calculate_torque_from_power(power_hp, rpm):
    """
    Torque (Nm) from horsepower (HP) and RPM.
    """

    if power_hp <= 0 or rpm <= 0:
        raise ValueError

    return (power_hp * HP_TO_NM_CONSTANT) / rpm


def calculate_power_from_torque(torque_nm, rpm):
    """
    Horsepower (HP) from torque (Nm) and RPM.
    """

    if torque_nm <= 0 or rpm <= 0:
        raise ValueError

    return (torque_nm * rpm) / HP_TO_NM_CONSTANT


def calculate_power_to_weight(power_hp, vehicle_weight_kg):
    """
    Power-to-weight ratio in HP per metric tonne.
    """

    if power_hp <= 0 or vehicle_weight_kg <= 0:
        raise ValueError

    return (power_hp * 1000.0) / vehicle_weight_kg


# ============================================================
# INFO BUTTON
# ============================================================

class InfoButton(QPushButton):

    def __init__(self, text="!", parent=None):

        super().__init__(text, parent)

        self.setFixedSize(28, 28)

        self.setStyleSheet("""
            QPushButton {
                background-color: #111111;
                color: #ff1e1e;
                border: 1px solid #ff1e1e;
                border-radius: 14px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #ff1e1e;
                color: #000000;
            }

            QPushButton:pressed {
                background-color: #b71c1c;
                color: #ffffff;
            }
        """)


# ============================================================
# RESULT CARD
# ============================================================

class ResultCard(QFrame):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            15,
            12,
            15,
            12
        )

        layout.setSpacing(5)

        self.value_label = QLabel("—")

        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.value_label.setStyleSheet("""
            QLabel {
                color: #ff2020;
                font-size: 22px;
                font-weight: bold;
                border: none;
            }
        """)

        self.detail_label = QLabel("")

        self.detail_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.detail_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 12px;
                border: none;
            }
        """)

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            self.detail_label
        )


# ============================================================
# SECTION CARD
# ============================================================

class SectionCard(QFrame):

    def __init__(
        self,
        title,
        info_text="",
        parent=None
    ):

        super().__init__(parent)

        self.setStyleSheet("""
            QFrame {
                background-color: #0b0b0b;
                border: 1px solid #242424;
                border-radius: 12px;
            }
        """)

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            18,
            16,
            18,
            16
        )

        self.main_layout.setSpacing(12)

        header = QHBoxLayout()

        header.setSpacing(8)

        title_label = QLabel(title)

        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 17px;
                font-weight: bold;
                border: none;
            }
        """)

        header.addWidget(
            title_label
        )

        header.addStretch()

        if info_text:

            info_button = InfoButton()

            info_button.clicked.connect(
                lambda: QMessageBox.information(
                    self,
                    title,
                    info_text
                )
            )

            header.addWidget(
                info_button
            )

        self.main_layout.addLayout(
            header
        )

        self.content_layout = QVBoxLayout()

        self.content_layout.setSpacing(10)

        self.main_layout.addLayout(
            self.content_layout
        )


# ============================================================
# MAIN CALCULATOR
# ============================================================

class PowerTorqueCalculator(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "ASLAN TUNER - Power / Torque"
        )

        self.resize(
            720,
            850
        )

        self.setMinimumSize(
            500,
            600
        )

        # Enable normal Windows title bar controls
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QDialog {
                background-color: #050505;
                color: #ffffff;
            }

            QWidget {
                background-color: #050505;
                color: #ffffff;
            }

            QLabel {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }

            QLineEdit {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 7px;
                padding: 8px;
                font-size: 13px;
            }

            QLineEdit:focus {
                border: 1px solid #ff2020;
            }

            QPushButton {
                background-color: #151515;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 7px;
                padding: 9px 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #ff2020;
                color: #000000;
                border: 1px solid #ff2020;
            }

            QScrollArea {
                border: none;
                background-color: #050505;
            }

            QScrollArea > QWidget > QWidget {
                background-color: #050505;
            }

            QScrollBar:vertical {
                background-color: #0b0b0b;
                width: 10px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background-color: #333333;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #ff2020;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.build_ui()


    # ========================================================
    # UI HELPERS
    # ========================================================

    def create_input(
        self,
        layout,
        label_text,
        default_value=""
    ):

        row = QHBoxLayout()

        row.setSpacing(10)

        label = QLabel(label_text)

        label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                background-color: transparent;
                font-size: 13px;
            }
        """)

        input_box = QLineEdit()

        input_box.setText(
            str(default_value)
        )

        row.addWidget(
            label,
            1
        )

        row.addWidget(
            input_box,
            1
        )

        layout.addLayout(
            row
        )

        return input_box


    def create_generate_button(
        self,
        text="GENERATE"
    ):

        button = QPushButton(text)

        button.setStyleSheet("""
            QPushButton {
                background-color: #151515;
                color: #ff2020;
                border: 1px solid #ff2020;
                border-radius: 7px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #ff2020;
                color: #000000;
            }
        """)

        return button


    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        content = QWidget()

        content.setStyleSheet("""
            QWidget {
                background-color: #050505;
            }
        """)

        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(
            22,
            22,
            22,
            22
        )

        content_layout.setSpacing(18)


        # ====================================================
        # HEADER
        # ====================================================

        header_layout = QHBoxLayout()

        title = QLabel(
            "ASLAN TUNER"
        )

        title.setStyleSheet("""
            QLabel {
                color: #ff2020;
                font-size: 25px;
                font-weight: bold;
                background-color: transparent;
            }
        """)

        subtitle = QLabel(
            "POWER / TORQUE"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 12px;
                font-weight: bold;
                background-color: transparent;
            }
        """)

        title_box = QVBoxLayout()

        title_box.setSpacing(2)

        title_box.addWidget(
            title
        )

        title_box.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_box
        )

        header_layout.addStretch()

        content_layout.addLayout(
            header_layout
        )


        # ====================================================
        # 1 - POWER TO TORQUE
        # ====================================================

        self.power_to_torque_card = SectionCard(
            "1. تبدیل توان به گشتاور",
            "تبدیل توان اسب بخار (HP) و دور موتور به گشتاور نیوتن‌متر."
        )

        self.power_to_torque_power = self.create_input(
            self.power_to_torque_card.content_layout,
            "توان اسب بخار (HP)",
            110
        )

        self.power_to_torque_rpm = self.create_input(
            self.power_to_torque_card.content_layout,
            "دور موتور (RPM)",
            6000
        )

        self.power_to_torque_rpm2 = self.create_input(
            self.power_to_torque_card.content_layout,
            "دور موتور دوم (RPM)",
            6500
        )

        button_1 = self.create_generate_button()

        button_1.clicked.connect(
            self.calculate_power_to_torque
        )

        self.power_to_torque_card.content_layout.addWidget(
            button_1
        )

        self.power_to_torque_result = ResultCard()

        self.power_to_torque_card.content_layout.addWidget(
            self.power_to_torque_result
        )

        content_layout.addWidget(
            self.power_to_torque_card
        )


        # ====================================================
        # 2 - TORQUE TO POWER
        # ====================================================

        self.torque_to_power_card = SectionCard(
            "2. تبدیل گشتاور به توان",
            "تبدیل گشتاور نیوتن‌متر و دور موتور به اسب بخار (HP)."
        )

        self.torque_to_power_torque = self.create_input(
            self.torque_to_power_card.content_layout,
            "گشتاور (Nm)",
            145
        )

        self.torque_to_power_rpm = self.create_input(
            self.torque_to_power_card.content_layout,
            "دور موتور (RPM)",
            4000
        )

        button_2 = self.create_generate_button()

        button_2.clicked.connect(
            self.calculate_torque_to_power
        )

        self.torque_to_power_card.content_layout.addWidget(
            button_2
        )

        self.torque_to_power_result = ResultCard()

        self.torque_to_power_card.content_layout.addWidget(
            self.torque_to_power_result
        )

        content_layout.addWidget(
            self.torque_to_power_card
        )


        # ====================================================
        # 3 - POWER TO WEIGHT
        # ====================================================

        self.pwr_card = SectionCard(
            "3. نسبت توان به وزن",
            "محاسبه نسبت توان خودرو به جرم خودرو."
        )

        self.pwr_power = self.create_input(
            self.pwr_card.content_layout,
            "توان (HP)",
            110
        )

        self.pwr_weight = self.create_input(
            self.pwr_card.content_layout,
            "وزن خودرو (kg)",
            1350
        )

        button_3 = self.create_generate_button()

        button_3.clicked.connect(
            self.calculate_pwr
        )

        self.pwr_card.content_layout.addWidget(
            button_3
        )

        self.pwr_result = ResultCard()

        self.pwr_card.content_layout.addWidget(
            self.pwr_result
        )

        content_layout.addWidget(
            self.pwr_card
        )


        content_layout.addStretch()

        scroll.setWidget(
            content
        )

        outer_layout.addWidget(
            scroll
        )


    # ========================================================
    # CALCULATE 1
    # ========================================================

    def calculate_power_to_torque(self):

        try:

            power = float(
                self.power_to_torque_power.text()
            )

            rpm_1 = float(
                self.power_to_torque_rpm.text()
            )

            rpm_2 = float(
                self.power_to_torque_rpm2.text()
            )

            if (
                power <= 0
                or rpm_1 <= 0
                or rpm_2 <= 0
            ):
                raise ValueError

            torque_1 = calculate_torque_from_power(
                power,
                rpm_1
            )

            torque_2 = calculate_torque_from_power(
                power,
                rpm_2
            )

            self.power_to_torque_result.value_label.setText(
                f"{torque_1:.2f} Nm"
            )

            self.power_to_torque_result.detail_label.setText(
                f"{rpm_1:.0f} RPM → {torque_1:.2f} Nm    |    "
                f"{rpm_2:.0f} RPM → {torque_2:.2f} Nm"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "مقادیر توان و دور موتور را به صورت عدد معتبر وارد کنید."
            )


    # ========================================================
    # CALCULATE 2
    # ========================================================

    def calculate_torque_to_power(self):

        try:

            torque = float(
                self.torque_to_power_torque.text()
            )

            rpm = float(
                self.torque_to_power_rpm.text()
            )

            if torque <= 0 or rpm <= 0:
                raise ValueError

            power = calculate_power_from_torque(
                torque,
                rpm
            )

            self.torque_to_power_result.value_label.setText(
                f"{power:.2f} HP"
            )

            self.torque_to_power_result.detail_label.setText(
                f"{torque:.2f} Nm @ {rpm:.0f} RPM"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "مقادیر گشتاور و دور موتور را به صورت عدد معتبر وارد کنید."
            )


    # ========================================================
    # CALCULATE 3
    # ========================================================

    def calculate_pwr(self):

        try:

            power = float(
                self.pwr_power.text()
            )

            weight = float(
                self.pwr_weight.text()
            )

            if power <= 0 or weight <= 0:
                raise ValueError

            pwr = calculate_power_to_weight(
                power,
                weight
            )

            kg_per_hp = weight / power

            self.pwr_result.value_label.setText(
                f"PWR = {pwr:.2f}"
            )

            self.pwr_result.detail_label.setText(
                f"{pwr:.2f} HP/tonne    |    "
                f"{kg_per_hp:.2f} kg/HP"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "توان و وزن خودرو را به صورت عدد معتبر وارد کنید."
            )