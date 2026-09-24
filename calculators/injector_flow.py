import csv
import math

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QFrame,
)


# ============================================================
# CONSTANTS
# ============================================================

LB_TO_GRAM = 453.59237
DEFAULT_DUTY = 85.0
MIN_DUTY = 1.0
MAX_DUTY = 100.0

COMMON_INJECTOR_SIZES = [
    50,
    60,
    80,
    100,
    120,
    140,
    160,
    180,
    200,
    220,
    240,
    260,
    280,
    300,
    320,
    350,
    380,
    400,
    440,
    480,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
    850,
    900,
    950,
    1000,
    1100,
    1200,
    1300,
    1400,
    1500,
    1600,
    1700,
    1800,
    2000,
    2200,
    2400,
    2600,
    2800,
    3000,
    3500,
    4000,
]


# ============================================================
# FUEL PRESETS
# ============================================================

FUEL_PRESETS = {
    "Gasoline": {
        "density": 0.745,
        "bsfc_na": 0.50,
        "bsfc_turbo": 0.60,
    },

    "E10 Gasoline": {
        "density": 0.742,
        "bsfc_na": 0.50,
        "bsfc_turbo": 0.60,
    },

    "E85": {
        "density": 0.785,
        "bsfc_na": 0.70,
        "bsfc_turbo": 0.75,
    },

    "Methanol": {
        "density": 0.792,
        "bsfc_na": 1.00,
        "bsfc_turbo": 1.10,
    },

    "Custom": {
        "density": 0.745,
        "bsfc_na": 0.50,
        "bsfc_turbo": 0.60,
    },
}


# ============================================================
# HELPERS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def lbhr_to_ccmin(lb_hr, density_kg_l):
    """
    Convert lb/hr of fuel to cc/min using fuel density.

    density_kg_l:
        kg/L
    """

    density = max(float(density_kg_l), 0.001)

    grams_per_hour = float(lb_hr) * LB_TO_GRAM
    grams_per_minute = grams_per_hour / 60.0

    return grams_per_minute / density


def ccmin_to_lbhr(cc_min, density_kg_l):
    """
    Convert cc/min to lb/hr using fuel density.
    """

    density = max(float(density_kg_l), 0.001)

    grams_per_minute = float(cc_min) * density
    grams_per_hour = grams_per_minute * 60.0

    return grams_per_hour / LB_TO_GRAM


def pressure_correct_flow(
    flow,
    rated_pressure,
    actual_pressure
):
    """
    Injector flow changes approximately with the square root
    of differential pressure.

    F2 = F1 * sqrt(P2 / P1)

    IMPORTANT:
    Both pressures must be DIFFERENTIAL pressure across
    the injector.
    """

    p1 = max(float(rated_pressure), 0.001)
    p2 = max(float(actual_pressure), 0.001)

    return float(flow) * math.sqrt(p2 / p1)


def rated_flow_from_actual(
    flow_actual,
    rated_pressure,
    actual_pressure
):
    """
    Reverse pressure correction.

    F_rated = F_actual / sqrt(P_actual / P_rated)
    """

    p1 = max(float(rated_pressure), 0.001)
    p2 = max(float(actual_pressure), 0.001)

    return float(flow_actual) / math.sqrt(p2 / p1)


# ============================================================
# ENGINE
# ============================================================

