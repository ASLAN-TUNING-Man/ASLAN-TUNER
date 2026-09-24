from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


# ============================================================
# ASLAN TUNER - THROTTLE BODY SIZE CALCULATOR
# Formula:
# HP = 0.0575 × Number of Throttle Bodies × Diameter²
# Diameter is in millimeters.
# ============================================================

THROTTLE_HP_FACTOR = 0.0575


def calculate_throttle_power(number_of_bodies: float, diameter_mm: float) -> float:
    """
    Calculates approximate supported power based on
    total throttle body cross-sectional area.

    HP = 0.0575 × N × D²
    """
    return THROTTLE_HP_FACTOR * number_of_bodies * (diameter_mm ** 2)


class ResultCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ResultCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)

        title = QLabel("ESTIMATED POWER CAPACITY")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)

        self.value_label = QLabel("0 HP")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            QLabel {
                color: #ff2b2b;
                font-size: 34px;
                font-weight: bold;
            }
        """)

        self.description_label = QLabel(
            "Approximate throttle airflow capacity"
        )
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(self.value_label)
        layout.addWidget(self.description_label)


class InfoButton(QPushButton):
    def __init__(self, text, title, message, parent=None):
        super().__init__(text, parent)

        self.title = title
        self.message = message

        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: #ff2b2b;
                border: 1px solid #3a3a3a;
                border-radius: 14px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2b2b2b;
                border: 1px solid #ff2b2b;
            }

            QPushButton:pressed {
                background-color: #151515;
            }
        """)

        self.clicked.connect(self.show_info)

    def show_info(self):
        QMessageBox.information(
            self,
            self.title,
            self.message
        )


