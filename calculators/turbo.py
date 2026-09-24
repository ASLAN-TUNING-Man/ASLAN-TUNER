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
    QGridLayout,
    QComboBox,
)


# ============================================================
# ASLAN TUNER - TURBO SIZING CORE
# ============================================================

LITER_TO_CUBIC_INCH = 61.0237441
GAS_CONSTANT = 639.6

# Standard compressor inlet reference conditions
STANDARD_PRESSURE_PSI = 14.696
STANDARD_TEMPERATURE_K = 288.15


# ============================================================
# PRESSURE RATIO
# ============================================================

def calculate_pressure_ratio(boost_psi, atmospheric_psi):
    """
    Compressor Pressure Ratio

    PR = Compressor Outlet Absolute Pressure
         / Compressor Inlet Absolute Pressure

    P2 = Atmospheric + Boost
    P1 = Atmospheric

    Example:
        Atmospheric = 12.5 PSI
        Boost = 10 PSI

        P2 = 22.5 PSIA
        P1 = 12.5 PSIA

        PR = 22.5 / 12.5 = 1.80
    """

    if boost_psi < 0:
        raise ValueError(
            "Boost pressure cannot be negative."
        )

    if atmospheric_psi <= 0:
        raise ValueError(
            "Atmospheric pressure must be greater than zero."
        )

    compressor_outlet_absolute = (
        atmospheric_psi + boost_psi
    )

    compressor_inlet_absolute = (
        atmospheric_psi
    )

    return (
        compressor_outlet_absolute
        / compressor_inlet_absolute
    )


# ============================================================
# ACTUAL AIRFLOW
# ============================================================

def calculate_airflow_lb_min(
    rpm,
    displacement_l,
    atmospheric_psi,
    boost_psi,
    manifold_temp_c,
    ve_percent,
):
    """
    Calculates actual engine mass airflow in lb/min.

    Four-stroke engine airflow relationship:

    W = MAP * VE * (RPM / 2) * Vd
        / R / (460 + T)

    Where:

        W   = actual airflow, lb/min
        MAP = manifold absolute pressure, psia
        VE  = volumetric efficiency
        RPM = engine speed
        Vd  = engine displacement, cubic inches
        R   = gas constant
        T   = manifold temperature, Fahrenheit
    """

    if rpm <= 0:
        raise ValueError(
            "RPM must be greater than zero."
        )

    if displacement_l <= 0:
        raise ValueError(
            "Engine displacement must be greater than zero."
        )

    if atmospheric_psi <= 0:
        raise ValueError(
            "Atmospheric pressure must be greater than zero."
        )

    if boost_psi < 0:
        raise ValueError(
            "Boost pressure cannot be negative."
        )

    if manifold_temp_c <= -273.15:
        raise ValueError(
            "Invalid manifold temperature."
        )

    if ve_percent <= 0 or ve_percent > 150:
        raise ValueError(
            "VE must be between 0 and 150 percent."
        )

    # --------------------------------------------------------
    # Manifold Absolute Pressure
    # --------------------------------------------------------

    map_absolute_psi = (
        atmospheric_psi + boost_psi
    )

    # --------------------------------------------------------
    # VE
    # --------------------------------------------------------

    ve = ve_percent / 100.0

    # --------------------------------------------------------
    # Temperature
    # Celsius -> Fahrenheit
    # --------------------------------------------------------

    manifold_temp_f = (
        manifold_temp_c * 9.0 / 5.0
    ) + 32.0

    # --------------------------------------------------------
    # Displacement
    # Liters -> Cubic Inches
    # --------------------------------------------------------

    displacement_ci = (
        displacement_l
        * LITER_TO_CUBIC_INCH
    )

    # --------------------------------------------------------
    # Actual Airflow
    # --------------------------------------------------------

    airflow_lb_min = (
        map_absolute_psi
        * ve
        * (rpm / 2.0)
        * displacement_ci
        / GAS_CONSTANT
        / (460.0 + manifold_temp_f)
    )

    return airflow_lb_min


# ============================================================
# TURBO AIRFLOW TARGET
# ============================================================