class InjectorFlowEngine:

    DEFAULT_DUTY = DEFAULT_DUTY

    def __init__(self):
        pass

    # --------------------------------------------------------
    # REQUIRED FLOW
    # --------------------------------------------------------

    def required_lbhr(
        self,
        horsepower,
        bsfc,
        injector_count,
        duty_cycle,
    ):
        hp = max(float(horsepower), 0.0)
        bsfc = max(float(bsfc), 0.0)
        count = max(int(injector_count), 1)

        duty = clamp(
            float(duty_cycle),
            MIN_DUTY,
            MAX_DUTY
        ) / 100.0

        return (hp * bsfc) / (count * duty)

    # --------------------------------------------------------

    def required_ccmin(
        self,
        horsepower,
        bsfc,
        injector_count,
        duty_cycle,
        density,
    ):
        required_lbhr = self.required_lbhr(
            horsepower,
            bsfc,
            injector_count,
            duty_cycle
        )

        return lbhr_to_ccmin(
            required_lbhr,
            density
        )

    # --------------------------------------------------------

    def supported_hp(
        self,
        injector_flow_lbhr,
        bsfc,
        injector_count,
        duty_cycle,
    ):
        flow = max(float(injector_flow_lbhr), 0.0)
        bsfc = max(float(bsfc), 0.000001)
        count = max(int(injector_count), 1)

        duty = clamp(
            float(duty_cycle),
            MIN_DUTY,
            MAX_DUTY
        ) / 100.0

        return (flow * count * duty) / bsfc

    # --------------------------------------------------------

    def duty_cycle_for_hp(
        self,
        horsepower,
        bsfc,
        injector_flow_lbhr,
        injector_count,
    ):
        hp = max(float(horsepower), 0.0)
        bsfc = max(float(bsfc), 0.000001)
        flow = max(float(injector_flow_lbhr), 0.000001)
        count = max(int(injector_count), 1)

        duty = (hp * bsfc) / (flow * count)

        return duty * 100.0

    # --------------------------------------------------------

    def total_fuel_lbhr(
        self,
        horsepower,
        bsfc,
    ):
        return max(
            float(horsepower),
            0.0
        ) * max(
            float(bsfc),
            0.0
        )

    # --------------------------------------------------------

    def total_fuel_ccmin(
        self,
        horsepower,
        bsfc,
        density,
    ):
        total_lbhr = self.total_fuel_lbhr(
            horsepower,
            bsfc
        )

        return lbhr_to_ccmin(
            total_lbhr,
            density
        )

    # --------------------------------------------------------

    def lph_from_ccmin(self, cc_min):
        return max(
            float(cc_min),
            0.0
        ) * 60.0 / 1000.0

    # --------------------------------------------------------

    def recommended_size(self, required_ccmin):
        required = max(
            float(required_ccmin),
            0.0
        )

        for size in COMMON_INJECTOR_SIZES:
            if size >= required:
                return size

        return COMMON_INJECTOR_SIZES[-1]

    # --------------------------------------------------------
    # COMPLETE CALCULATION
    # --------------------------------------------------------

    def calculate_all(
        self,
        horsepower,
        injector_count,
        bsfc,
        duty_cycle,
        density,
        rated_pressure,
        actual_pressure,
    ):
        hp = max(float(horsepower), 0.0)
        count = max(int(injector_count), 1)
        bsfc = max(float(bsfc), 0.0)
        density = max(float(density), 0.001)

        rated_pressure = max(
            float(rated_pressure),
            0.001
        )

        actual_pressure = max(
            float(actual_pressure),
            0.001
        )

        duty_cycle = clamp(
            float(duty_cycle),
            MIN_DUTY,
            MAX_DUTY
        )

        # ----------------------------------------------------
        # Required injector flow at RATED pressure
        # ----------------------------------------------------

        required_lbhr = self.required_lbhr(
            hp,
            bsfc,
            count,
            duty_cycle
        )

        required_ccmin = lbhr_to_ccmin(
            required_lbhr,
            density
        )

        # ----------------------------------------------------
        # Pressure correction
        # ----------------------------------------------------

        pressure_factor = math.sqrt(
            actual_pressure / rated_pressure
        )

        actual_flow_lbhr = (
            required_lbhr * pressure_factor
        )

        actual_flow_ccmin = (
            required_ccmin * pressure_factor
        )

        # ----------------------------------------------------
        # Total engine fuel consumption
        # ----------------------------------------------------

        total_fuel_lbhr = (
            hp * bsfc
        )

        total_fuel_ccmin = lbhr_to_ccmin(
            total_fuel_lbhr,
            density
        )

        total_fuel_lph = self.lph_from_ccmin(
            total_fuel_ccmin
        )

        # ----------------------------------------------------
        # Capacity at actual pressure
        # ----------------------------------------------------

        supported_hp_actual = self.supported_hp(
            actual_flow_lbhr,
            bsfc,
            count,
            duty_cycle
        )

        # ----------------------------------------------------
        # Duty cycle at actual pressure
        # ----------------------------------------------------

        duty_for_target = self.duty_cycle_for_hp(
            hp,
            bsfc,
            actual_flow_lbhr,
            count
        )

        # ----------------------------------------------------
        # Recommended nominal injector size
        # ----------------------------------------------------

        recommended_size = self.recommended_size(
            required_ccmin
        )

        # ----------------------------------------------------
        # Reverse check
        # ----------------------------------------------------

        equivalent_rated_ccmin = rated_flow_from_actual(
            actual_flow_ccmin,
            rated_pressure,
            actual_pressure
        )

        return {
            "required_lbhr": required_lbhr,
            "required_ccmin": required_ccmin,

            "pressure_factor": pressure_factor,

            "actual_flow_lbhr": actual_flow_lbhr,
            "actual_flow_ccmin": actual_flow_ccmin,

            "equivalent_rated_ccmin":
                equivalent_rated_ccmin,

            "total_fuel_lbhr":
                total_fuel_lbhr,

            "total_fuel_ccmin":
                total_fuel_ccmin,

            "total_fuel_lph":
                total_fuel_lph,

            "supported_hp_actual":
                supported_hp_actual,

            "duty_for_target":
                duty_for_target,

            "recommended_size":
                recommended_size,
        }


# ============================================================
# INFO BUTTON
# ============================================================

