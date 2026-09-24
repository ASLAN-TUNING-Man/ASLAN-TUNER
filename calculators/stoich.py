from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QFont,
)
from PySide6.QtWidgets import (
    QScrollArea,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QSizePolicy,
)


# ============================================================
# ASLAN TUNER
# STOICHIOMETRIC AFR CALCULATOR
#
# Engineering basis:
#
# Fuel:
#     Cc Hh Oo Nn
#
# Stoichiometric oxygen requirement:
#
#     nO2 = C + H/4 - O/2
#
# Fuel molecular mass:
#
#     MW = 12.011C + 1.008H + 15.999O + 14.007N
#
# AFR is mass of air / mass of fuel.
#
# Dry-air approximation:
#     oxygen mass fraction ≈ 23.2%
#
# Therefore:
#
#     AFR = (nO2 * 32.00) / (0.232 * MW)
#
# Nitrogen in the fuel is included in MW but does not
# increase external O2 requirement in this ideal model.
# ============================================================


# ------------------------------------------------------------
# COLORS
# ------------------------------------------------------------

RED = "#CE0029"
RED_BRIGHT = "#CF0029"
RED_DARK = "#860119"
RED_GLOW = "#DB0033"

BLACK = "#08090B"
DARK = "#101114"
DARK_2 = "#15171B"
DARK_3 = "#1D1E1F"
DARK_4 = "#333333"

WHITE = "#F5F5F5"
GRAY = "#A7ABB3"
GRAY_DARK = "#686D77"


# ------------------------------------------------------------
# COMMON FUEL REFERENCE DATA
#
# Formula values are for pure/reference fuels.
# Gasoline / Diesel / LPG / CNG are practical reference AFRs
# because they are mixtures rather than single compounds.
# ------------------------------------------------------------

FUEL_REFERENCE = [
    {
        "name": "Gasoline",
        "formula": "C8H18",
        "afr": 14.70,
        "note": "Practical automotive reference",
    },
    {
        "name": "Diesel",
        "formula": "≈ CH1.8",
        "afr": 14.50,
        "note": "Typical diesel reference",
    },
    {
        "name": "E10",
        "formula": "Gasoline + 10% Ethanol",
        "afr": 14.08,
        "note": "Typical reference",
    },
    {
        "name": "E20",
        "formula": "Gasoline + 20% Ethanol",
        "afr": 13.80,
        "note": "Approximate blend reference",
    },
    {
        "name": "E30",
        "formula": "Gasoline + 30% Ethanol",
        "afr": 13.20,
        "note": "Approximate blend reference",
    },
    {
        "name": "E50",
        "formula": "Gasoline + 50% Ethanol",
        "afr": 12.40,
        "note": "Approximate blend reference",
    },
    {
        "name": "E85",
        "formula": "Gasoline + Ethanol",
        "afr": 9.80,
        "note": "Typical E85 reference",
    },
    {
        "name": "Ethanol",
        "formula": "C2H6O",
        "afr": 9.00,
        "note": "Pure ethanol",
    },
    {
        "name": "Methanol",
        "formula": "CH4O",
        "afr": 6.45,
        "note": "Pure methanol",
    },
    {
        "name": "CNG",
        "formula": "≈ CH4",
        "afr": 17.20,
        "note": "Typical methane/CNG reference",
    },
]


# ============================================================
# AFR REFERENCE CHART
# ============================================================