def calculate_turbo_target_airflow_lb_min(
    horsepower
):
    """
    Calculates a practical turbo compressor airflow target
    from engine horsepower.

    Approximation:

        Turbo Airflow = HP / 10

    Output:
        lb/min
    """

    if horsepower <= 0:
        raise ValueError(
            "Horsepower must be greater than zero."
        )

    turbo_airflow_lb_min = (
        horsepower / 10.0
    )

    return turbo_airflow_lb_min


# ============================================================
# CORRECTED AIRFLOW
# ============================================================

def calculate_corrected_airflow_lb_min(
    actual_airflow_lb_min,
    atmospheric_psi,
    inlet_temp_c,
):
    """
    Calculates compressor corrected airflow.

    Corrected Flow:

        Wc = Wactual
             * sqrt(T1 / Tstd)
             / (P1 / Pstd)

    Where:

        Wc      = corrected airflow
        Wactual = actual airflow
        T1      = compressor inlet absolute temperature, K
        Tstd    = standard temperature, 288.15 K
        P1      = compressor inlet absolute pressure, PSI
        Pstd    = standard pressure, 14.696 PSI

    The purpose is to normalize compressor flow
    to standard inlet conditions.
    """

    if actual_airflow_lb_min < 0:
        raise ValueError(
            "Actual airflow cannot be negative."
        )

    if atmospheric_psi <= 0:
        raise ValueError(
            "Atmospheric pressure must be greater than zero."
        )

    if inlet_temp_c <= -273.15:
        raise ValueError(
            "Invalid inlet temperature."
        )

    # Celsius -> Kelvin

    inlet_temp_k = (
        inlet_temp_c + 273.15
    )

    corrected_flow = (
        actual_airflow_lb_min
        * math.sqrt(
            inlet_temp_k
            / STANDARD_TEMPERATURE_K
        )
        / (
            atmospheric_psi
            / STANDARD_PRESSURE_PSI
        )
    )

    return corrected_flow


# ============================================================
# PRESSURE AXIS
# ============================================================

def generate_pressure_axis(
    center_pressure,
    count,
):
    """
    Generates atmospheric pressure values.

    The user-selected atmospheric pressure is always
    retained as one of the table pressure points.
    """

    if center_pressure <= 0:
        raise ValueError(
            "Atmospheric pressure must be greater than zero."
        )

    if count <= 1:
        return [
            round(center_pressure, 2)
        ]

    if count <= 8:
        span = 4.0
    elif count <= 16:
        span = 5.0
    else:
        span = 6.0

    start = max(
        1.0,
        center_pressure - span
    )

    end = (
        center_pressure + span
    )

    step = (
        end - start
    ) / (count - 1)

    values = []

    for i in range(count):

        pressure = (
            start + step * i
        )

        values.append(
            round(pressure, 2)
        )

    # Make sure the user-selected pressure
    # is represented exactly.

    nearest_index = min(
        range(len(values)),
        key=lambda i:
            abs(
                values[i]
                - center_pressure
            )
    )

    values[
        nearest_index
    ] = round(
        center_pressure,
        2
    )

    return values


# ============================================================
# RPM AXIS
# ============================================================

