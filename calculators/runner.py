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
    QGridLayout,
    QFrame,
    QMessageBox,
    QScrollArea,
)


DEFAULT_VE = 73.5
DEFAULT_AIR_TEMP_C = 20.0


# ============================================================
# CALCULATIONS
# ============================================================

def calculate_engine_displacement(
    bore_mm,
    stroke_mm,
    cylinders
):
    return (
        math.pi / 4
        * bore_mm ** 2
        * stroke_mm
        * cylinders
        / 1000
    )


def calculate_gasket_volume(
    gasket_diameter_mm,
    gasket_thickness_mm
):
    return (
        math.pi / 4
        * gasket_diameter_mm ** 2
        * gasket_thickness_mm
        / 1000
    )


def calculate_compression_ratio(
    displacement_cc,
    gasket_volume_cc,
    chamber_volume_cc,
    piston_volume_cc
):
    clearance_volume = (
        gasket_volume_cc
        + chamber_volume_cc
        + piston_volume_cc
    )

    if clearance_volume <= 0:
        raise ValueError(
            "Clearance volume must be greater than zero."
        )

    return (
        displacement_cc + clearance_volume
    ) / clearance_volume


def calculate_runner_diameter(
    displacement_cc,
    rpm,
    ve_percent
):
    displacement_l = displacement_cc / 1000
    ve = ve_percent / 100

    diameter_inches = math.sqrt(
        (rpm * displacement_l * ve) / 3330
    )

    return diameter_inches * 25.4


def calculate_speed_of_sound(
    temperature_c
):
    return 331.3 + (
        0.606 * temperature_c
    )


def calculate_runner_length(
    rpm,
    cam_duration_deg,
    harmonic,
    temperature_c
):
    if rpm <= 0:
        raise ValueError(
            "RPM must be greater than zero."
        )

    effective_closed_duration = (
        720
        - (cam_duration_deg - 20)
    )

    speed_of_sound = calculate_speed_of_sound(
        temperature_c
    )

    length_m = (
        speed_of_sound
        * effective_closed_duration
        / (12 * rpm * harmonic)
    )

    return length_m * 100


# ============================================================
# INFO BUTTON
# ============================================================

class InfoButton(QPushButton):

    def __init__(
        self,
        title,
        message,
        parent=None
    ):
        super().__init__(
            "i",
            parent
        )

        self.title = title
        self.message = message

        self.setFixedSize(
            27,
            27
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: #ff2b2b;
                border: 1px solid #3a3a3a;
                border-radius: 13px;
                font-size: 13px;
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

        self.clicked.connect(
            self.show_info
        )

    def show_info(self):

        QMessageBox.information(
            self,
            self.title,
            self.message
        )


# ============================================================
# RESULT CARD
# ============================================================

class ResultCard(QFrame):

    def __init__(
        self,
        title="RESULT",
        parent=None
    ):
        super().__init__(
            parent
        )

        self.setObjectName(
            "ResultCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            15,
            20,
            15
        )

        layout.setSpacing(
            5
        )

        title_label = QLabel(
            title
        )

        title_label.setAlignment(
            Qt.AlignCenter
        )

        title_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 11px;
                font-weight: bold;
            }
        """)

        self.value_label = QLabel(
            "--"
        )

        self.value_label.setAlignment(
            Qt.AlignCenter
        )

        self.value_label.setStyleSheet("""
            QLabel {
                color: #ff2b2b;
                font-size: 27px;
                font-weight: bold;
            }
        """)

        self.detail_label = QLabel(
            ""
        )

        self.detail_label.setAlignment(
            Qt.AlignCenter
        )

        self.detail_label.setWordWrap(
            True
        )

        self.detail_label.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 10px;
            }
        """)

        layout.addWidget(
            title_label
        )

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
        number,
        title,
        subtitle,
        parent=None
    ):
        super().__init__(
            parent
        )

        self.setObjectName(
            "SectionCard"
        )

        self.layout = QVBoxLayout(
            self
        )

        self.layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        self.layout.setSpacing(
            10
        )

        header = QHBoxLayout()

        title_label = QLabel(
            f"{number}. {title}"
        )

        title_label.setObjectName(
            "SectionTitle"
        )

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setObjectName(
            "SectionSubtitle"
        )

        header.addWidget(
            title_label
        )

        header.addStretch()

        header.addWidget(
            subtitle_label
        )

        self.layout.addLayout(
            header
        )