class AFRReferenceChart(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(285)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.selected_index = 0

        self.setMouseTracking(True)

    def set_selected(self, index):
        self.selected_index = index
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # Background
        painter.fillRect(
            rect,
            QColor(DARK)
        )

        # Title
        painter.setPen(QColor(RED))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)

        painter.setFont(title_font)

        painter.drawText(
            18,
            25,
            "FUEL AFR REFERENCE"
        )

        # Subtitle
        painter.setPen(QColor(GRAY))

        subtitle_font = QFont()
        subtitle_font.setPointSize(9)

        painter.setFont(subtitle_font)

        painter.drawText(
            18,
            44,
            "Common stoichiometric AFR reference values"
        )

        # Chart area
        chart_left = 150
        chart_right = self.width() - 25
        chart_top = 65
        chart_bottom = self.height() - 25

        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top

        max_afr = 18.0

        rows = len(FUEL_REFERENCE)

        row_height = chart_height / rows

        # Vertical grid
        painter.setPen(
            QPen(
                QColor("#292D34"),
                1
            )
        )

        for value in range(0, 19, 3):

            x = chart_left + (
                value / max_afr
            ) * chart_width

            painter.drawLine(
                int(x),
                chart_top,
                int(x),
                chart_bottom
            )

            painter.setPen(
                QColor(GRAY_DARK)
            )

            painter.drawText(
                int(x - 8),
                chart_bottom + 16,
                str(value)
            )

            painter.setPen(
                QPen(
                    QColor("#292D34"),
                    1
                )
            )

        # Bars
        for i, fuel in enumerate(FUEL_REFERENCE):

            y = chart_top + i * row_height

            bar_y = int(
                y + row_height * 0.20
            )

            bar_h = int(
                row_height * 0.55
            )

            bar_width = (
                fuel["afr"] / max_afr
            ) * chart_width

            # Fuel name
            painter.setPen(
                QColor(WHITE)
            )

            font = QFont()
            font.setPointSize(8)
            font.setBold(True)

            painter.setFont(font)

            painter.drawText(
                18,
                int(
                    bar_y + bar_h * 0.72
                ),
                fuel["name"]
            )

            # Bar background
            painter.setBrush(
                QColor(DARK_3)
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.drawRoundedRect(
                QRectF(
                    chart_left,
                    bar_y,
                    chart_width,
                    bar_h
                ),
                4,
                4
            )

            # Actual bar
            if i == self.selected_index:

                bar_color = QColor(
                    RED_BRIGHT
                )

            else:

                bar_color = QColor(
                    RED_DARK
                )

            painter.setBrush(
                QBrush(bar_color)
            )

            painter.drawRoundedRect(
                QRectF(
                    chart_left,
                    bar_y,
                    bar_width,
                    bar_h
                ),
                4,
                4
            )

            # AFR number
            painter.setPen(
                QColor(WHITE)
            )

            painter.drawText(
                int(
                    chart_left +
                    bar_width +
                    8
                ),
                int(
                    bar_y +
                    bar_h * 0.72
                ),
                f"{fuel['afr']:.2f}"
            )


# ============================================================
# MAIN CALCULATOR
# ============================================================

class StoichCalculator(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.setWindowTitle(
            "ASLAN TUNER - Stoichiometric Ratio"
        )

        self.setMinimumSize(
            850,
            760
        )

        self.resize(
            980,
            820
        )

        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        # ----------------------------------------------------
        # STYLE
        # ----------------------------------------------------

        self.setStyleSheet("""

            QDialog {
                background-color: #08090B;
            }

            QLabel {
                color: #F5F5F5;
            }

            QLabel#Title {
                color: #FF1744;
                font-size: 27px;
                font-weight: bold;
            }

            QLabel#Subtitle {
                color: #A7ABB3;
                font-size: 13px;
            }

            QLabel#SectionTitle {
                color: #FF1744;
                font-size: 15px;
                font-weight: bold;
            }

            QLabel#FormulaDisplay {
                color: #FF2B55;
                background-color: #101114;
                border: 1px solid #8E0E26;
                border-radius: 8px;
                padding: 10px;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#Result {
                color: #FFFFFF;
                background-color: #101114;
                border: 1px solid #FF1744;
                border-radius: 10px;
                padding: 15px;
                font-size: 23px;
                font-weight: bold;
            }

            QLabel#SecondaryResult {
                color: #D8DADF;
                background-color: #15171B;
                border: 1px solid #292D34;
                border-radius: 7px;
                padding: 10px;
                font-size: 12px;
            }

            QLabel#Info {
                color: #A7ABB3;
                background-color: #15171B;
                border: 1px solid #292D34;
                border-radius: 7px;
                padding: 9px;
                font-size: 11px;
            }

            QLineEdit {
                background-color: #15171B;
                color: #FFFFFF;
                border: 1px solid #3A3E46;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                selection-background-color: #8E0E26;
            }

            QLineEdit:focus {
                border: 1px solid #FF1744;
            }

            QPushButton {
                background-color: #8E0E26;
                color: #FFFFFF;
                border: 1px solid #FF1744;
                border-radius: 7px;
                padding: 9px 13px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #C9153A;
                border: 1px solid #FF2B55;
            }

            QPushButton:pressed {
                background-color: #65091C;
            }

            QPushButton#InfoButton {
                background-color: #15171B;
                color: #FF1744;
                border: 1px solid #8E0E26;
                border-radius: 12px;
                padding: 0px;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton#InfoButton:hover {
                background-color: #FF1744;
                color: #FFFFFF;
            }

            QPushButton#FuelButton {
                background-color: #15171B;
                color: #D8DADF;
                border: 1px solid #292D34;
                border-radius: 6px;
                padding: 7px;
                font-size: 10px;
            }

            QPushButton#FuelButton:hover {
                background-color: #8E0E26;
                color: #FFFFFF;
                border: 1px solid #FF1744;
            }

            QFrame#Card {
                background-color: #101114;
                border: 1px solid #292D34;
                border-radius: 10px;
            }

        """)

        # ----------------------------------------------------
        # MAIN LAYOUT
        # ----------------------------------------------------

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            20,
            24,
            20
        )

        layout.setSpacing(12)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel(
            "STOICHIOMETRIC RATIO"
        )

        title.setObjectName(
            "Title"
        )

        title_box.addWidget(
            title
        )

        subtitle = QLabel(
            "Chemical fuel composition → Stoichiometric AFR"
        )

        subtitle.setObjectName(
            "Subtitle"
        )

        title_box.addWidget(
            subtitle
        )

        header.addLayout(
            title_box
        )

        header.addStretch()

        formula_label = QLabel(
            "C8H18"
        )

        formula_label.setObjectName(
            "FormulaDisplay"
        )

        formula_label.setMinimumWidth(
            140
        )

        formula_label.setAlignment(
            Qt.AlignCenter
        )

        self.formula_display = formula_label

        header.addWidget(
            formula_label
        )

        layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # INPUT CARD
        # ----------------------------------------------------

        input_card = QFrame()

        input_card.setObjectName(
            "Card"
        )

        input_layout = QVBoxLayout(
            input_card
        )

        input_layout.setContentsMargins(
            16,
            14,
            16,
            14
        )

        section_title = QLabel(
            "FUEL CHEMICAL COMPOSITION"
        )

        section_title.setObjectName(
            "SectionTitle"
        )

        input_layout.addWidget(
            section_title
        )

        input_layout.addSpacing(5)

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            10
        )

        grid.setVerticalSpacing(
            10
        )

        # Carbon
        self.carbon_input = self.create_input(
            "8"
        )

        grid.addWidget(
            QLabel("Carbon  (C)"),
            0,
            0
        )

        grid.addWidget(
            self.carbon_input,
            0,
            1
        )

        grid.addWidget(
            self.create_info_button(
                "تعداد اتم‌های کربن در هر مولکول سوخت.\n\n"
                "مثال Octane:\n"
                "C8H18 → کربن = 8"
            ),
            0,
            2
        )

        # Hydrogen
        self.hydrogen_input = self.create_input(
            "18"
        )

        grid.addWidget(
            QLabel("Hydrogen  (H)"),
            0,
            3
        )

        grid.addWidget(
            self.hydrogen_input,
            0,
            4
        )

        grid.addWidget(
            self.create_info_button(
                "تعداد اتم‌های هیدروژن در هر مولکول سوخت.\n\n"
                "مثال Octane:\n"
                "C8H18 → هیدروژن = 18"
            ),
            0,
            5
        )

        # Oxygen
        self.oxygen_input = self.create_input(
            "0"
        )

        grid.addWidget(
            QLabel("Oxygen  (O)"),
            1,
            0
        )

        grid.addWidget(
            self.oxygen_input,
            1,
            1
        )

        grid.addWidget(
            self.create_info_button(
                "اکسیژن موجود داخل خود سوخت.\n\n"
                "اکسیژن موجود در سوخت باعث کاهش O₂ موردنیاز از هوای ورودی می‌شود."
            ),
            1,
            2
        )

        # Nitrogen
        self.nitrogen_input = self.create_input(
            "0"
        )

        grid.addWidget(
            QLabel("Nitrogen  (N)"),
            1,
            3
        )

        grid.addWidget(
            self.nitrogen_input,
            1,
            4
        )

        grid.addWidget(
            self.create_info_button(
                "نیتروژن موجود در خود سوخت.\n\n"
                "در مدل احتراق کامل ایده‌آل، نیتروژن سوخت در محاسبه نیاز O₂ خارجی وارد نمی‌شود و در جرم مولکولی لحاظ می‌شود."
            ),
            1,
            5
        )

        input_layout.addLayout(
            grid
        )

        layout.addWidget(
            input_card
        )

        # ----------------------------------------------------
        # LIVE FORMULA
        # ----------------------------------------------------

        self.formula_text = QLabel(
            "Fuel Formula: C8H18O0N0"
        )

        self.formula_text.setObjectName(
            "FormulaDisplay"
        )

        self.formula_text.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.formula_text
        )

        # ----------------------------------------------------
        # CALCULATE BUTTON
        # ----------------------------------------------------

        calculate_button = QPushButton(
            "⚡ CALCULATE STOICHIOMETRIC AFR"
        )

        calculate_button.setMinimumHeight(
            44
        )

        calculate_button.clicked.connect(
            self.calculate
        )

        layout.addWidget(
            calculate_button
        )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        self.result = QLabel(
            "Stoichiometric AFR = ---"
        )

        self.result.setObjectName(
            "Result"
        )

        self.result.setAlignment(
            Qt.AlignCenter
        )

        self.result.setWordWrap(
            True
        )

        layout.addWidget(
            self.result
        )

        # ----------------------------------------------------
        # SECONDARY RESULTS
        # ----------------------------------------------------

        self.details = QLabel(
            "O₂ Required = ---\n"
            "Fuel Molecular Mass = ---"
        )

        self.details.setObjectName(
            "SecondaryResult"
        )

        self.details.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.details
        )

        # ----------------------------------------------------
        # REFERENCE CHART
        # ----------------------------------------------------

        chart_card = QFrame()

        chart_card.setObjectName(
            "Card"
        )

        chart_layout = QVBoxLayout(
            chart_card
        )

        chart_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        self.chart = AFRReferenceChart()

        chart_layout.addWidget(
            self.chart
        )

        layout.addWidget(
            chart_card
        )

        # ----------------------------------------------------
        # FUEL QUICK SELECT
        # ----------------------------------------------------

        quick_title = QLabel(
            "QUICK FUEL REFERENCES"
        )

        quick_title.setObjectName(
            "SectionTitle"
        )

        layout.addWidget(
            quick_title
        )

        quick_layout = QGridLayout()

        self.fuel_buttons = []

        for index, fuel in enumerate(
            FUEL_REFERENCE
        ):

            button = QPushButton(
                f"{fuel['name']}\n"
                f"{fuel['afr']:.2f}"
            )

            button.setObjectName(
                "FuelButton"
            )

            button.setMinimumHeight(
                42
            )

            button.clicked.connect(
                lambda checked=False,
                i=index:
                self.select_reference_fuel(i)
            )

            self.fuel_buttons.append(
                button
            )

            row = index // 5
            col = index % 5

            quick_layout.addWidget(
                button,
                row,
                col
            )

        layout.addLayout(
            quick_layout
        )

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        info = QLabel(
            "Engineering basis: CcHhOoNn\n"
            "nO₂ = C + H/4 − O/2\n"
            "AFR = (nO₂ × 32.00) / (0.232 × MWfuel)\n\n"
            "AFR یعنی جرم هوای لازم برای احتراق کامل یک واحد جرم سوخت."
        )

        info.setObjectName(
            "Info"
        )

        info.setWordWrap(
            True
        )

        layout.addWidget(
            info
        )

        # ----------------------------------------------------
        # LIVE UPDATE
        # ----------------------------------------------------

        self.carbon_input.textChanged.connect(
            self.update_formula_preview
        )

        self.hydrogen_input.textChanged.connect(
            self.update_formula_preview
        )

        self.oxygen_input.textChanged.connect(
            self.update_formula_preview
        )

        self.nitrogen_input.textChanged.connect(
            self.update_formula_preview
        )

        # Initial preview
        self.update_formula_preview()

    # ========================================================
    # INPUT CREATOR
    # ========================================================

    def create_input(self, value):

        edit = QLineEdit()

        edit.setText(
            value
        )

        edit.setAlignment(
            Qt.AlignCenter
        )

        edit.setMinimumWidth(
            90
        )

        return edit

    # ========================================================
    # INFO BUTTON
    # ========================================================

    def create_info_button(self, text):

        button = QPushButton(
            "ⓘ"
        )

        button.setObjectName(
            "InfoButton"
        )

        button.setFixedSize(
            26,
            26
        )

        button.clicked.connect(
            lambda checked=False,
            message=text:
            QMessageBox.information(
                self,
                "ASLAN TUNER - Information",
                message
            )
        )

        return button

    # ========================================================
    # SAFE FLOAT
    # ========================================================

    def get_number(self, widget):

        text = widget.text().strip()

        if not text:
            raise ValueError

        value = float(
            text
        )

        if value < 0:
            raise ValueError

        return value

    # ========================================================
    # FORMULA PREVIEW
    # ========================================================

    def update_formula_preview(self):

        try:

            c = self.get_number(
                self.carbon_input
            )

            h = self.get_number(
                self.hydrogen_input
            )

            o = self.get_number(
                self.oxygen_input
            )

            n = self.get_number(
                self.nitrogen_input
            )

            formula = (
                f"C{self.format_subscript_number(c)}"
                f"H{self.format_subscript_number(h)}"
                f"O{self.format_subscript_number(o)}"
                f"N{self.format_subscript_number(n)}"
            )

            self.formula_text.setText(
                f"Fuel Formula: {formula}"
            )

            self.formula_display.setText(
                formula
            )

        except ValueError:

            self.formula_text.setText(
                "Fuel Formula: ---"
            )

            self.formula_display.setText(
                "---"
            )

    # ========================================================
    # NUMBER FORMATTER
    # ========================================================

    def format_subscript_number(self, value):

        if value == int(value):

            return str(
                int(value)
            )

        return f"{value:g}"

    # ========================================================
    # REFERENCE FUEL
    # ========================================================

    def select_reference_fuel(self, index):

        fuel = FUEL_REFERENCE[index]

        # Highlight selected bar
        self.chart.set_selected(
            index
        )

        # Only chemical formulas with exact
        # elemental composition are entered into
        # the chemical calculator.
        #
        # Practical blends remain reference values.

        if fuel["name"] == "Gasoline":

            self.carbon_input.setText(
                "8"
            )

            self.hydrogen_input.setText(
                "18"
            )

            self.oxygen_input.setText(
                "0"
            )

            self.nitrogen_input.setText(
                "0"
            )

        elif fuel["name"] == "Ethanol":

            self.carbon_input.setText(
                "2"
            )

            self.hydrogen_input.setText(
                "6"
            )

            self.oxygen_input.setText(
                "1"
            )

            self.nitrogen_input.setText(
                "0"
            )

        elif fuel["name"] == "Methanol":

            self.carbon_input.setText(
                "1"
            )

            self.hydrogen_input.setText(
                "4"
            )

            self.oxygen_input.setText(
                "1"
            )

            self.nitrogen_input.setText(
                "0"
            )

        elif fuel["name"] == "CNG":

            self.carbon_input.setText(
                "1"
            )

            self.hydrogen_input.setText(
                "4"
            )

            self.oxygen_input.setText(
                "0"
            )

            self.nitrogen_input.setText(
                "0"
            )

        else:

            # For blends, show the reference AFR
            # directly rather than pretending the blend
            # has one exact molecular formula.

            self.result.setText(
                f"{fuel['name']} Reference AFR = "
                f"{fuel['afr']:.2f}:1"
            )

            self.details.setText(
                f"Formula / model: {fuel['formula']}\n"
                f"{fuel['note']}"
            )

            self.formula_text.setText(
                f"Reference Fuel: {fuel['name']}"
            )

            self.formula_display.setText(
                fuel["name"]
            )

            return

        self.calculate()

    # ========================================================
    # CALCULATE
    # ========================================================

    def calculate(self):

        try:

            C = self.get_number(
                self.carbon_input
            )

            H = self.get_number(
                self.hydrogen_input
            )

            O = self.get_number(
                self.oxygen_input
            )

            N = self.get_number(
                self.nitrogen_input
            )

            # At least one fuel atom must exist
            if (
                C <= 0 and
                H <= 0 and
                O <= 0 and
                N <= 0
            ):
                raise ValueError

            # ------------------------------------------------
            # MOLECULAR MASS
            # ------------------------------------------------

            MW = (
                12.011 * C +
                1.008 * H +
                15.999 * O +
                14.007 * N
            )

            if MW <= 0:
                raise ValueError

            # ------------------------------------------------
            # STOICHIOMETRIC O2
            #
            # CcHhOoNn
            #
            # nO2 = C + H/4 - O/2
            # ------------------------------------------------

            O2_required = (
                C +
                H / 4.0 -
                O / 2.0
            )

            # A fuel cannot require negative
            # external oxygen in this ideal model.
            O2_required = max(
                0.0,
                O2_required
            )

            # ------------------------------------------------
            # AIR / FUEL RATIO
            #
            # Oxygen mass fraction of dry air ≈ 0.232
            #
            # mass O2 = nO2 * 32
            # mass air = mass O2 / 0.232
            #
            # AFR = mass air / mass fuel
            # ------------------------------------------------

            AIR_O2_MASS_FRACTION = 0.232

            AFR = (
                O2_required * 32.00
            ) / (
                AIR_O2_MASS_FRACTION * MW
            )

            # ------------------------------------------------
            # FORMULA STRING
            # ------------------------------------------------

            formula = (
                f"C{self.format_subscript_number(C)}"
                f"H{self.format_subscript_number(H)}"
                f"O{self.format_subscript_number(O)}"
                f"N{self.format_subscript_number(N)}"
            )

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            self.result.setText(
                f"Stoichiometric AFR = "
                f"{AFR:.3f}:1"
            )

            self.details.setText(
                f"Fuel Formula: {formula}\n"
                f"O₂ Required = {O2_required:.4f} mol O₂/mol fuel"
                f"    |    "
                f"Fuel Molecular Mass = {MW:.4f} g/mol"
            )

            # ------------------------------------------------
            # UPDATE FORMULA DISPLAY
            # ------------------------------------------------

            self.formula_text.setText(
                f"Fuel Formula: {formula}"
            )

            self.formula_display.setText(
                formula
            )

        except ValueError:

            self.result.setText(
                "خطا: مقادیر C / H / O / N معتبر نیستند."
            )

            self.details.setText(
                "لطفاً فقط اعداد صفر یا مثبت وارد کنید."
            )