def generate_rpm_axis(
    idle_rpm,
    cutoff_rpm,
    count,
):
    """
    Generates RPM points across the complete
    engine operating range.

    RPM values are rounded to practical,
    tuner-friendly intervals depending on
    the selected table size.
    """

    if idle_rpm <= 0:
        raise ValueError(
            "Idle RPM must be greater than zero."
        )

    if cutoff_rpm <= idle_rpm:
        raise ValueError(
            "Cutoff RPM must be greater than idle RPM."
        )

    if count <= 1:
        return [
            int(round(idle_rpm))
        ]

    step = (
        cutoff_rpm - idle_rpm
    ) / (count - 1)

    # --------------------------------------------------------
    # Choose a practical RPM rounding step.
    # This prevents ugly values such as:
    # 1437, 1871, 2306, etc.
    # --------------------------------------------------------

    raw_step = step

    if raw_step >= 1000:
        rpm_round = 1000
    elif raw_step >= 500:
        rpm_round = 500
    elif raw_step >= 250:
        rpm_round = 250
    elif raw_step >= 100:
        rpm_round = 100
    elif raw_step >= 50:
        rpm_round = 50
    else:
        rpm_round = 10

    rpm_values = []

    for i in range(count):

        raw_rpm = (
            idle_rpm
            + step * i
        )

        if i == 0:
            rpm = int(round(idle_rpm))
        elif i == count - 1:
            rpm = int(round(cutoff_rpm))
        else:
            rpm = int(
                round(
                    raw_rpm
                    / rpm_round
                )
                * rpm_round
            )

        rpm_values.append(
            rpm
        )

    # --------------------------------------------------------
    # Make sure RPM values remain strictly increasing.
    # --------------------------------------------------------

    for i in range(1, len(rpm_values)):

        if rpm_values[i] <= rpm_values[i - 1]:

            rpm_values[i] = (
                rpm_values[i - 1]
                + rpm_round
            )

    # --------------------------------------------------------
    # Never exceed cutoff RPM.
    # --------------------------------------------------------

    rpm_values[-1] = int(
        round(cutoff_rpm)
    )

    # --------------------------------------------------------
    # Fix possible duplicate / reversed values
    # from very small RPM ranges.
    # --------------------------------------------------------

    for i in range(
        len(rpm_values) - 2,
        -1,
        -1
    ):

        if rpm_values[i] >= rpm_values[i + 1]:

            rpm_values[i] = max(
                int(round(idle_rpm)),
                rpm_values[i + 1]
                - rpm_round
            )

    rpm_values[0] = int(
        round(idle_rpm)
    )

    return rpm_values


# ============================================================
# TABLE DIMENSIONS
# ============================================================

def get_table_dimensions(
    table_size
):
    """
    Returns:

        rows    = RPM points
        columns = atmospheric pressure points
    """

    mapping = {
        "8 × 8": (8, 8),
        "16 × 16": (16, 16),
        "32 × 32": (32, 32),

        "16 × 32": (16, 32),
        "32 × 16": (32, 16),

        "16 × 8": (16, 8),
        "8 × 16": (8, 16),

        "32 × 8": (32, 8),
        "8 × 32": (8, 32),
    }

    if table_size not in mapping:
        raise ValueError(
            "Invalid table size."
        )

    return mapping[
        table_size
    ]


# ============================================================
# TURBO GRID
# ============================================================

def calculate_turbo_grid(
    idle_rpm,
    cutoff_rpm,
    displacement_l,
    boost_psi,
    atmospheric_psi,
    manifold_temp_c,
    ve_percent,
    table_size,
):
    """
    Creates the Turbo Sizing grid.

    Rows:
        RPM

    Columns:
        Atmospheric Pressure (PSI)

    Cell:
        Actual Airflow (lb/min)

    Additional calculated values:
        Pressure Ratio
        Corrected Airflow
    """

    rows, columns = (
        get_table_dimensions(
            table_size
        )
    )

    rpm_axis = generate_rpm_axis(
        idle_rpm,
        cutoff_rpm,
        rows
    )

    pressure_axis = generate_pressure_axis(
        atmospheric_psi,
        columns
    )

    grid = []

    for rpm in rpm_axis:

        row = []

        for pressure in pressure_axis:

            actual_airflow = (
                calculate_airflow_lb_min(
                    rpm=rpm,
                    displacement_l=displacement_l,
                    atmospheric_psi=pressure,
                    boost_psi=boost_psi,
                    manifold_temp_c=manifold_temp_c,
                    ve_percent=ve_percent,
                )
            )

            corrected_airflow = (
                calculate_corrected_airflow_lb_min(
                    actual_airflow_lb_min=
                        actual_airflow,
                    atmospheric_psi=
                        pressure,
                    inlet_temp_c=
                        manifold_temp_c,
                )
            )

            pressure_ratio = (
                calculate_pressure_ratio(
                    boost_psi,
                    pressure
                )
            )

            row.append(
                {
                    "rpm":
                        rpm,

                    "atmospheric_psi":
                        pressure,

                    "airflow_lb_min":
                        actual_airflow,

                    "corrected_airflow_lb_min":
                        corrected_airflow,

                    "pressure_ratio":
                        pressure_ratio,
                }
            )

        grid.append(row)

    return (
        rpm_axis,
        pressure_axis,
        grid
    )


