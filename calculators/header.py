from math import sqrt, isfinite

from ui.topbar import ASLANTopBar

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# ASLAN TUNING — HEADER ENGINEERING CALCULATOR
#
# Bell-style exhaust tuning relations:
#
#   P(in) = 850 * (180 + EVO[BBDC]) / RPM - 3
#
#   IDP(in) =
#       sqrt(cc_per_cyl / ((P + 3) * 25)) * 2.1
#
#   IDS(in) =
#       sqrt(IDP^2 * 2) * 0.93
#
# 4-2-1 starting point:
#
#   P = P1 + P2
#   P1 = 15 in
#   P2 = P - P1
#
# IMPORTANT:
# The entered pipe diameter is treated as an existing/selected
# primary ID and is compared with the calculated ID.
#
# It is NOT inserted into the tuned-length equation.
# ============================================================


APP_RED = "#e00000"
APP_DARK = "#121212"
APP_PANEL = "#1b1b1b"
APP_PANEL_2 = "#202020"
APP_TEXT = "#f2f2f2"
APP_MUTED = "#a6a6a6"
APP_BORDER = "#343434"
APP_GREEN = "#6fdc8c"
APP_ORANGE = "#ffb454"


# ============================================================
# ENGINE CONFIGURATIONS
# ============================================================

ENGINE_CONFIGS = [
    ("Inline-3 / سه خطی", "I3", 3),
    ("Inline-4 / چهار خطی", "I4", 4),
    ("Inline-5 / پنج خطی", "I5", 5),
    ("Inline-6 / شش خطی", "I6", 6),
    ("Inline-8 / هشت خطی", "I8", 8),
    ("Inline-10 / ده خطی", "I10", 10),
    ("Inline-12 / دوازده خطی", "I12", 12),

    ("V6", "V6", 6),
    ("V8", "V8", 8),
    ("V10", "V10", 10),
    ("V12", "V12", 12),
]


# ============================================================
# INFO BUTTON
# ============================================================

class InfoButton(QPushButton):

    def __init__(self, text):
        super().__init__("ⓘ")

        self.setToolTip(text)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet(
            f"""
            QPushButton {{
                background:#171717;
                border:1px solid {APP_RED};
                color:#ffffff;
                border-radius:14px;
                font-size:15px;
                font-weight:700;
            }}

            QPushButton:hover {{
                background:{APP_RED};
            }}
            """
        )


# ============================================================
# RESULT CARD
# ============================================================

class ResultCard(QFrame):

    def __init__(self, title, value="—", subtitle=""):
        super().__init__()

        self.setObjectName("ResultCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)

        self.title = QLabel(title)
        self.title.setStyleSheet(
            f"""
            color:{APP_MUTED};
            font-size:12px;
            font-weight:600;
            """
        )

        self.value = QLabel(value)
        self.value.setStyleSheet(
            """
            color:#ffffff;
            font-size:24px;
            font-weight:800;
            """
        )
        self.value.setWordWrap(True)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setStyleSheet(
            f"""
            color:{APP_MUTED};
            font-size:11px;
            """
        )
        self.subtitle.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.subtitle)

    def set_value(self, value, subtitle=None):
        self.value.setText(value)

        if subtitle is not None:
            self.subtitle.setText(subtitle)


# ============================================================
# HEADER CALCULATOR
# ============================================================