class InfoButton(QPushButton):

    def __init__(self, text, parent=None):
        super().__init__("ⓘ", parent)

        self.info_text = text

        self.setFixedSize(34, 34)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QPushButton {
                background: #0b1017;
                color: #ef334d;
                border: 1px solid #2a303a;
                border-radius: 17px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #151b24;
                border-color: #ef334d;
            }

            QPushButton:pressed {
                background: #1d232d;
            }
        """)

        self.clicked.connect(self.show_info)

    def show_info(self):

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "ASLAN TUNER — Information"
        )

        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(250)

        dialog.setWindowFlags(
            Qt.Dialog |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint
        )

        dialog.setStyleSheet("""
            QDialog {
                background: #05070b;
                color: #ffffff;
            }

            QLabel {
                color: #e7eaf0;
            }

            QPushButton {
                background: #10151d;
                color: #ffffff;
                border: 1px solid #252c36;
                border-radius: 9px;
                padding: 9px 20px;
                font-weight: 800;
            }

            QPushButton:hover {
                border-color: #ef334d;
                background: #151b24;
            }
        """)

        layout = QVBoxLayout(dialog)

        layout.setContentsMargins(
            22,
            22,
            22,
            22
        )

        layout.setSpacing(18)

        title = QLabel(
            "ⓘ  Technical Information"
        )

        title.setStyleSheet("""
            color: #ef334d;
            font-size: 18px;
            font-weight: 900;
        """)

        description = QLabel(
            self.info_text
        )

        description.setWordWrap(True)

        description.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        description.setStyleSheet("""
            color: #dce1e8;
            font-size: 13px;
            background: #0b1017;
            border: 1px solid #202731;
            border-radius: 10px;
            padding: 15px;
        """)

        close_button = QPushButton(
            "Close"
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(
            close_button,
            alignment=Qt.AlignRight
        )

        dialog.exec()


# ============================================================
# RESULT CARD
# ============================================================

class ResultCard(QFrame):

    def __init__(
        self,
        title,
        value="—",
        subtitle="",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "ResultCard"
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            15,
            12,
            15,
            12
        )

        layout.setSpacing(4)

        title_label = QLabel(title)

        title_label.setStyleSheet("""
            color: #9299a5;
            font-size: 12px;
            font-weight: bold;
        """)

        self.value_label = QLabel(
            value
        )

        self.value_label.setStyleSheet("""
            color: #ffffff;
            font-size: 22px;
            font-weight: 900;
        """)

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setStyleSheet("""
            color: #676f7c;
            font-size: 10px;
        """)

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            self.value_label
        )

        layout.addWidget(
            subtitle_label
        )


# ============================================================
# PRESSURE CURVE
# ============================================================

class PressureCurveWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(240)

        self.base_flow = 180.0
        self.rated_pressure = 43.5

    def set_data(
        self,
        base_flow,
        rated_pressure,
    ):
        self.base_flow = max(
            float(base_flow),
            0.0
        )

        self.rated_pressure = max(
            float(rated_pressure),
            0.1
        )

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        painter.fillRect(
            rect,
            QColor("#080b10")
        )

        left = 55
        right = rect.width() - 20
        top = 25
        bottom = rect.height() - 40

        # ----------------------------------------------------
        # Grid
        # ----------------------------------------------------

        painter.setPen(
            QPen(
                QColor("#202630"),
                1
            )
        )

        for i in range(6):

            x = left + (
                right - left
            ) * i / 5.0

            painter.drawLine(
                QPointF(x, top),
                QPointF(x, bottom)
            )

        for i in range(5):

            y = top + (
                bottom - top
            ) * i / 4.0

            painter.drawLine(
                QPointF(left, y),
                QPointF(right, y)
            )

        # ----------------------------------------------------
        # Labels
        # ----------------------------------------------------

        painter.setPen(
            QColor("#737b88")
        )

        painter.drawText(
            10,
            20,
            "cc/min"
        )

        painter.drawText(
            left,
            rect.height() - 12,
            "Pressure PSI"
        )

        # ----------------------------------------------------
        # Curve range
        # ----------------------------------------------------

        min_pressure = max(
            self.rated_pressure * 0.4,
            5.0
        )

        max_pressure = max(
            self.rated_pressure * 2.0,
            min_pressure + 10.0
        )

        max_flow = (
            self.base_flow
            * math.sqrt(
                max_pressure
                / self.rated_pressure
            )
        )

        max_flow = max(
            max_flow,
            self.base_flow,
            1.0
        )

        # ----------------------------------------------------
        # Curve
        # ----------------------------------------------------

        painter.setPen(
            QPen(
                QColor("#ef334d"),
                3
            )
        )

        previous = None

        for i in range(101):

            pressure = (
                min_pressure
                + (
                    max_pressure
                    - min_pressure
                ) * i / 100.0
            )

            flow = (
                self.base_flow
                * math.sqrt(
                    pressure
                    / self.rated_pressure
                )
            )

            x = left + (
                right - left
            ) * i / 100.0

            y = bottom - (
                bottom - top
            ) * (
                flow / max_flow
            )

            point = QPointF(
                x,
                y
            )

            if previous is not None:

                painter.drawLine(
                    previous,
                    point
                )

            previous = point

        # ----------------------------------------------------
        # Rated point
        # ----------------------------------------------------

        rated_x = left + (
            right - left
        ) * (
            (
                self.rated_pressure
                - min_pressure
            )
            / (
                max_pressure
                - min_pressure
            )
        )

        rated_flow = self.base_flow

        rated_y = bottom - (
            bottom - top
        ) * (
            rated_flow / max_flow
        )

        painter.setBrush(
            QBrush(
                QColor("#ef334d")
            )
        )

        painter.drawEllipse(
            QPointF(
                rated_x,
                rated_y
            ),
            5,
            5
        )

        painter.setPen(
            QColor("#dce1e8")
        )

        painter.drawText(
            int(rated_x + 8),
            int(rated_y - 8),
            f"{self.rated_pressure:.1f} PSI"
        )


# ============================================================
# PRESSURE WINDOW
# ============================================================

class InjectorPressureWindow(QDialog):

    def __init__(
        self,
        base_flow=180.0,
        rated_pressure=43.5,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Injector Pressure Calculator"
        )

        self.resize(
            750,
            520
        )

        self.setMinimumSize(
            650,
            450
        )

        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QDialog {
                background: #05070b;
                color: #ffffff;
            }

            QLabel {
                color: #e7eaf0;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background: #0b1017;
                color: #ffffff;
                border: 1px solid #252c36;
                border-radius: 9px;
                padding: 9px;
                min-height: 18px;
            }

            QComboBox QAbstractItemView {
                background: #080b10;
                color: #ffffff;
                border: 1px solid #252c36;
                selection-background-color: #ef334d;
                selection-color: #ffffff;
            }

            QPushButton {
                background: #10151d;
                color: #ffffff;
                border: 1px solid #252c36;
                border-radius: 9px;
                padding: 10px 14px;
                font-weight: 800;
            }

            QPushButton:hover {
                border-color: #ef334d;
            }
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        layout.setSpacing(14)

        title = QLabel(
            "تصحیح جریان انژکتور بر اساس فشار دیفرانسیلی"
        )

        title.setStyleSheet("""
            font-size: 18px;
            font-weight: 900;
            color: white;
        """)

        layout.addWidget(title)

        info = QLabel(
            "فرمول: Flow₂ = Flow₁ × √(Pressure₂ / Pressure₁)"
        )

        info.setStyleSheet(
            "color: #9098a5;"
        )

        layout.addWidget(info)

        controls = QGridLayout()

        controls.setHorizontalSpacing(15)
        controls.setVerticalSpacing(12)

        controls.setColumnStretch(0, 2)
        controls.setColumnStretch(1, 3)

        controls.addWidget(
            QLabel("جریان نامی (cc/min)"),
            0,
            0
        )

        self.flow_input = QDoubleSpinBox()

        self.flow_input.setRange(
            0.0,
            10000.0
        )

        self.flow_input.setDecimals(2)

        self.flow_input.setValue(
            base_flow
        )

        controls.addWidget(
            self.flow_input,
            0,
            1
        )

        controls.addWidget(
            QLabel("فشار نامی (PSI)"),
            1,
            0
        )

        self.rated_input = QDoubleSpinBox()

        self.rated_input.setRange(
            0.1,
            500.0
        )

        self.rated_input.setDecimals(2)

        self.rated_input.setValue(
            rated_pressure
        )

        controls.addWidget(
            self.rated_input,
            1,
            1
        )

        controls.addWidget(
            QLabel("فشار واقعی (PSI)"),
            2,
            0
        )

        self.actual_input = QDoubleSpinBox()

        self.actual_input.setRange(
            0.1,
            500.0
        )

        self.actual_input.setDecimals(2)

        self.actual_input.setValue(
            rated_pressure
        )

        controls.addWidget(
            self.actual_input,
            2,
            1
        )

        layout.addLayout(
            controls
        )

        self.result = QLabel(
            "—"
        )

        self.result.setStyleSheet("""
            background: #0c1118;
            border: 1px solid #252c36;
            border-radius: 12px;
            padding: 16px;
            color: #ef334d;
            font-size: 22px;
            font-weight: 900;
        """)

        self.result.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.result
        )

        self.chart = PressureCurveWidget()

        layout.addWidget(
            self.chart
        )

        self.flow_input.valueChanged.connect(
            self.calculate
        )

        self.rated_input.valueChanged.connect(
            self.calculate
        )

        self.actual_input.valueChanged.connect(
            self.calculate
        )

        self.calculate()

    def calculate(self):

        flow = self.flow_input.value()
        rated = self.rated_input.value()
        actual = self.actual_input.value()

        corrected = pressure_correct_flow(
            flow,
            rated,
            actual
        )

        factor = math.sqrt(
            actual / rated
        )

        self.result.setText(
            f"{corrected:.2f} cc/min\n"
            f"Pressure Factor: {factor:.4f}"
        )

        self.chart.set_data(
            flow,
            rated
        )


# ============================================================
# MAIN CALCULATOR
# ============================================================

class InjectorFlowCalculator(QDialog):

    def __init__(
        self,
        params=None,
        parent=None,
    ):
        super().__init__(parent)

        self.params = params or {}
        self.engine = InjectorFlowEngine()
        self.last_results = None

        self.setWindowTitle(
            "ASLAN TUNER — Injector Flow"
        )

        self.resize(
            1150,
            850
        )

        self.setMinimumSize(
            900,
            650
        )

        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QDialog {
                background: #05070b;
                color: #ffffff;
            }

            QWidget {
                background: transparent;
            }

            QLabel {
                color: #e7eaf0;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background: #0b1017;
                color: #ffffff;
                border: 1px solid #252c36;
                border-radius: 9px;
                padding: 9px 12px;
                min-height: 18px;
                selection-background-color: #ef334d;
                selection-color: #ffffff;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border-color: #ef334d;
            }

            QComboBox:hover {
                border-color: #3a424f;
            }

            QComboBox::drop-down {
                background: #0b1017;
                border: none;
                width: 32px;
            }

            QComboBox QAbstractItemView {
                background: #080b10;
                color: #ffffff;
                border: 1px solid #252c36;
                selection-background-color: #ef334d;
                selection-color: #ffffff;
                padding: 5px;
            }

            QScrollArea {
                border: none;
                background: #05070b;
            }

            QScrollBar:vertical {
                background: #080b10;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #252c36;
                border-radius: 6px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #ef334d;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QPushButton {
                background: #10151d;
                color: #ffffff;
                border: 1px solid #252c36;
                border-radius: 9px;
                padding: 10px 14px;
                font-weight: 800;
            }

            QPushButton:hover {
                border-color: #ef334d;
            }

            QPushButton:pressed {
                background: #171d26;
            }

            QPushButton#primary {
                background: #ef334d;
                color: #ffffff;
                border-color: #ef334d;
                font-size: 14px;
                min-height: 42px;
            }

            QPushButton#primary:hover {
                background: #ff4058;
                border-color: #ff4058;
            }

            QFrame#ResultCard {
                background: #0b1017;
                border: 1px solid #202731;
                border-radius: 13px;
            }
        """)

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            18,
            18,
            18,
            18
        )

        root.setSpacing(16)

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = QHBoxLayout()

        header.setSpacing(10)

        title = QLabel(
            "⛽ Injector Flow Calculator"
        )

        title.setStyleSheet("""
            font-size: 23px;
            font-weight: 900;
            color: #ffffff;
        """)

        header.addWidget(title)

        header.addStretch()

        pressure_button = QPushButton(
            "📈 Pressure Curve"
        )

        pressure_button.clicked.connect(
            self.open_pressure_window
        )

        header.addWidget(
            pressure_button
        )

        export_button = QPushButton(
            "📄 Export CSV"
        )

        export_button.clicked.connect(
            self.export_csv
        )

        header.addWidget(
            export_button
        )

        root.addLayout(
            header
        )

        # ----------------------------------------------------
        # Scroll Area
        # ----------------------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        container = QWidget()

        content = QVBoxLayout(
            container
        )

        content.setContentsMargins(
            6,
            6,
            6,
            20
        )

        content.setSpacing(
            18
        )

        # ----------------------------------------------------
        # Mode
        # ----------------------------------------------------

        mode_frame = QFrame()

        mode_frame.setStyleSheet("""
            QFrame {
                background: #080c12;
                border: 1px solid #202731;
                border-radius: 13px;
            }
        """)

        mode_layout = QHBoxLayout(
            mode_frame
        )

        mode_layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        mode_layout.setSpacing(
            15
        )

        mode_label = QLabel(
            "حالت محاسبه"
        )

        mode_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 900;
            color: #ffffff;
        """)

        self.mode = QComboBox()

        self.mode.addItems([
            "Required Injector Size",
            "Injector Power Capacity",
            "Duty Cycle Check",
        ])

        mode_layout.addWidget(
            mode_label
        )

        mode_layout.addWidget(
            self.mode,
            1
        )

        content.addWidget(
            mode_frame
        )

        # ----------------------------------------------------
        # Input Grid
        # ----------------------------------------------------

        grid_frame = QFrame()

        grid_frame.setStyleSheet("""
            QFrame {
                background: #080c12;
                border: 1px solid #202731;
                border-radius: 13px;
            }
        """)

        grid = QGridLayout(
            grid_frame
        )

        grid.setContentsMargins(
            22,
            20,
            22,
            20
        )

        grid.setHorizontalSpacing(
            22
        )

        grid.setVerticalSpacing(
            12
        )

        grid.setColumnStretch(
            0,
            3
        )

        grid.setColumnStretch(
            1,
            5
        )

        grid.setColumnStretch(
            2,
            1
        )

        row = 0

        # ====================================================
        # Horsepower
        # ====================================================

        grid.addWidget(
            QLabel("Target Engine Power"),
            row,
            0
        )

        self.hp = QDoubleSpinBox()

        self.hp.setRange(
            0.0,
            10000.0
        )

        self.hp.setDecimals(
            1
        )

        self.hp.setValue(
            safe_float(
                self.params.get(
                    "horsepower",
                    110
                ),
                110
            )
        )

        self.hp.setSuffix(
            " HP"
        )

        grid.addWidget(
            self.hp,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "توان هدف موتور بر حسب HP. "
                "این مقدار برای محاسبه کل سوخت مورد نیاز استفاده می‌شود."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Injector Count
        # ====================================================

        grid.addWidget(
            QLabel("Number of Injectors"),
            row,
            0
        )

        self.injector_count = QSpinBox()

        self.injector_count.setRange(
            1,
            32
        )

        self.injector_count.setValue(
            safe_int(
                self.params.get(
                    "injector_count",
                    4
                ),
                4
            )
        )

        grid.addWidget(
            self.injector_count,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "تعداد انژکتورهای فعال موتور. "
                "مثلاً موتور 4 سیلندر معمولاً 4 انژکتور دارد."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Engine Type
        # ====================================================

        grid.addWidget(
            QLabel("Engine Type"),
            row,
            0
        )

        self.engine_type = QComboBox()

        self.engine_type.addItems([
            "Naturally Aspirated",
            "Turbo-Supercharged",
            "Custom",
        ])

        grid.addWidget(
            self.engine_type,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "نوع موتور برای انتخاب BSFC پیش‌فرض استفاده می‌شود. "
                "BSFC پیش‌فرض فقط نقطه شروع است و قابل تغییر دستی است."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Fuel
        # ====================================================

        grid.addWidget(
            QLabel("Fuel"),
            row,
            0
        )

        self.fuel = QComboBox()

        self.fuel.addItems([
            "Gasoline",
            "E10 Gasoline",
            "E85",
            "Methanol",
            "Custom",
        ])

        grid.addWidget(
            self.fuel,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "نوع سوخت. انتخاب سوخت مقدار اولیه BSFC "
                "و چگالی سوخت را تعیین می‌کند."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # BSFC
        # ====================================================

        grid.addWidget(
            QLabel("BSFC"),
            row,
            0
        )

        self.bsfc = QDoubleSpinBox()

        self.bsfc.setRange(
            0.01,
            5.00
        )

        self.bsfc.setDecimals(
            3
        )

        self.bsfc.setSingleStep(
            0.01
        )

        self.bsfc.setSuffix(
            " lb/HP/hr"
        )

        grid.addWidget(
            self.bsfc,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "Brake Specific Fuel Consumption. "
                "مقدار واقعی به موتور، بازده، AFR/Lambda، "
                "بوست و شرایط کاری بستگی دارد."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Duty Cycle
        # ====================================================

        grid.addWidget(
            QLabel("Maximum Duty Cycle"),
            row,
            0
        )

        self.duty = QDoubleSpinBox()

        self.duty.setRange(
            1.0,
            100.0
        )

        self.duty.setDecimals(
            1
        )

        self.duty.setValue(
            safe_float(
                self.params.get(
                    "duty_cycle",
                    DEFAULT_DUTY
                ),
                DEFAULT_DUTY
            )
        )

        self.duty.setSuffix(
            " %"
        )

        grid.addWidget(
            self.duty,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "حداکثر Duty Cycle مجاز برای سایزینگ. "
                "85٪ یک مقدار عملی برای سایزینگ است، "
                "نه یک قانون فیزیکی مطلق."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Density
        # ====================================================

        grid.addWidget(
            QLabel("Fuel Density"),
            row,
            0
        )

        self.density = QDoubleSpinBox()

        self.density.setRange(
            0.100,
            2.000
        )

        self.density.setDecimals(
            4
        )

        self.density.setSingleStep(
            0.001
        )

        self.density.setSuffix(
            " kg/L"
        )

        grid.addWidget(
            self.density,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "چگالی سوخت بر حسب kg/L. "
                "تبدیل lb/hr به cc/min بر اساس همین مقدار انجام می‌شود."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Rated Differential Pressure
        # ====================================================

        grid.addWidget(
            QLabel(
                "Rated Differential Pressure"
            ),
            row,
            0
        )

        self.rated_pressure = QDoubleSpinBox()

        self.rated_pressure.setRange(
            0.1,
            500.0
        )

        self.rated_pressure.setDecimals(
            2
        )

        self.rated_pressure.setValue(
            safe_float(
                self.params.get(
                    "rated_pressure",
                    43.5
                ),
                43.5
            )
        )

        self.rated_pressure.setSuffix(
            " PSI"
        )

        grid.addWidget(
            self.rated_pressure,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "فشار دیفرانسیلی مرجع انژکتور؛ "
                "همان فشاری که سازنده جریان نامی انژکتور را "
                "در آن اعلام کرده است."
            ),
            row,
            2
        )

        row += 1

        # ====================================================
        # Actual Differential Pressure
        # ====================================================

        grid.addWidget(
            QLabel(
                "Actual Differential Pressure"
            ),
            row,
            0
        )

        self.actual_pressure = QDoubleSpinBox()

        self.actual_pressure.setRange(
            0.1,
            500.0
        )

        self.actual_pressure.setDecimals(
            2
        )

        self.actual_pressure.setValue(
            safe_float(
                self.params.get(
                    "actual_pressure",
                    43.5
                ),
                43.5
            )
        )

        self.actual_pressure.setSuffix(
            " PSI"
        )

        grid.addWidget(
            self.actual_pressure,
            row,
            1
        )

        grid.addWidget(
            InfoButton(
                "فشار واقعی دیفرانسیلی روی انژکتور. "
                "در موتور توربو نباید صرفاً فشار ریل را وارد کنید. "
                "فشار دیفرانسیلی تقریباً برابر است با "
                "Fuel Rail Pressure منهای MAP."
            ),
            row,
            2
        )

        row += 1

        content.addWidget(
            grid_frame
        )

        # ----------------------------------------------------
        # Calculate Button
        # ----------------------------------------------------

        calculate_button = QPushButton(
            "⚡ Calculate"
        )

        calculate_button.setObjectName(
            "primary"
        )

        calculate_button.clicked.connect(
            self.calculate
        )

        content.addWidget(
            calculate_button
        )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        result_grid = QGridLayout()

        result_grid.setHorizontalSpacing(
            14
        )

        result_grid.setVerticalSpacing(
            14
        )

        result_grid.setColumnStretch(
            0,
            1
        )

        result_grid.setColumnStretch(
            1,
            1
        )

        self.card_required_cc = ResultCard(
            "Required Injector Flow",
            "—",
            "cc/min @ rated pressure"
        )

        self.card_required_lb = ResultCard(
            "Required Injector Flow",
            "—",
            "lb/hr @ rated pressure"
        )

        self.card_actual_cc = ResultCard(
            "Actual Injector Flow",
            "—",
            "cc/min @ actual differential pressure"
        )

        self.card_actual_lb = ResultCard(
            "Actual Injector Flow",
            "—",
            "lb/hr @ actual differential pressure"
        )

        self.card_total = ResultCard(
            "Total Fuel Flow",
            "—",
            "L/hr — entire engine"
        )

        self.card_capacity = ResultCard(
            "Supported Power",
            "—",
            "HP @ actual pressure"
        )

        self.card_duty = ResultCard(
            "Duty Cycle",
            "—",
            "for target power"
        )

        self.card_recommended = ResultCard(
            "Recommended Injector",
            "—",
            "common nominal size"
        )

        cards = [
            self.card_required_cc,
            self.card_required_lb,
            self.card_actual_cc,
            self.card_actual_lb,
            self.card_total,
            self.card_capacity,
            self.card_duty,
            self.card_recommended,
        ]

        for i, card in enumerate(cards):

            result_grid.addWidget(
                card,
                i // 2,
                i % 2
            )

        content.addLayout(
            result_grid
        )

        # ----------------------------------------------------
        # Technical Status
        # ----------------------------------------------------

        self.status = QLabel(
            "Ready"
        )

        self.status.setWordWrap(
            True
        )

        self.status.setStyleSheet("""
            background: #0b1017;
            border: 1px solid #202731;
            border-radius: 12px;
            padding: 14px;
            color: #9ca5b2;
        """)

        content.addWidget(
            self.status
        )

        # ----------------------------------------------------
        # Pressure Chart
        # ----------------------------------------------------

        chart_title = QLabel(
            "Injector Flow vs Differential Pressure"
        )

        chart_title.setStyleSheet("""
            font-size: 15px;
            font-weight: 900;
            color: white;
        """)

        content.addWidget(
            chart_title
        )

        self.chart = PressureCurveWidget()

        content.addWidget(
            self.chart
        )

        content.addStretch()

        scroll.setWidget(
            container
        )

        root.addWidget(
            scroll
        )

        # ----------------------------------------------------
        # Connections
        # ----------------------------------------------------

        self.fuel.currentIndexChanged.connect(
            self.update_bsfc_from_fuel
        )

        self.engine_type.currentIndexChanged.connect(
            self.update_bsfc_from_fuel
        )

        self.mode.currentIndexChanged.connect(
            self.update_mode
        )

        # ----------------------------------------------------
        # Initial setup
        # ----------------------------------------------------

        self.update_bsfc_from_fuel(
            preserve_custom=False
        )

        self.calculate()

    # ========================================================
    # BSFC
    # ========================================================

    def update_bsfc_from_fuel(
        self,
        index=None,
        preserve_custom=True,
    ):

        fuel_name = self.fuel.currentText()

        preset = FUEL_PRESETS.get(
            fuel_name,
            FUEL_PRESETS["Custom"]
        )

        density = preset["density"]

        self.density.setValue(
            density
        )

        engine_type = (
            self.engine_type.currentText()
        )

        if engine_type == "Turbo-Supercharged":

            bsfc = preset[
                "bsfc_turbo"
            ]

        elif engine_type == "Naturally Aspirated":

            bsfc = preset[
                "bsfc_na"
            ]

        else:

            if preserve_custom:
                return

            bsfc = preset[
                "bsfc_na"
            ]

        self.bsfc.setValue(
            bsfc
        )

        self.calculate()

    # ========================================================
    # MODE
    # ========================================================

    def update_mode(self):

        mode = self.mode.currentText()

        if mode == "Required Injector Size":

            self.status.setText(
                "حالت سایزینگ: جریان مورد نیاز هر انژکتور "
                "در Duty Cycle انتخاب‌شده محاسبه می‌شود."
            )

        elif mode == "Injector Power Capacity":

            self.status.setText(
                "حالت ظرفیت: بررسی می‌شود این سایز انژکتور "
                "در فشار واقعی چه توان موتوری را پشتیبانی می‌کند."
            )

        else:

            self.status.setText(
                "حالت Duty Cycle: مشخص می‌شود برای توان هدف، "
                "انژکتور در فشار واقعی چند درصد Duty خواهد داشت."
            )

        self.calculate()

    # ========================================================
    # CALCULATE
    # ========================================================

    def calculate(self):

        try:

            hp = self.hp.value()
            count = self.injector_count.value()
            bsfc = self.bsfc.value()
            duty = self.duty.value()
            density = self.density.value()
            rated_pressure = self.rated_pressure.value()
            actual_pressure = self.actual_pressure.value()

            if hp <= 0:

                self.status.setText(
                    "⚠ توان موتور باید بیشتر از صفر باشد."
                )

                return

            if bsfc <= 0:

                self.status.setText(
                    "⚠ BSFC باید بیشتر از صفر باشد."
                )

                return

            if density <= 0:

                self.status.setText(
                    "⚠ چگالی سوخت باید بیشتر از صفر باشد."
                )

                return

            if rated_pressure <= 0:

                self.status.setText(
                    "⚠ فشار نامی باید بیشتر از صفر باشد."
                )

                return

            if actual_pressure <= 0:

                self.status.setText(
                    "⚠ فشار واقعی باید بیشتر از صفر باشد."
                )

                return

            results = self.engine.calculate_all(
                horsepower=hp,
                injector_count=count,
                bsfc=bsfc,
                duty_cycle=duty,
                density=density,
                rated_pressure=rated_pressure,
                actual_pressure=actual_pressure,
            )

            self.last_results = results

            # ------------------------------------------------
            # Cards
            # ------------------------------------------------

            self.card_required_cc.value_label.setText(
                f"{results['required_ccmin']:.2f}"
            )

            self.card_required_lb.value_label.setText(
                f"{results['required_lbhr']:.2f}"
            )

            self.card_actual_cc.value_label.setText(
                f"{results['actual_flow_ccmin']:.2f}"
            )

            self.card_actual_lb.value_label.setText(
                f"{results['actual_flow_lbhr']:.2f}"
            )

            self.card_total.value_label.setText(
                f"{results['total_fuel_lph']:.2f}"
            )

            self.card_capacity.value_label.setText(
                f"{results['supported_hp_actual']:.1f}"
            )

            duty_target = results[
                "duty_for_target"
            ]

            self.card_duty.value_label.setText(
                f"{duty_target:.1f}%"
            )

            self.card_recommended.value_label.setText(
                f"{results['recommended_size']} cc/min"
            )

            # ------------------------------------------------
            # Status
            # ------------------------------------------------

            factor = results[
                "pressure_factor"
            ]

            pressure_difference = (
                actual_pressure
                - rated_pressure
            )

            if duty_target > duty:

                status_text = (
                    "⚠ Duty Cycle هدف از حد تعیین‌شده بیشتر است. "
                    "انژکتور بزرگ‌تر یا فشار/شرایط مناسب‌تر لازم است."
                )

            elif duty_target >= 80.0:

                status_text = (
                    "⚠ Duty Cycle نسبتاً بالا است. "
                    "برای حاشیه اطمینان بیشتر، سایز بزرگ‌تر بررسی شود."
                )

            else:

                status_text = (
                    "✓ محاسبه معتبر است. "
                    "Duty Cycle در محدوده قابل قبول قرار دارد."
                )

            pressure_text = (
                f"\n\nPressure Factor: {factor:.4f}"
                f"\nRated Differential Pressure: "
                f"{rated_pressure:.2f} PSI"
                f"\nActual Differential Pressure: "
                f"{actual_pressure:.2f} PSI"
                f"\nPressure Difference: "
                f"{pressure_difference:+.2f} PSI"
            )

            self.status.setText(
                status_text
                + pressure_text
            )

            # ------------------------------------------------
            # Chart
            # ------------------------------------------------

            self.chart.set_data(
                results["required_ccmin"],
                rated_pressure
            )

        except Exception as exc:

            self.status.setText(
                f"⚠ Calculation error: {exc}"
            )

    # ========================================================
    # PRESSURE WINDOW
    # ========================================================

    def open_pressure_window(self):

        flow = 180.0

        if self.last_results:

            flow = self.last_results[
                "required_ccmin"
            ]

        window = InjectorPressureWindow(
            base_flow=flow,
            rated_pressure=self.rated_pressure.value(),
            parent=self
        )

        window.exec()

    # ========================================================
    # CSV EXPORT
    # ========================================================

    def export_csv(self):

        if not self.last_results:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "ابتدا محاسبه را انجام دهید."
            )

            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Injector Flow CSV",
            "injector_flow.csv",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        r = self.last_results

        rows = [
            ["ASLAN TUNER - Injector Flow"],
            [],
            ["Parameter", "Value", "Unit"],

            [
                "Target Engine Power",
                self.hp.value(),
                "HP"
            ],

            [
                "Injector Count",
                self.injector_count.value(),
                "injectors"
            ],

            [
                "Engine Type",
                self.engine_type.currentText(),
                ""
            ],

            [
                "Fuel",
                self.fuel.currentText(),
                ""
            ],

            [
                "BSFC",
                self.bsfc.value(),
                "lb/HP/hr"
            ],

            [
                "Maximum Duty Cycle",
                self.duty.value(),
                "%"
            ],

            [
                "Fuel Density",
                self.density.value(),
                "kg/L"
            ],

            [
                "Rated Differential Pressure",
                self.rated_pressure.value(),
                "PSI"
            ],

            [
                "Actual Differential Pressure",
                self.actual_pressure.value(),
                "PSI"
            ],

            [],
            ["RESULTS", "", ""],

            [
                "Required Injector Flow",
                r["required_ccmin"],
                "cc/min @ rated pressure"
            ],

            [
                "Required Injector Flow",
                r["required_lbhr"],
                "lb/hr @ rated pressure"
            ],

            [
                "Actual Injector Flow",
                r["actual_flow_ccmin"],
                "cc/min @ actual pressure"
            ],

            [
                "Actual Injector Flow",
                r["actual_flow_lbhr"],
                "lb/hr @ actual pressure"
            ],

            [
                "Pressure Factor",
                r["pressure_factor"],
                ""
            ],

            [
                "Total Fuel Flow",
                r["total_fuel_lph"],
                "L/hr"
            ],

            [
                "Supported Power",
                r["supported_hp_actual"],
                "HP"
            ],

            [
                "Duty Cycle For Target",
                r["duty_for_target"],
                "%"
            ],

            [
                "Recommended Injector",
                r["recommended_size"],
                "cc/min nominal"
            ],
        ]

        try:

            with open(
                path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:

                writer = csv.writer(
                    file
                )

                writer.writerows(
                    rows
                )

            QMessageBox.information(
                self,
                "ASLAN TUNER",
                "فایل CSV با موفقیت ذخیره شد."
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "ASLAN TUNER",
                f"خطا در ذخیره فایل:\n{exc}"
            )