# ============================================================
# INFO BUTTON
# ============================================================

class InfoButton(QPushButton):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            "!",
            parent
        )

        self.setFixedSize(
            28,
            28
        )

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

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border: 1px solid #252525;
                border-radius: 10px;
            }
        """)

        self.layout = QVBoxLayout(
            self
        )

        self.layout.setContentsMargins(
            18,
            16,
            18,
            16
        )

        self.layout.setSpacing(
            7
        )

    def clear(self):

        while self.layout.count():

            item = (
                self.layout.takeAt(
                    0
                )
            )

            widget = (
                item.widget()
            )

            if widget:
                widget.deleteLater()

    def add_result(
        self,
        title,
        value,
        detail=""
    ):

        self.clear()

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
            }
        """)

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet("""
            QLabel {
                color: #ff1e1e;
                font-size: 27px;
                font-weight: bold;
            }
        """)

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.layout.addWidget(
            title_label
        )

        self.layout.addWidget(
            value_label
        )

        if detail:

            detail_label = QLabel(
                detail
            )

            detail_label.setStyleSheet("""
                QLabel {
                    color: #aaaaaa;
                    font-size: 12px;
                }
            """)

            detail_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.layout.addWidget(
                detail_label
            )


# ============================================================
# SECTION CARD
# ============================================================