# ============================================================
# MAIN CALCULATOR
# ============================================================

class RunnerCalculator(QDialog):

    def __init__(
        self,
        parent=None
    ):
        super().__init__(
            parent
        )

        self.setWindowTitle(
            "ASLAN TUNER - Intake Runner"
        )

        self.setMinimumSize(
            720,
            650
        )

        self.resize(
            820,
            800
        )

        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.setStyleSheet("""
            QDialog {
                background-color: #0d0d0d;
                color: #ffffff;
            }

            QWidget#ScrollContent {
                background-color: #0d0d0d;
            }

            QLabel {
                color: #eeeeee;
            }

            QLineEdit {
                background-color: #171717;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 7px;
                padding: 9px 11px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #ff2b2b;
            }

            QPushButton#calculateButton {
                background-color: #d50000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#calculateButton:hover {
                background-color: #ff1f1f;
            }

            QPushButton#resetButton {
                background-color: #1b1b1b;
                color: #dddddd;
                border: 1px solid #383838;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#resetButton:hover {
                background-color: #252525;
                border: 1px solid #555555;
            }

            QFrame#SectionCard {
                background-color: #121212;
                border: 1px solid #292929;
                border-radius: 10px;
            }

            QFrame#ResultCard {
                background-color: #111111;
                border: 1px solid #3b1717;
                border-radius: 10px;
            }

            QLabel#SectionTitle {
                color: #ff2b2b;
                font-size: 15px;
                font-weight: bold;
            }

            QLabel#SectionSubtitle {
                color: #777777;
                font-size: 11px;
            }

            QScrollBar:vertical {
                background: #111111;
                width: 12px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 5px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background: #ff2b2b;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.build_ui()


    # ========================================================
    # INPUT ROW WITH INFO BUTTON
    # ========================================================

    def add_input(
        self,
        grid,
        row,
        label,
        info_title,
        info_message,
        default
    ):

        label_widget = QLabel(
            label
        )

        info = InfoButton(
            info_title,
            info_message
        )

        field = QLineEdit()

        field.setText(
            str(default)
        )

        grid.addWidget(
            label_widget,
            row,
            0
        )

        grid.addWidget(
            info,
            row,
            1
        )

        grid.addWidget(
            field,
            row,
            2
        )

        return field


    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        content = QWidget()

        content.setObjectName(
            "ScrollContent"
        )

        main_layout = QVBoxLayout(
            content
        )

        main_layout.setContentsMargins(
            25,
            20,
            25,
            25
        )

        main_layout.setSpacing(
            14
        )

        scroll.setWidget(
            content
        )

        outer_layout.addWidget(
            scroll
        )


        # ====================================================
        # HEADER
        # ====================================================

        title = QLabel(
            "INTAKE RUNNER CALCULATOR"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet("""
            QLabel {
                color: #ff2b2b;
                font-size: 25px;
                font-weight: bold;
            }
        """)

        subtitle = QLabel(
            "ASLAN TUNER"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            subtitle
        )


        # ====================================================
        # 01 ENGINE DISPLACEMENT
        # ====================================================

        card1 = SectionCard(
            "01",
            "ENGINE DISPLACEMENT",
            "حجم موتور"
        )

        grid1 = QGridLayout()

        self.bore_input = self.add_input(
            grid1,
            0,
            "Bore Diameter (mm)",
            "Bore Diameter",
            "قطر سیلندر را بر حسب میلی‌متر وارد کنید.",
            78.5
        )

        self.stroke_input = self.add_input(
            grid1,
            1,
            "Piston Stroke (mm)",
            "Piston Stroke",
            "کورس پیستون را بر حسب میلی‌متر وارد کنید.",
            82
        )

        self.cylinders_input = self.add_input(
            grid1,
            2,
            "Number of Cylinders",
            "Cylinders",
            "تعداد سیلندرهای موتور را وارد کنید.",
            4
        )

        card1.layout.addLayout(
            grid1
        )

        button1 = QPushButton(
            "GENERATE"
        )

        button1.setObjectName(
            "calculateButton"
        )

        button1.clicked.connect(
            self.calculate_displacement
        )

        card1.layout.addWidget(
            button1
        )

        self.displacement_result = ResultCard(
            "ENGINE DISPLACEMENT"
        )

        card1.layout.addWidget(
            self.displacement_result
        )

        main_layout.addWidget(
            card1
        )


        # ====================================================
        # 02 COMPRESSION RATIO
        # ====================================================

        card2 = SectionCard(
            "02",
            "COMPRESSION RATIO",
            "نسبت تراکم"
        )

        grid2 = QGridLayout()

        self.cr_bore_input = self.add_input(
            grid2,
            0,
            "Bore Diameter (mm)",
            "Bore Diameter",
            "قطر سیلندر.",
            78.5
        )

        self.cr_stroke_input = self.add_input(
            grid2,
            1,
            "Piston Stroke (mm)",
            "Piston Stroke",
            "کورس پیستون.",
            82
        )

        self.gasket_diameter_input = self.add_input(
            grid2,
            2,
            "Gasket Diameter (mm)",
            "Gasket Diameter",
            "قطر داخلی واشر سرسیلندر.",
            80
        )

        self.gasket_thickness_input = self.add_input(
            grid2,
            3,
            "Gasket Thickness (mm)",
            "Gasket Thickness",
            "ضخامت واشر سرسیلندر.",
            0.65
        )

        self.chamber_input = self.add_input(
            grid2,
            4,
            "Combustion Chamber Volume (cc)",
            "Chamber Volume",
            "حجم محفظه احتراق سرسیلندر.",
            37
        )

        self.piston_volume_input = self.add_input(
            grid2,
            5,
            "Piston Dome / Dish Volume (cc)",
            "Piston Volume",
            "حجم تاج یا کاسه پیستون. Dome مثبت و Dish باید مطابق جهت حجم واقعی وارد شود.",
            0
        )

        card2.layout.addLayout(
            grid2
        )

        button2 = QPushButton(
            "GENERATE"
        )

        button2.setObjectName(
            "calculateButton"
        )

        button2.clicked.connect(
            self.calculate_compression
        )

        card2.layout.addWidget(
            button2
        )

        self.cr_result = ResultCard(
            "COMPRESSION RATIO"
        )

        card2.layout.addWidget(
            self.cr_result
        )

        main_layout.addWidget(
            card2
        )


        # ====================================================
        # 03 RUNNER DIAMETER
        # ====================================================

        card3 = SectionCard(
            "03",
            "RUNNER DIAMETER",
            "قطر رانر"
        )

        grid3 = QGridLayout()

        self.runner_displacement_input = self.add_input(
            grid3,
            0,
            "Engine Displacement (cc)",
            "Engine Displacement",
            "حجم موتور را وارد کنید یا از نتیجه بخش اول استفاده کنید.",
            1587.46
        )

        self.runner_cylinders_input = self.add_input(
            grid3,
            1,
            "Number of Cylinders",
            "Cylinders",
            "تعداد سیلندر.",
            4
        )

        self.runner_rpm_input = self.add_input(
            grid3,
            2,
            "Target RPM",
            "Target RPM",
            "دور موتوری که می‌خواهید رانر برای آن طراحی شود.",
            6000
        )

        self.ve_input = self.add_input(
            grid3,
            3,
            "Design VE (%)",
            "Design VE",
            "VE هدف در محدوده دور طراحی.",
            DEFAULT_VE
        )

        card3.layout.addLayout(
            grid3
        )

        button3 = QPushButton(
            "GENERATE"
        )

        button3.setObjectName(
            "calculateButton"
        )

        button3.clicked.connect(
            self.calculate_runner_diameter_only
        )

        card3.layout.addWidget(
            button3
        )

        self.diameter_result = ResultCard(
            "RUNNER DIAMETER"
        )

        card3.layout.addWidget(
            self.diameter_result
        )

        main_layout.addWidget(
            card3
        )


        # ====================================================
        # 04 RUNNER LENGTH
        # ====================================================

        card4 = SectionCard(
            "04",
            "RUNNER LENGTH",
            "طول رانر"
        )

        grid4 = QGridLayout()

        self.length_rpm_input = self.add_input(
            grid4,
            0,
            "Target RPM",
            "Target RPM",
            "دور موتور هدف.",
            6000
        )

        self.runner_diameter_input = self.add_input(
            grid4,
            1,
            "Runner Diameter (cm)",
            "Runner Diameter",
            "قطر رانر محاسبه‌شده در بخش سوم.",
            3.68
        )

        self.cam_duration_input = self.add_input(
            grid4,
            2,
            "Camshaft Duration (°)",
            "Cam Duration",
            "Duration میل‌سوپاپ را بر حسب درجه وارد کنید.",
            243
        )

        self.air_temp_input = self.add_input(
            grid4,
            3,
            "Intake Air Temperature (°C)",
            "Air Temperature",
            "دمای هوای ورودی.",
            DEFAULT_AIR_TEMP_C
        )

        card4.layout.addLayout(
            grid4
        )

        button4 = QPushButton(
            "GENERATE"
        )

        button4.setObjectName(
            "calculateButton"
        )

        button4.clicked.connect(
            self.calculate_runner_length_only
        )

        card4.layout.addWidget(
            button4
        )

        results_row = QHBoxLayout()

        self.length1_result = ResultCard(
            "PRIMARY/URBAN"
        )

        self.length2_result = ResultCard(
            "SPORT"
        )

        self.length3_result = ResultCard(
            "SUPER SPORT"
        )

        results_row.addWidget(
            self.length1_result
        )

        results_row.addWidget(
            self.length2_result
        )

        results_row.addWidget(
            self.length3_result
        )

        card4.layout.addLayout(
            results_row
        )

        main_layout.addWidget(
            card4
        )


        # ====================================================
        # RESET
        # ====================================================

        reset_button = QPushButton(
            "RESET ALL"
        )

        reset_button.setObjectName(
            "resetButton"
        )

        reset_button.clicked.connect(
            self.reset
        )

        main_layout.addWidget(
            reset_button
        )


        disclaimer = QLabel(
            "⚠ مقادیر این ابزار برای طراحی اولیه هستند و برای انتخاب نهایی "
            "رانر باید هندسه پورت، سوپاپ، کام، پلنیوم و VE واقعی موتور نیز بررسی شود."
        )

        disclaimer.setAlignment(
            Qt.AlignCenter
        )

        disclaimer.setWordWrap(
            True
        )

        disclaimer.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 10px;
                padding: 5px;
            }
        """)

        main_layout.addWidget(
            disclaimer
        )


    # ========================================================
    # 01 - DISPLACEMENT
    # ========================================================

    def calculate_displacement(self):

        try:

            bore = float(
                self.bore_input.text()
            )

            stroke = float(
                self.stroke_input.text()
            )

            cylinders = int(
                float(
                    self.cylinders_input.text()
                )
            )

            if bore <= 0 or stroke <= 0 or cylinders <= 0:
                raise ValueError

            displacement = calculate_engine_displacement(
                bore,
                stroke,
                cylinders
            )

            self.displacement_result.value_label.setText(
                f"{displacement:,.2f} cm³"
            )

            self.displacement_result.detail_label.setText(
                f"{bore:g} × {stroke:g} mm × {cylinders} cylinders"
            )

            self.runner_displacement_input.setText(
                f"{displacement:.2f}"
            )

            self.runner_cylinders_input.setText(
                str(cylinders)
            )

            self.cr_bore_input.setText(
                f"{bore:g}"
            )

            self.cr_stroke_input.setText(
                f"{stroke:g}"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "مقادیر حجم موتور را به صورت عدد معتبر وارد کنید."
            )


    # ========================================================
    # 02 - COMPRESSION
    # ========================================================

    def calculate_compression(self):

        try:

            bore = float(
                self.cr_bore_input.text()
            )

            stroke = float(
                self.cr_stroke_input.text()
            )

            gasket_diameter = float(
                self.gasket_diameter_input.text()
            )

            gasket_thickness = float(
                self.gasket_thickness_input.text()
            )

            chamber = float(
                self.chamber_input.text()
            )

            piston_volume = float(
                self.piston_volume_input.text()
            )

            if (
                bore <= 0
                or stroke <= 0
                or gasket_diameter <= 0
                or gasket_thickness < 0
                or chamber <= 0
            ):
                raise ValueError

            # ==================================================
            # IMPORTANT:
            # Compression Ratio is calculated PER CYLINDER.
            #
            # Therefore cylinder count is NOT used here.
            # ==================================================

            cylinder_displacement = (
                math.pi / 4
                * bore ** 2
                * stroke
                / 1000
            )

            gasket_volume = calculate_gasket_volume(
                gasket_diameter,
                gasket_thickness
            )

            cr = calculate_compression_ratio(
                cylinder_displacement,
                gasket_volume,
                chamber,
                piston_volume
            )

            clearance_volume = (
                gasket_volume
                + chamber
                + piston_volume
            )

            self.cr_result.value_label.setText(
                f"CR = {cr:.2f}:1"
            )

            self.cr_result.detail_label.setText(
                f"Clearance volume = "
                f"{clearance_volume:.3f} cc"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "مقادیر نسبت تراکم را به صورت عدد معتبر وارد کنید."
            )


    # ========================================================
    # 03 - RUNNER DIAMETER
    # ========================================================

    def calculate_runner_diameter_only(self):

        try:

            displacement = float(
                self.runner_displacement_input.text()
            )

            rpm = float(
                self.runner_rpm_input.text()
            )

            ve = float(
                self.ve_input.text()
            )

            if displacement <= 0 or rpm <= 0 or ve <= 0:
                raise ValueError

            diameter_mm = calculate_runner_diameter(
                displacement,
                rpm,
                ve
            )

            diameter_cm = (
                diameter_mm / 10
            )

            self.diameter_result.value_label.setText(
                f"{diameter_cm:.2f} cm"
            )

            self.diameter_result.detail_label.setText(
                f"{diameter_mm:.1f} mm | VE = {ve:.1f}%"
            )

            self.runner_diameter_input.setText(
                f"{diameter_cm:.2f}"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "مقادیر قطر رانر را به صورت عدد معتبر وارد کنید."
            )


    # ========================================================
    # 04 - RUNNER LENGTH
    # ========================================================

    def calculate_runner_length_only(self):

        try:

            rpm = float(
                self.length_rpm_input.text()
            )

            cam_duration = float(
                self.cam_duration_input.text()
            )

            air_temperature = float(
                self.air_temp_input.text()
            )

            length1 = calculate_runner_length(
                rpm,
                cam_duration,
                4,
                air_temperature
            )

            length2 = calculate_runner_length(
                rpm,
                cam_duration,
                8,
                air_temperature
            )

            length3 = calculate_runner_length(
                rpm,
                cam_duration,
                12,
                air_temperature
            )

            self.length1_result.value_label.setText(
                f"{length1:.2f} cm"
            )

            self.length2_result.value_label.setText(
                f"{length2:.2f} cm"
            )

            self.length3_result.value_label.setText(
                f"{length3:.2f} cm"
            )

            self.length1_result.detail_label.setText(
                "اولیه/شهری"
            )

            self.length2_result.detail_label.setText(
                "اسپرت"
            )

            self.length3_result.detail_label.setText(
                "سوپر اسپرت"
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Invalid Input",
                "مقادیر طول رانر را به صورت عدد معتبر وارد کنید."
            )


    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.bore_input.setText(
            "78.5"
        )

        self.stroke_input.setText(
            "82"
        )

        self.cylinders_input.setText(
            "4"
        )

        self.cr_bore_input.setText(
            "78.5"
        )

        self.cr_stroke_input.setText(
            "82"
        )

        self.gasket_diameter_input.setText(
            "80"
        )

        self.gasket_thickness_input.setText(
            "0.65"
        )

        self.chamber_input.setText(
            "37"
        )

        self.piston_volume_input.setText(
            "0"
        )

        self.runner_displacement_input.setText(
            "1587.46"
        )

        self.runner_cylinders_input.setText(
            "4"
        )

        self.runner_rpm_input.setText(
            "6000"
        )

        self.ve_input.setText(
            str(DEFAULT_VE)
        )

        self.length_rpm_input.setText(
            "6000"
        )

        self.runner_diameter_input.setText(
            "3.68"
        )

        self.cam_duration_input.setText(
            "243"
        )

        self.air_temp_input.setText(
            str(DEFAULT_AIR_TEMP_C)
        )

        self.displacement_result.value_label.setText(
            "--"
        )

        self.displacement_result.detail_label.setText(
            ""
        )

        self.cr_result.value_label.setText(
            "--"
        )

        self.cr_result.detail_label.setText(
            ""
        )

        self.diameter_result.value_label.setText(
            "--"
        )

        self.diameter_result.detail_label.setText(
            ""
        )

        self.length1_result.value_label.setText(
            "--"
        )

        self.length2_result.value_label.setText(
            "--"
        )

        self.length3_result.value_label.setText(
            "--"
        )