class ThrottleBodyCalculator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("ASLAN TUNER - Throttle Body Size")
        self.setMinimumSize(620, 650)
        self.resize(700, 720)

        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QDialog {
                background-color: #0d0d0d;
                color: #ffffff;
            }

            QLabel {
                color: #eeeeee;
            }

            QLineEdit {
                background-color: #171717;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 7px;
                padding: 10px 12px;
                font-size: 14px;
                selection-background-color: #b00000;
            }

            QLineEdit:focus {
                border: 1px solid #ff2b2b;
            }

            QPushButton#calculateButton {
                background-color: #d50000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 13px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton#calculateButton:hover {
                background-color: #ff1f1f;
            }

            QPushButton#calculateButton:pressed {
                background-color: #a00000;
            }

            QPushButton#resetButton {
                background-color: #1b1b1b;
                color: #dddddd;
                border: 1px solid #383838;
                border-radius: 8px;
                padding: 13px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#resetButton:hover {
                background-color: #252525;
                border: 1px solid #555555;
            }

            QFrame#InputCard {
                background-color: #121212;
                border: 1px solid #292929;
                border-radius: 10px;
            }

            QFrame#ResultCard {
                background-color: #111111;
                border: 1px solid #3b1717;
                border-radius: 12px;
            }
        """)

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(18)
        scroll.setWidget(content)
        root_layout.addWidget(scroll, 1)

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        title = QLabel("THROTTLE BODY SIZE")
        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            QLabel {
                color: #ff2b2b;
                font-size: 26px;
                font-weight: bold;
            }
        """)

        subtitle = QLabel("ASLAN TUNER")
        subtitle.setAlignment(Qt.AlignCenter)

        subtitle.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ----------------------------------------------------
        # Explanation
        # ----------------------------------------------------

        explanation = QLabel(
            "این محاسبه برای موتورهای تنفس طبیعی طراحی شده است.\n"
            "توان بر اساس تعداد و قطر دریچه‌های گاز محاسبه می‌شود."
        )

        explanation.setAlignment(Qt.AlignCenter)
        explanation.setWordWrap(True)

        explanation.setStyleSheet("""
            QLabel {
                background-color: #111111;
                color: #bdbdbd;
                border: 1px solid #292929;
                border-radius: 9px;
                padding: 14px;
                font-size: 13px;
            }
        """)

        main_layout.addWidget(explanation)

        # ----------------------------------------------------
        # Input Card
        # ----------------------------------------------------

        input_card = QFrame()
        input_card.setObjectName("InputCard")

        input_layout = QGridLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setHorizontalSpacing(12)
        input_layout.setVerticalSpacing(16)

        # Number of throttle bodies
        number_label = QLabel("Number of Throttle Bodies")
        number_label.setStyleSheet("""
            QLabel {
                color: #dddddd;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        number_info = InfoButton(
            "i",
            "Number of Throttle Bodies",
            "تعداد دریچه‌های گاز مورد استفاده در موتور را وارد کنید.\n\n"
            "مثال:\n"
            "1 = یک دریچه گاز\n"
            "4 = چهار دریچه گاز"
        )

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("مثلاً 4")
        self.number_input.setText("4")

        input_layout.addWidget(number_label, 0, 0)
        input_layout.addWidget(number_info, 0, 1)
        input_layout.addWidget(self.number_input, 0, 2)

        # Diameter
        diameter_label = QLabel("Throttle Body Diameter (mm)")
        diameter_label.setStyleSheet("""
            QLabel {
                color: #dddddd;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        diameter_info = InfoButton(
            "i",
            "Throttle Body Diameter",
            "قطر هر دریچه گاز را بر حسب میلی‌متر وارد کنید.\n\n"
            "مثال:\n"
            "36 mm\n"
            "50 mm\n"
            "80 mm"
        )

        self.diameter_input = QLineEdit()
        self.diameter_input.setPlaceholderText("مثلاً 36")
        self.diameter_input.setText("36")

        input_layout.addWidget(diameter_label, 1, 0)
        input_layout.addWidget(diameter_info, 1, 1)
        input_layout.addWidget(self.diameter_input, 1, 2)

        input_layout.setColumnStretch(0, 1)
        input_layout.setColumnStretch(2, 2)

        main_layout.addWidget(input_card)

        # ----------------------------------------------------
        # Formula Card
        # ----------------------------------------------------

        formula_card = QFrame()
        formula_card.setStyleSheet("""
            QFrame {
                background-color: #101010;
                border: 1px solid #252525;
                border-radius: 9px;
            }
        """)

        formula_layout = QVBoxLayout(formula_card)
        formula_layout.setContentsMargins(20, 15, 20, 15)

        formula_title = QLabel("CALCULATION FORMULA")
        formula_title.setAlignment(Qt.AlignCenter)

        formula_title.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 11px;
                font-weight: bold;
            }
        """)

        formula = QLabel(
            "HP = 0.0575 × Number of Throttle Bodies × Diameter²"
        )

        formula.setAlignment(Qt.AlignCenter)

        formula.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        formula_layout.addWidget(formula_title)
        formula_layout.addWidget(formula)

        main_layout.addWidget(formula_card)

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        self.result_card = ResultCard()
        main_layout.addWidget(self.result_card)

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        calculate_button = QPushButton("CALCULATE")
        calculate_button.setObjectName("calculateButton")
        calculate_button.setCursor(Qt.PointingHandCursor)

        reset_button = QPushButton("RESET")
        reset_button.setObjectName("resetButton")
        reset_button.setCursor(Qt.PointingHandCursor)

        calculate_button.clicked.connect(self.calculate)
        reset_button.clicked.connect(self.reset)

        buttons_layout.addWidget(calculate_button)
        buttons_layout.addWidget(reset_button)

        main_layout.addLayout(buttons_layout)

        # ----------------------------------------------------
        # Disclaimer
        # ----------------------------------------------------

        disclaimer = QLabel(
            "⚠ این عدد به معنی تولید مستقیم این توان توسط دریچه گاز نیست.\n"
            "این مقدار ظرفیت تقریبی عبور هوا از دریچه‌ها را نشان می‌دهد و "
            "توان واقعی موتور به سایر عوامل وابسته است."
        )

        disclaimer.setAlignment(Qt.AlignCenter)
        disclaimer.setWordWrap(True)

        disclaimer.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 11px;
                padding: 5px;
            }
        """)

        main_layout.addWidget(disclaimer)

        # Calculate initial example
        self.calculate()

    # ========================================================
    # Calculation
    # ========================================================

    def calculate(self):

        try:
            number_of_bodies = float(
                self.number_input.text().strip()
            )

            diameter_mm = float(
                self.diameter_input.text().strip()
            )

        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "لطفاً تعداد دریچه‌ها و قطر دریچه را به صورت عدد وارد کنید."
            )
            return

        if number_of_bodies <= 0:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "تعداد دریچه‌ها باید بیشتر از صفر باشد."
            )
            return

        if diameter_mm <= 0:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "قطر دریچه باید بیشتر از صفر باشد."
            )
            return

        hp = calculate_throttle_power(
            number_of_bodies,
            diameter_mm
        )

        hp_rounded = round(hp)

        self.result_card.value_label.setText(
            f"{hp_rounded:,} HP"
        )

        self.result_card.description_label.setText(
            f"{number_of_bodies:g} × {diameter_mm:g} mm "
            f"→ approximate airflow capacity"
        )

    # ========================================================
    # Reset
    # ========================================================

    def reset(self):

        self.number_input.setText("")
        self.diameter_input.setText("")

        self.result_card.value_label.setText("0 HP")
        self.result_card.description_label.setText(
            "Approximate throttle airflow capacity"
        )