class HeaderCalculator(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "ASLAN TUNING • Header Engineering"
        )

        self.setMinimumSize(980, 720)
        self.resize(1120, 820)

        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self._build_ui()
        self._apply_style()
        self._set_defaults()
        self._update_config_warning()

    # ========================================================
    # MATH CORE
    # ========================================================

    @staticmethod
    def tuned_length_in(rpm, evo_bbdc):
        """
        Bell-style tuned exhaust length.

        P(in) =
            850 * (180 + EVO) / RPM - 3
        """

        return (
            850.0
            * (180.0 + evo_bbdc)
            / rpm
        ) - 3.0

    @staticmethod
    def primary_id_in(cyl_cc, tuned_length_in):
        """
        Bell-style primary inside diameter.
        """

        effective_length = max(
            tuned_length_in,
            15.0
        )

        return sqrt(
            cyl_cc
            / (
                (effective_length + 3.0)
                * 25.0
            )
        ) * 2.1

    @staticmethod
    def secondary_id_in(primary_id_in):
        """
        Bell-style 4-2-1 secondary ID.
        """

        return sqrt(
            (primary_id_in ** 2) * 2.0
        ) * 0.93

    @staticmethod
    def inch_to_mm(value):
        return value * 25.4

    @staticmethod
    def inch_to_cm(value):
        return value * 2.54

    @staticmethod
    def cm_to_in(value):
        return value / 2.54

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    def _read_float(
        self,
        widget,
        name,
        minimum,
        maximum,
    ):

        text = (
            widget.text()
            .strip()
            .replace(",", ".")
        )

        if not text:
            raise ValueError(
                f"مقدار «{name}» وارد نشده است."
            )

        try:
            value = float(text)
        except ValueError:
            raise ValueError(
                f"مقدار «{name}» معتبر نیست."
            )

        if (
            not isfinite(value)
            or value < minimum
            or value > maximum
        ):
            raise ValueError(
                f"مقدار «{name}» باید بین "
                f"{minimum} و {maximum} باشد."
            )

        return value

    # ========================================================
    # ENGINE CONFIG READER
    # ========================================================

    def _read_config(self):

        data = self.config_combo.currentData()

        if (
            not isinstance(data, tuple)
            or len(data) != 2
        ):
            raise ValueError(
                "آرایش موتور معتبر نیست."
            )

        config_code = str(data[0])

        try:
            cylinders = int(data[1])
        except (TypeError, ValueError):
            raise ValueError(
                "تعداد سیلندر آرایش انتخاب‌شده معتبر نیست."
            )

        return config_code, cylinders

    # ========================================================
    # MAIN CALCULATION
    # ========================================================

    def _calculate(self):

        try:

            pipe_d_cm = self._read_float(
                self.pipe_diameter,
                "قطر لوله",
                1.0,
                20.0,
            )

            displacement = self._read_float(
                self.displacement,
                "حجم موتور",
                50.0,
                30000.0,
            )

            rpm = self._read_float(
                self.rpm,
                "دور موتور",
                800.0,
                25000.0,
            )

            evo = self._read_float(
                self.evo,
                "EVO",
                20.0,
                120.0,
            )

            port_cm = self._read_float(
                self.port_length,
                "طول پورت",
                0.0,
                100.0,
            )

            config_code, cylinders = self._read_config()

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "ورودی نامعتبر",
                str(exc),
            )

            return

        header_type = self.header_type.currentData()

        # ====================================================
        # CYLINDER DISPLACEMENT
        # ====================================================

        cyl_cc = displacement / cylinders

        # ====================================================
        # TUNED LENGTH
        # ====================================================

        raw_total_in = self.tuned_length_in(
            rpm,
            evo,
        )

        design_total_in = max(
            raw_total_in,
            15.0,
        )

        # ====================================================
        # PRIMARY DIAMETER
        # ====================================================

        primary_id = self.primary_id_in(
            cyl_cc,
            raw_total_in,
        )

        # ====================================================
        # SECONDARY DIAMETER
        # ====================================================

        secondary_id = self.secondary_id_in(
            primary_id
        )

        # ====================================================
        # USER DIAMETER
        # ====================================================

        entered_id_in = self.cm_to_in(
            pipe_d_cm
        )

        if primary_id > 0:

            diameter_delta_pct = (
                (
                    entered_id_in
                    - primary_id
                )
                / primary_id
            ) * 100.0

        else:

            diameter_delta_pct = 0.0

        # ====================================================
        # PORT COMPENSATION
        # ====================================================

        port_in = self.cm_to_in(
            port_cm
        )

        buildable_total_in = max(
            design_total_in - port_in,
            0.0,
        )

        # ====================================================
        # HEADER SPLIT
        # ====================================================

        if header_type == "4-1":

            primary_section_in = (
                buildable_total_in
            )

            secondary_section_in = 0.0

            final_desc = (
                "4-1 • تمام طول تیون‌شده در Primary"
            )

        else:

            primary_section_in = min(
                15.0,
                buildable_total_in,
            )

            secondary_section_in = max(
                buildable_total_in - 15.0,
                0.0,
            )

            final_desc = (
                "4-2-1 • Primary + Secondary"
            )

        # ====================================================
        # RESULT CARDS
        # ====================================================

        self.result_type.set_value(
            header_type,
            final_desc,
        )

        self.result_cyl.set_value(
            f"{cyl_cc:,.1f} cc",
            (
                f"حجم هر سیلندر • "
                f"{cylinders} سیلندر"
            ),
        )

        self.result_total.set_value(
            f"{self.inch_to_mm(design_total_in):,.0f} mm",
            (
                f"{design_total_in:.2f} in • "
                f"مرجع موج از پشت سوپاپ دود"
            ),
        )

        self.result_primary.set_value(
            f"{self.inch_to_mm(primary_section_in):,.0f} mm",
            (
                f"{primary_section_in:.2f} in • "
                f"طول اجرایی Primary"
            ),
        )

        self.result_secondary.set_value(
            f"{self.inch_to_mm(secondary_section_in):,.0f} mm",
            (
                f"{secondary_section_in:.2f} in • "
                f"طول اجرایی Secondary"
            ),
        )

        self.result_primary_d.set_value(
            f"{self.inch_to_mm(primary_id):.1f} mm",
            (
                f"{primary_id:.3f} in ID • "
                f"قطر داخلی پیشنهادی Primary"
            ),
        )

        self.result_secondary_d.set_value(
            f"{self.inch_to_mm(secondary_id):.1f} mm",
            (
                f"{secondary_id:.3f} in ID • "
                f"قطر داخلی پیشنهادی Secondary"
            ),
        )

        # ====================================================
        # DIAMETER CHECK
        # ====================================================

        if abs(diameter_delta_pct) <= 5:

            match = (
                "قطر واردشده بسیار نزدیک "
                "به مقدار محاسباتی است."
            )

        elif diameter_delta_pct < 0:

            match = (
                f"قطر واردشده حدود "
                f"{abs(diameter_delta_pct):.1f}% "
                f"کوچک‌تر از مقدار محاسباتی است."
            )

        else:

            match = (
                f"قطر واردشده حدود "
                f"{diameter_delta_pct:.1f}% "
                f"بزرگ‌تر از مقدار محاسباتی است."
            )

        self.diameter_check.setText(
            f"<b>مقایسه قطر:</b> "
            f"{pipe_d_cm:.2f} cm ID واردشده  →  "
            f"{self.inch_to_cm(primary_id):.2f} cm "
            f"ID پیشنهادی"
            f"<br>{match}"
        )

        # ====================================================
        # ENGINEERING WARNINGS
        # ====================================================

        warnings = []

        if raw_total_in < 15.0:

            warnings.append(
                "طول خام از 15 اینچ کمتر شد؛ "
                "مقدار عملی با کف 15 اینچ محدود شده است."
            )

        if (
            header_type == "4-2-1"
            and secondary_section_in < 1.0
        ):

            warnings.append(
                "برای 4-2-1 طول Secondary بسیار کوتاه است؛ "
                "RPM/EVO یا بسته‌بندی واقعی را بررسی کنید."
            )

        if (
            header_type == "4-2-1"
            and cylinders % 2 != 0
        ):

            warnings.append(
                "آرایش 4-2-1 کلاسیک برای تعداد سیلندر فرد "
                "جفت‌سازی کامل ندارد؛ خروجی ابعادی است و "
                "Pairing واقعی باید با firing order طراحی شود."
            )

        if config_code.startswith("V"):

            bank = cylinders // 2

            if bank != 4:

                warnings.append(
                    f"برای {config_code} هر بانک "
                    f"{bank} سیلندر دارد؛ "
                    f"4-1/4-2-1 در این حالت "
                    f"به‌عنوان مدل مرجع سایزبندی تفسیر شده است."
                )

        if port_cm > 0:

            if port_in >= design_total_in:

                warnings.append(
                    "طول پورت واردشده تقریباً برابر "
                    "یا بیشتر از طول تیون‌شده است؛ "
                    "طول اجرایی غیرواقعی می‌شود."
                )

        # ====================================================
        # SHOW WARNINGS
        # ====================================================

        if warnings:

            self.warning_box.setText(
                "⚠ " + "\n⚠ ".join(warnings)
            )

            self.warning_box.setVisible(True)

        else:

            self.warning_box.clear()
            self.warning_box.setVisible(False)

        # ====================================================
        # FORMULA TRACE
        # ====================================================

        self.formula_box.setText(
            f"P = 850 × (180 + EVO) / RPM − 3\n"
            f"= 850 × (180 + {evo:.1f}) / "
            f"{rpm:.0f} − 3\n"
            f"= {raw_total_in:.2f} in\n\n"

            f"ID₁ = √(cc/cyl / ((P + 3) × 25)) × 2.1\n"
            f"= {primary_id:.3f} in\n\n"

            f"ID₂ = √(ID₁² × 2) × 0.93\n"
            f"= {secondary_id:.3f} in"
        )

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.setSpacing(0)

        # ====================================================
        # ASLAN TOP BAR
        # ====================================================

        self.title_bar = ASLANTopBar(
            self,
            "HEADER ENGINEERING",
        )

        root.addWidget(
            self.title_bar,
        )

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        root.addWidget(
            scroll,
            1,
        )

        page = QWidget()

        page.setObjectName(
            "HeaderPage"
        )

        scroll.setWidget(page)

        page_layout = QVBoxLayout(page)

        page_layout.setContentsMargins(
            22,
            20,
            22,
            22,
        )

        page_layout.setSpacing(16)

        # ====================================================
        # INTRO
        # ====================================================

        intro = QFrame()

        intro.setObjectName(
            "Intro"
        )

        intro_l = QVBoxLayout(intro)

        intro_l.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        intro_l.setSpacing(6)

        h = QLabel(
            "محاسبه طول و قطر هدرز • 4-1 / 4-2-1"
        )

        h.setStyleSheet(
            """
            color:#ffffff;
            font-size:19px;
            font-weight:800;
            """
        )

        p = QLabel(
            "مدل ASLAN از فرمول تیونینگ موج اگزوز "
            "استفاده می‌کند؛ قطر واردشده برای بررسی "
            "تناسب لوله است و طول بر پایه RPM + EVO "
            "محاسبه می‌شود. EVO در بخش پیشرفته قابل اصلاح است."
        )

        p.setWordWrap(True)

        p.setStyleSheet(
            f"""
            color:{APP_MUTED};
            font-size:12px;
            """
        )

        intro_l.addWidget(h)
        intro_l.addWidget(p)

        page_layout.addWidget(intro)

        # ====================================================
        # INPUT PANEL
        # ====================================================

        inputs = QFrame()

        inputs.setObjectName(
            "Panel"
        )

        grid = QGridLayout(inputs)

        grid.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(13)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(4, 1)

        row = 0

        # ====================================================
        # HEADER TYPE
        # ====================================================

        self.header_type = self._combo(
            [
                ("4-1", "4-1"),
                ("4-2-1", "4-2-1"),
            ]
        )

        grid.addWidget(
            self._label("نوع هدرز"),
            row,
            0,
        )

        grid.addWidget(
            self.header_type,
            row,
            1,
        )

        grid.addWidget(
            InfoButton(
                "4-1 همه Primaryها را در یک Collector "
                "جمع می‌کند؛ 4-2-1 ابتدا دو جفت را "
                "جمع و سپس به یک خروجی می‌رساند."
            ),
            row,
            2,
        )

        # ====================================================
        # ENGINE CONFIGURATION
        # ====================================================

        self.config_combo = self._combo(
            [
                (
                    name,
                    (code, cylinders),
                )
                for name, code, cylinders in ENGINE_CONFIGS
            ]
        )

        grid.addWidget(
            self._label("آرایش موتور"),
            row,
            3,
        )

        grid.addWidget(
            self.config_combo,
            row,
            4,
        )

        grid.addWidget(
            InfoButton(
                "تعداد سیلندر از آرایش انتخابی "
                "خوانده می‌شود. برای V موتورها، "
                "طراحی هر بانک باید جداگانه بررسی شود."
            ),
            row,
            5,
        )

        row += 1

        # ====================================================
        # PIPE DIAMETER
        # ====================================================

        self.pipe_diameter = self._line(
            "4.20"
        )

        grid.addWidget(
            self._label(
                "قطر داخلی لوله اولیه (cm)"
            ),
            row,
            0,
        )

        grid.addWidget(
            self.pipe_diameter,
            row,
            1,
        )

        grid.addWidget(
            InfoButton(
                "این مقدار برای مقایسه با قطر "
                "پیشنهادی استفاده می‌شود. در فرمول "
                "طول به‌صورت مستقیم وارد نمی‌شود."
            ),
            row,
            2,
        )

        # ====================================================
        # DISPLACEMENT
        # ====================================================

        self.displacement = self._line(
            "1600"
        )

        grid.addWidget(
            self._label(
                "حجم موتور (cc)"
            ),
            row,
            3,
        )

        grid.addWidget(
            self.displacement,
            row,
            4,
        )

        grid.addWidget(
            InfoButton(
                "کل حجم موتور. حجم هر سیلندر "
                "از تقسیم حجم کل بر تعداد سیلندرها "
                "محاسبه می‌شود."
            ),
            row,
            5,
        )

        row += 1

        # ====================================================
        # TARGET RPM
        # ====================================================

        self.rpm = self._line(
            "5500"
        )

        grid.addWidget(
            self._label(
                "دور هدف (RPM)"
            ),
            row,
            0,
        )

        grid.addWidget(
            self.rpm,
            row,
            1,
        )

        grid.addWidget(
            InfoButton(
                "RPM نقطه‌ای است که می‌خواهید "
                "هدرز در آن بیشترین اثر تیونینگ موجی "
                "را داشته باشد."
            ),
            row,
            2,
        )

        # ====================================================
        # CYLINDER DISPLAY
        # ====================================================

        self.cylinder_display = self._line(
            "4",
            readonly=True,
        )

        grid.addWidget(
            self._label(
                "تعداد سیلندر"
            ),
            row,
            3,
        )

        grid.addWidget(
            self.cylinder_display,
            row,
            4,
        )

        grid.addWidget(
            InfoButton(
                "به‌صورت خودکار از آرایش موتور "
                "خوانده می‌شود و قابل ویرایش مستقیم نیست."
            ),
            row,
            5,
        )

        row += 1

        # ====================================================
        # ADVANCED BUTTON
        # ====================================================

        self.advanced_toggle = QPushButton(
            "⚙ بخش پیشرفته"
        )

        self.advanced_toggle.setCheckable(True)

        self.advanced_toggle.clicked.connect(
            self._toggle_advanced
        )

        grid.addWidget(
            self.advanced_toggle,
            row,
            0,
            1,
            2,
        )

        # ====================================================
        # ADVANCED PANEL
        # ====================================================

        self.advanced_box = QFrame()

        adv_grid = QGridLayout(
            self.advanced_box
        )

        adv_grid.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        adv_grid.setHorizontalSpacing(14)
        adv_grid.setVerticalSpacing(12)

        adv_grid.setColumnStretch(1, 1)
        adv_grid.setColumnStretch(4, 1)

        # ====================================================
        # EVO
        # ====================================================

        self.evo = self._line(
            "60"
        )

        adv_grid.addWidget(
            self._label(
                "EVO (درجه قبل از BDC)"
            ),
            0,
            0,
        )

        adv_grid.addWidget(
            self.evo,
            0,
            1,
        )

        adv_grid.addWidget(
            InfoButton(
                "EVO یعنی Exhaust Valve Opening. "
                "این مقدار نشان می‌دهد سوپاپ دود "
                "چند درجه قبل از BDC باز می‌شود. "
                "برای نتیجه واقعی‌تر از Cam Card استفاده شود."
            ),
            0,
            2,
        )

        # ====================================================
        # PORT LENGTH
        # ====================================================

        self.port_length = self._line(
            "0"
        )

        adv_grid.addWidget(
            self._label(
                "طول پورت خروجی (cm)"
            ),
            0,
            3,
        )

        adv_grid.addWidget(
            self.port_length,
            0,
            4,
        )

        adv_grid.addWidget(
            InfoButton(
                "طول تیون‌شده کلاسیک از پشت سوپاپ "
                "در نظر گرفته می‌شود. در صورت وارد کردن "
                "طول پورت، برای رسیدن به طول اجرایی "
                "از طول کل کم می‌شود."
            ),
            0,
            5,
        )

        self.advanced_box.setVisible(False)

        grid.addWidget(
            self.advanced_box,
            row + 1,
            0,
            1,
            6,
        )

        page_layout.addWidget(inputs)

        # ====================================================
        # CONFIG WARNING
        # ====================================================

        self.config_warning = QLabel()

        self.config_warning.setWordWrap(True)
        self.config_warning.setVisible(False)

        page_layout.addWidget(
            self.config_warning
        )

        # ====================================================
        # CALCULATE BUTTON
        # ====================================================

        calc_btn = QPushButton(
            "محاسبه هدرز"
        )

        calc_btn.setMinimumHeight(48)

        calc_btn.setCursor(
            Qt.PointingHandCursor
        )

        calc_btn.clicked.connect(
            self._calculate
        )

        page_layout.addWidget(calc_btn)

        # ====================================================
        # RESULTS TITLE
        # ====================================================

        results_title = QLabel(
            "نتیجه مهندسی"
        )

        results_title.setStyleSheet(
            """
            color:#ffffff;
            font-size:16px;
            font-weight:800;
            """
        )

        page_layout.addWidget(
            results_title
        )

        # ====================================================
        # RESULTS
        # ====================================================

        results_grid = QGridLayout()

        results_grid.setHorizontalSpacing(12)
        results_grid.setVerticalSpacing(12)

        for c in range(3):

            results_grid.setColumnStretch(
                c,
                1,
            )

        self.result_type = ResultCard(
            "نوع هدرز"
        )

        self.result_total = ResultCard(
            "طول کل تیون‌شده"
        )

        self.result_cyl = ResultCard(
            "حجم هر سیلندر"
        )

        self.result_primary = ResultCard(
            "طول Primary"
        )

        self.result_secondary = ResultCard(
            "طول Secondary"
        )

        self.result_primary_d = ResultCard(
            "قطر داخلی Primary"
        )

        self.result_secondary_d = ResultCard(
            "قطر داخلی Secondary"
        )

        cards = [
            self.result_type,
            self.result_total,
            self.result_cyl,
            self.result_primary,
            self.result_secondary,
            self.result_primary_d,
            self.result_secondary_d,
        ]

        for i, card in enumerate(cards):

            results_grid.addWidget(
                card,
                i // 3,
                i % 3,
            )

        page_layout.addLayout(
            results_grid
        )

        # ====================================================
        # DIAMETER INFO
        # ====================================================

        self.diameter_check = QLabel()

        self.diameter_check.setWordWrap(True)

        self.diameter_check.setObjectName(
            "InfoPanel"
        )

        page_layout.addWidget(
            self.diameter_check
        )

        # ====================================================
        # WARNING
        # ====================================================

        self.warning_box = QLabel()

        self.warning_box.setWordWrap(True)

        self.warning_box.setObjectName(
            "WarningPanel"
        )

        self.warning_box.setVisible(False)

        page_layout.addWidget(
            self.warning_box
        )

        # ====================================================
        # FORMULA TRACE
        # ====================================================

        formula_title = QLabel(
            "Formula Trace"
        )

        formula_title.setStyleSheet(
            f"""
            color:{APP_RED};
            font-size:13px;
            font-weight:800;
            """
        )

        page_layout.addWidget(
            formula_title
        )

        self.formula_box = QLabel()

        self.formula_box.setWordWrap(True)

        self.formula_box.setObjectName(
            "FormulaPanel"
        )

        page_layout.addWidget(
            self.formula_box
        )

        # ====================================================
        # ENGINEERING NOTE
        # ====================================================

        note = QLabel(
            "نکته مهندسی: 4-1 و 4-2-1 به "
            "cam timing، شکل پورت، collector، "
            "firing order و محدودیت‌های واقعی ساخت "
            "وابسته‌اند. این ابزار یک نقطه شروع "
            "مهندسی است و جایگزین flow-bench، "
            "شبیه‌سازی موج یا تست داینومتر نیست."
        )

        note.setWordWrap(True)

        note.setStyleSheet(
            f"""
            color:{APP_MUTED};
            font-size:11px;
            padding:4px;
            """
        )

        page_layout.addWidget(note)

        page_layout.addStretch(1)

        # ====================================================
        # SIGNALS
        # ====================================================

        self.header_type.currentIndexChanged.connect(
            self._header_changed
        )

        self.config_combo.currentIndexChanged.connect(
            self._config_changed
        )

    # ========================================================
    # HELPERS
    # ========================================================

    def _label(self, text):

        label = QLabel(text)

        label.setStyleSheet(
            """
            color:#f0f0f0;
            font-size:12px;
            font-weight:700;
            """
        )

        return label

    def _line(
        self,
        value,
        readonly=False,
    ):

        edit = QLineEdit(value)

        edit.setReadOnly(readonly)

        validator = QDoubleValidator(
            0.0,
            100000.0,
            3,
            edit,
        )

        validator.setNotation(
            QDoubleValidator.StandardNotation
        )

        edit.setValidator(validator)

        edit.setMinimumHeight(38)

        return edit

    def _combo(self, items):

        combo = QComboBox()

        combo.setMinimumHeight(38)

        for text, data in items:

            combo.addItem(
                text,
                data,
            )

        return combo

    # ========================================================
    # ADVANCED
    # ========================================================

    def _toggle_advanced(
        self,
        checked,
    ):

        self.advanced_box.setVisible(
            checked
        )

        self.advanced_toggle.setText(
            "⚙ بخش پیشرفته  ▲"
            if checked
            else
            "⚙ بخش پیشرفته  ▼"
        )

    # ========================================================
    # CONFIG CHANGE
    # ========================================================

    def _header_changed(self):

        self._update_config_warning()

    def _config_changed(self):

        self._update_config_warning()

    def _update_config_warning(self):

        try:

            code, cylinders = self._read_config()

        except ValueError:

            self.cylinder_display.setText("—")
            self.config_warning.clear()
            self.config_warning.setVisible(False)

            return

        htype = self.header_type.currentData()

        self.cylinder_display.setText(
            str(cylinders)
        )

        messages = []

        # ====================================================
        # ODD CYLINDER COUNT
        # ====================================================

        if (
            htype == "4-2-1"
            and cylinders % 2 != 0
        ):

            messages.append(
                "4-2-1 کلاسیک برای تعداد سیلندر فرد "
                "جفت‌سازی کامل ندارد؛ خروجی ابعادی است "
                "و Pairing واقعی نیاز به firing order دارد."
            )

        # ====================================================
        # V ENGINE
        # ====================================================

        if code.startswith("V"):

            bank = cylinders // 2

            if bank != 4:

                messages.append(
                    f"{code}: هر بانک {bank} سیلندر دارد؛ "
                    f"4-1/4-2-1 در این حالت به‌عنوان "
                    f"مدل مرجع سایزبندی در نظر گرفته شده است."
                )

        # ====================================================
        # SHOW CONFIG WARNING
        # ====================================================

        if messages:

            self.config_warning.setText(
                "⚠ "
                + "\n⚠ ".join(messages)
            )

            self.config_warning.setStyleSheet(
                f"""
                color:{APP_ORANGE};
                background:#241c12;
                border:1px solid #5a3d16;
                border-radius:8px;
                padding:10px;
                """
            )

            self.config_warning.setVisible(True)

        else:

            self.config_warning.clear()
            self.config_warning.setVisible(False)

    # ========================================================
    # DEFAULTS
    # ========================================================

    def _set_defaults(self):

        # Inline-4
        self.config_combo.setCurrentIndex(1)

        # 4-1
        self.header_type.setCurrentIndex(0)

        self.diameter_check.setText(
            "بعد از محاسبه، قطر واردشده با "
            "قطر پیشنهادی مقایسه می‌شود."
        )

        self.formula_box.setText(
            "EVO پیش‌فرض = 60° BBDC.\n"
            "برای نتیجه دقیق‌تر، EVO واقعی "
            "از Cam Card وارد شود."
        )

    # ========================================================
    # STYLING
    # ========================================================

    def _apply_style(self):

        self.setStyleSheet(
            f"""
            QDialog {{
                background:{APP_DARK};
                color:{APP_TEXT};
            }}

            QScrollArea {{
                background:{APP_DARK};
                border:none;
            }}

            QScrollArea > QWidget {{
                background:{APP_DARK};
                border:none;
            }}

            QScrollArea > QWidget > QWidget {{
                background:{APP_DARK};
                border:none;
            }}

            QWidget#HeaderPage {{
                background:{APP_DARK};
            }}

            QFrame#Intro,
            QFrame#Panel {{
                background:{APP_PANEL};
                border:1px solid {APP_BORDER};
                border-radius:12px;
            }}

            QFrame#ResultCard {{
                background:{APP_PANEL_2};
                border:1px solid {APP_BORDER};
                border-left:3px solid {APP_RED};
                border-radius:10px;
            }}

            QFrame {{
                background:transparent;
            }}

            QLineEdit,
            QComboBox {{
                background:#151515;
                color:#ffffff;
                border:1px solid #3b3b3b;
                border-radius:8px;
                padding:6px 10px;
                font-size:12px;
            }}

            QLineEdit:focus,
            QComboBox:focus {{
                border:1px solid {APP_RED};
            }}

            QComboBox QAbstractItemView {{
                background:#181818;
                color:#ffffff;
                selection-background-color:{APP_RED};
            }}

            QPushButton {{
                background:#171717;
                color:#ffffff;
                border:1px solid #3a3a3a;
                border-radius:8px;
                padding:8px 14px;
                font-weight:700;
            }}

            QPushButton:hover {{
                border-color:{APP_RED};
            }}

            QScrollBar:vertical {{
                background:#101010;
                width:11px;
                margin:2px;
            }}

            QScrollBar::handle:vertical {{
                background:#3e3e3e;
                min-height:50px;
                border-radius:5px;
            }}

            QScrollBar::handle:vertical:hover {{
                background:{APP_RED};
            }}

            QLabel#InfoPanel,
            QLabel#FormulaPanel {{
                background:#171717;
                border:1px solid #323232;
                border-radius:9px;
                padding:12px;
                color:#dddddd;
            }}

            QLabel#WarningPanel {{
                background:#241c12;
                border:1px solid #5a3d16;
                border-radius:9px;
                padding:12px;
                color:{APP_ORANGE};
            }}
            """
        )