class SectionCard(QFrame):

    def __init__(
        self,
        title,
        info_text,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.setStyleSheet("""
            QFrame {
                background-color: #0b0b0b;
                border: 1px solid #242424;
                border-radius: 12px;
            }
        """)

        self.main_layout = (
            QVBoxLayout(self)
        )

        self.main_layout.setContentsMargins(
            18,
            16,
            18,
            18
        )

        self.main_layout.setSpacing(
            12
        )

        header = QHBoxLayout()

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 17px;
                font-weight: bold;
                border: none;
            }
        """)

        info = InfoButton()

        info.clicked.connect(
            lambda:
            QMessageBox.information(
                self,
                title,
                info_text
            )
        )

        header.addWidget(
            title_label
        )

        header.addStretch()

        header.addWidget(
            info
        )

        self.main_layout.addLayout(
            header
        )


# ============================================================
# TURBO CALCULATOR
# ============================================================

class TurboCalculator(QDialog):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "ASLAN TUNER - Turbo Sizing"
        )

        self.resize(
            760,
            900
        )

        self.setMinimumSize(
            540,
            650
        )

        self.setWindowFlags(
            Qt.WindowType.Window
            |
            Qt.WindowType.WindowMinimizeButtonHint
            |
            Qt.WindowType.WindowMaximizeButtonHint
            |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QDialog {
                background-color: #050505;
            }

            QWidget {
                background-color: #050505;
            }

            QLabel {
                color: #dddddd;
                background: transparent;
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
                border: 1px solid #ff1e1e;
            }

            QPushButton {
                background-color: #151515;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 7px;
                padding: 9px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #ff1e1e;
                color: #000000;
                border: 1px solid #ff1e1e;
            }

            QComboBox {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 7px;
                padding: 8px;
                font-size: 13px;
            }

            QComboBox:focus {
                border: 1px solid #ff1e1e;
            }

            QComboBox QAbstractItemView {
                background-color: #111111;
                color: #ffffff;
                selection-background-color: #ff1e1e;
                selection-color: #000000;
            }

            QScrollArea {
                border: none;
                background-color: #050505;
            }

            QScrollBar:vertical {
                background: #0b0b0b;
                width: 12px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background: #333333;
                border-radius: 6px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #ff1e1e;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background: #0b0b0b;
                height: 12px;
                margin: 0px;
            }

            QScrollBar::handle:horizontal {
                background: #333333;
                border-radius: 6px;
                min-width: 30px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #ff1e1e;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        self.build_ui()

    # --------------------------------------------------------
    # CREATE INPUT
    # --------------------------------------------------------

    def create_input(
        self,
        layout,
        label_text,
        default_value
    ):

        row = QHBoxLayout()

        label = QLabel(
            label_text
        )

        label.setMinimumWidth(
            250
        )

        label.setStyleSheet("""
            QLabel {
                color: #dddddd;
                font-size: 13px;
                border: none;
            }
        """)

        edit = QLineEdit(
            str(default_value)
        )

        edit.setMinimumWidth(
            160
        )

        row.addWidget(
            label
        )

        row.addWidget(
            edit
        )

        layout.addLayout(
            row
        )

        return edit

    # --------------------------------------------------------
    # CREATE COMBO
    # --------------------------------------------------------

    def create_combo(
        self,
        layout,
        label_text,
        values,
        default_value
    ):

        row = QHBoxLayout()

        label = QLabel(
            label_text
        )

        label.setMinimumWidth(
            250
        )

        label.setStyleSheet("""
            QLabel {
                color: #dddddd;
                font-size: 13px;
                border: none;
            }
        """)

        combo = QComboBox()

        combo.addItems(
            values
        )

        index = combo.findText(
            default_value
        )

        if index >= 0:

            combo.setCurrentIndex(
                index
            )

        combo.setMinimumWidth(
            160
        )

        row.addWidget(
            label
        )

        row.addWidget(
            combo
        )

        layout.addLayout(
            row
        )

        return combo

    # --------------------------------------------------------
    # BUILD UI
    # --------------------------------------------------------

    def build_ui(
        self
    ):

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        container = QWidget()

        container_layout = (
            QVBoxLayout(
                container
            )
        )

        container_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        container_layout.setSpacing(
            15
        )

        # ====================================================
        # HEADER
        # ====================================================

        title = QLabel(
            "ASLAN TUNER"
        )

        title.setStyleSheet("""
            QLabel {
                color: #ff1e1e;
                font-size: 27px;
                font-weight: bold;
                border: none;
            }
        """)

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle = QLabel(
            "TURBO SIZING / BOOST ANALYSIS"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 12px;
                letter-spacing: 1px;
                border: none;
            }
        """)

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        container_layout.addWidget(
            title
        )

        container_layout.addWidget(
            subtitle
        )

        # ====================================================
        # INPUT SECTION
        # ====================================================

        input_card = SectionCard(
            "1. پارامترهای موتور و توربو",
            "تمام پارامترهای اصلی موتور، فشار بوست و شرایط هوای ورودی را وارد کنید."
        )

        input_layout = (
            input_card.main_layout
        )

        self.idle_rpm = self.create_input(
            input_layout,
            "دور آرام (RPM)",
            900
        )

        self.cutoff_rpm = self.create_input(
            input_layout,
            "دور موتور کاتاف (RPM)",
            7000
        )

        self.peak_power = self.create_input(
            input_layout,
            "اوج توان (HP)",
            110
        )

        self.peak_power_rpm = self.create_input(
            input_layout,
            "دور موتور اوج توان (RPM)",
            5500
        )

        self.peak_torque = self.create_input(
            input_layout,
            "اوج گشتاور (N·m)",
            170
        )

        self.peak_torque_rpm = self.create_input(
            input_layout,
            "دور موتور اوج گشتاور (RPM)",
            3000
        )

        self.displacement = self.create_input(
            input_layout,
            "حجم موتور (L)",
            2.0
        )

        self.boost = self.create_input(
            input_layout,
            "بوست توربو (PSI)",
            15
        )

        self.atmospheric = self.create_input(
            input_layout,
            "فشار هوا (PSI)",
            12.5
        )

        self.manifold_temp = self.create_input(
            input_layout,
            "دمای هوای منیفولد (°C)",
            50
        )

        self.ve = self.create_input(
            input_layout,
            "راندمان حجمی موتور VE (%)",
            90
        )

        self.table_size = self.create_combo(
            input_layout,
            "اندازه جدول",
            [
                "8 × 8",
                "16 × 16",
                "32 × 32",
                "16 × 32",
                "32 × 16",
                "16 × 8",
                "8 × 16",
                "32 × 8",
                "8 × 32",
            ],
            "16 × 16"
        )

        container_layout.addWidget(
            input_card
        )

        # ====================================================
        # GENERATE BUTTON
        # ====================================================

        generate = QPushButton(
            "⚡ GENERATE TURBO CALCULATION"
        )

        generate.setMinimumHeight(
            48
        )

        generate.setStyleSheet("""
            QPushButton {
                background-color: #151515;
                color: #ff1e1e;
                border: 1px solid #ff1e1e;
                border-radius: 8px;
                font-size: 14px;
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

        generate.clicked.connect(
            self.calculate
        )

        container_layout.addWidget(
            generate
        )

        # ====================================================
        # PRESSURE RATIO
        # ====================================================

        pr_card = SectionCard(
            "2. نسبت فشار توربو",
            "Pressure Ratio مقدار نسبت فشار مطلق خروجی کمپرسور به فشار مطلق ورودی آن است."
        )

        pr_layout = (
            pr_card.main_layout
        )

        self.pr_result = ResultCard()

        pr_layout.addWidget(
            self.pr_result
        )

        container_layout.addWidget(
            pr_card
        )

        # ====================================================
        # ACTUAL AIRFLOW
        # ====================================================

        airflow_card = SectionCard(
            "3. دبی جرمی پایه",
            "مقدار Airflow واقعی موتور بر حسب lb/min در دور اوج توان، فشار اتمسفر، بوست و VE واردشده."
        )

        airflow_layout = (
            airflow_card.main_layout
        )

        self.airflow_result = ResultCard()

        airflow_layout.addWidget(
            self.airflow_result
        )

        container_layout.addWidget(
            airflow_card
        )

        # ====================================================
        # CORRECTED AIRFLOW
        # ====================================================

        corrected_card = SectionCard(
            "4. Corrected Airflow",
            "دبی جرمی تصحیح‌شده برای شرایط استاندارد ورودی کمپرسور که برای مقایسه با Compressor Map استفاده می‌شود."
        )

        corrected_layout = (
            corrected_card.main_layout
        )

        self.corrected_result = ResultCard()

        corrected_layout.addWidget(
            self.corrected_result
        )

        container_layout.addWidget(
            corrected_card
        )

        # ====================================================
        # TABLE
        # ====================================================

        table_card = SectionCard(
            "5. جدول RPM / ATMOSPHERIC PSI / lb/min",
            "سطرها RPM هستند، ستون‌ها فشار اتمسفر هستند و هر خانه مقدار Actual Airflow را نشان می‌دهد. با حرکت روی خانه‌ها Pressure Ratio و Corrected Airflow نیز نمایش داده می‌شوند."
        )

        table_layout = (
            table_card.main_layout
        )

        self.table_widget = QWidget()

        self.table_layout = (
            QGridLayout(
                self.table_widget
            )
        )

        self.table_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.table_layout.setHorizontalSpacing(
            5
        )

        self.table_layout.setVerticalSpacing(
            5
        )

        table_layout.addWidget(
            self.table_widget
        )

        container_layout.addWidget(
            table_card
        )

        container_layout.addStretch()

        scroll.setWidget(
            container
        )

        main_layout = (
            QVBoxLayout(self)
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.addWidget(
            scroll
        )

    # --------------------------------------------------------
    # GET FLOAT
    # --------------------------------------------------------

    def get_float(
        self,
        widget
    ):

        text = (
            widget.text().strip()
        )

        if not text:

            raise ValueError(
                "یکی از ورودی‌ها خالی است."
            )

        return float(
            text.replace(
                ",",
                "."
            )
        )

    # --------------------------------------------------------
    # CLEAR TABLE
    # --------------------------------------------------------

    def clear_table(
        self
    ):

        while self.table_layout.count():

            item = (
                self.table_layout.takeAt(
                    0
                )
            )

            widget = (
                item.widget()
            )

            if widget:
                widget.deleteLater()

    # --------------------------------------------------------
    # CALCULATE
    # --------------------------------------------------------

    def calculate(
        self
    ):

        try:

            idle = self.get_float(
                self.idle_rpm
            )

            cutoff = self.get_float(
                self.cutoff_rpm
            )

            power = self.get_float(
                self.peak_power
            )

            power_rpm = self.get_float(
                self.peak_power_rpm
            )

            torque = self.get_float(
                self.peak_torque
            )

            torque_rpm = self.get_float(
                self.peak_torque_rpm
            )

            displacement = self.get_float(
                self.displacement
            )

            boost = self.get_float(
                self.boost
            )

            atmospheric = self.get_float(
                self.atmospheric
            )

            temperature = self.get_float(
                self.manifold_temp
            )

            ve = self.get_float(
                self.ve
            )

            table_size = (
                self.table_size.currentText()
            )

            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            if idle <= 0:

                raise ValueError(
                    "Idle RPM must be greater than zero."
                )

            if cutoff <= idle:

                raise ValueError(
                    "Cutoff RPM must be greater than idle RPM."
                )

            if power <= 0:

                raise ValueError(
                    "Peak power must be greater than zero."
                )

            if torque <= 0:

                raise ValueError(
                    "Peak torque must be greater than zero."
                )

            if (
                power_rpm < idle
                or power_rpm > cutoff
            ):

                raise ValueError(
                    "Peak power RPM must be inside the engine RPM range."
                )

            if (
                torque_rpm < idle
                or torque_rpm > cutoff
            ):

                raise ValueError(
                    "Peak torque RPM must be inside the engine RPM range."
                )

            # ------------------------------------------------
            # PRESSURE RATIO
            # ------------------------------------------------

            pr = calculate_pressure_ratio(
                boost,
                atmospheric
            )

            compressor_outlet_pressure = (
                atmospheric + boost
            )

            compressor_inlet_pressure = (
                atmospheric
            )

            # ------------------------------------------------
            # ACTUAL AIRFLOW
            # ------------------------------------------------

            peak_airflow = (
                calculate_airflow_lb_min(
                    rpm=power_rpm,
                    displacement_l=displacement,
                    atmospheric_psi=atmospheric,
                    boost_psi=boost,
                    manifold_temp_c=temperature,
                    ve_percent=ve,
                )
            )

            # ------------------------------------------------
            # CORRECTED AIRFLOW
            # ------------------------------------------------

            peak_corrected_airflow = (
                calculate_corrected_airflow_lb_min(
                    actual_airflow_lb_min=peak_airflow,
                    atmospheric_psi=atmospheric,
                    inlet_temp_c=temperature,
                )
            )

            # ------------------------------------------------
            # TURBO TARGET AIRFLOW
            # ------------------------------------------------

            turbo_target_airflow = (
                calculate_turbo_target_airflow_lb_min(
                    power
                )
            )

            # ------------------------------------------------
            # PR RESULT
            # ------------------------------------------------

            self.pr_result.add_result(
                "COMPRESSOR PRESSURE RATIO",
                f"{pr:.2f} : 1",
                (
                    f"P1 = {compressor_inlet_pressure:.2f} PSIA"
                    f"    |    "
                    f"P2 = {compressor_outlet_pressure:.2f} PSIA"
                )
            )

            # ------------------------------------------------
            # ACTUAL AIRFLOW RESULT
            # ------------------------------------------------

            self.airflow_result.add_result(
                "ACTUAL AIRFLOW",
                f"{peak_airflow:.2f} lb/min",
                (
                    f"{int(round(power_rpm)):,} RPM"
                    f"    |    "
                    f"VE = {ve:.1f}%"
                )
            )

            # ------------------------------------------------
            # CORRECTED AIRFLOW RESULT
            # ------------------------------------------------

            self.corrected_result.add_result(
                "CORRECTED AIRFLOW",
                f"{peak_corrected_airflow:.2f} lb/min",
                (
                    f"Standard = "
                    f"{STANDARD_PRESSURE_PSI:.3f} PSI"
                    f" / "
                    f"{STANDARD_TEMPERATURE_K:.2f} K"
                )
            )

            # ------------------------------------------------
            # GENERATE GRID
            # ------------------------------------------------

            (
                rpm_axis,
                pressure_axis,
                grid
            ) = calculate_turbo_grid(
                idle_rpm=idle,
                cutoff_rpm=cutoff,
                displacement_l=displacement,
                boost_psi=boost,
                atmospheric_psi=atmospheric,
                manifold_temp_c=temperature,
                ve_percent=ve,
                table_size=table_size,
            )

            # ------------------------------------------------
            # CLEAR OLD TABLE
            # ------------------------------------------------

            self.clear_table()

            # ------------------------------------------------
            # CORNER
            # ------------------------------------------------

            corner = QLabel(
                "RPM"
            )

            corner.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            corner.setStyleSheet("""
                QLabel {
                    background-color: #151515;
                    color: #ff1e1e;
                    border: 1px solid #333333;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
            """)

            self.table_layout.addWidget(
                corner,
                0,
                0
            )

            # ------------------------------------------------
            # PRESSURE HEADERS
            # ------------------------------------------------

            for col, pressure in enumerate(
                pressure_axis,
                start=1
            ):

                header = QLabel(
                    f"{pressure:.2f}\nPSI"
                )

                header.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                if abs(
                    pressure - atmospheric
                ) < 0.011:

                    header.setStyleSheet("""
                        QLabel {
                            background-color: #ff1e1e;
                            color: #000000;
                            border: 1px solid #ff1e1e;
                            border-radius: 6px;
                            padding: 6px;
                            font-weight: bold;
                        }
                    """)

                else:

                    header.setStyleSheet("""
                        QLabel {
                            background-color: #151515;
                            color: #ff1e1e;
                            border: 1px solid #333333;
                            border-radius: 6px;
                            padding: 6px;
                            font-weight: bold;
                        }
                    """)

                self.table_layout.addWidget(
                    header,
                    0,
                    col
                )

            # ------------------------------------------------
            # DATA
            # ------------------------------------------------

            for row_index, rpm in enumerate(
                rpm_axis,
                start=1
            ):

                rpm_label = QLabel(
                    f"{rpm:,}"
                )

                rpm_label.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                rpm_label.setStyleSheet("""
                    QLabel {
                        background-color: #151515;
                        color: #ff1e1e;
                        border: 1px solid #333333;
                        border-radius: 6px;
                        padding: 6px;
                        font-weight: bold;
                    }
                """)

                self.table_layout.addWidget(
                    rpm_label,
                    row_index,
                    0
                )

                row_data = grid[
                    row_index - 1
                ]

                for col_index, cell in enumerate(
                    row_data,
                    start=1
                ):

                    pressure = (
                        cell[
                            "atmospheric_psi"
                        ]
                    )

                    airflow = (
                        cell[
                            "airflow_lb_min"
                        ]
                    )

                    corrected_airflow = (
                        cell[
                            "corrected_airflow_lb_min"
                        ]
                    )

                    pressure_ratio = (
                        cell[
                            "pressure_ratio"
                        ]
                    )

                    if abs(
                        pressure - atmospheric
                    ) < 0.011:

                        cell_style = """
                            QLabel {
                                background-color: #241010;
                                color: #ff1e1e;
                                border: 1px solid #ff1e1e;
                                border-radius: 6px;
                                padding: 6px;
                                font-weight: bold;
                            }
                        """

                    else:

                        cell_style = """
                            QLabel {
                                background-color: #101010;
                                color: #dddddd;
                                border: 1px solid #242424;
                                border-radius: 6px;
                                padding: 6px;
                            }
                        """

                    # Main displayed value:
                    # ACTUAL AIRFLOW

                    airflow_label = QLabel(
                        f"{airflow:.2f}"
                    )

                    airflow_label.setToolTip(
                        (
                            f"RPM: {rpm:,}\n"
                            f"Atmospheric: "
                            f"{pressure:.2f} PSI\n"
                            f"Boost: "
                            f"{boost:.2f} PSI\n"
                            f"PR: "
                            f"{pressure_ratio:.3f}:1\n"
                            f"Actual Airflow: "
                            f"{airflow:.2f} lb/min\n"
                            f"Corrected Airflow: "
                            f"{corrected_airflow:.2f} lb/min\n"
                            f"Turbo Target Airflow: "
                            f"{turbo_target_airflow:.2f} lb/min"
                        )
                    )

                    airflow_label.setAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                    airflow_label.setStyleSheet(
                        cell_style
                    )

                    self.table_layout.addWidget(
                        airflow_label,
                        row_index,
                        col_index
                    )

        except ValueError as e:

            QMessageBox.warning(
                self,
                "Input Error",
                str(e)
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Calculation Error",
                f"خطا در محاسبه:\n{e}"
            )