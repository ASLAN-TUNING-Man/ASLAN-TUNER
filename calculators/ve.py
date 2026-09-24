import math

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QFileDialog,
    QMessageBox,
    QGroupBox,
)


# ============================================================
# CONSTANTS
# ============================================================

ATMOSPHERIC_KPA = 101.325
PSI_TO_KPA = 6.894757293
REFERENCE_IAT_C = 20.0


# ============================================================
# GENERAL UTILITIES
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def psi_to_kpa(psi):
    return float(psi) * PSI_TO_KPA


def kpa_to_psi(kpa):
    return float(kpa) / PSI_TO_KPA


def boost_to_map(boost_psi, baro_kpa):
    """
    Converts gauge boost into absolute MAP.

    MAP = atmospheric pressure + gauge boost
    """
    boost_psi = max(0.0, float(boost_psi))

    return float(baro_kpa) + psi_to_kpa(boost_psi)


def air_density_ratio(iat_c, baro_kpa):
    """
    Useful for air-mass calculations.

    IMPORTANT:
    This is NOT directly multiplied into VE.

    VE describes cylinder filling relative to the
    theoretical cylinder volume. Temperature and
    pressure belong to the air-density calculation.
    """
    temperature_k = float(iat_c) + 273.15
    reference_k = REFERENCE_IAT_C + 273.15

    if temperature_k <= 0.0:
        temperature_k = 273.15

    return (
        float(baro_kpa) / temperature_k
    ) / (
        ATMOSPHERIC_KPA / reference_k
    )


# ============================================================
# AXIS HELPERS
# ============================================================

def unique_axis(values):
    """
    Returns a strictly increasing unique axis.
    """
    result = []

    for value in values:
        value = float(value)

        if not result:
            result.append(value)
            continue

        if value > result[-1]:
            result.append(value)

    return result


def choose_axis_step(start, end, count, axis_type):
    """
    Chooses a practical rounding step that is small enough
    to preserve the requested number of unique points.
    """

    start = float(start)
    end = float(end)
    count = int(count)

    if count <= 1:
        return 1.0

    average_spacing = abs(end - start) / max(
        1,
        count - 1
    )

    if axis_type == "rpm":
        candidates = [
            500.0,
            250.0,
            100.0,
            50.0,
            25.0,
            10.0,
            5.0,
            1.0,
        ]
    else:
        candidates = [
            10.0,
            5.0,
            2.0,
            1.0,
            0.5,
            0.1,
        ]

    for step in candidates:
        if step <= average_spacing * 0.50:
            return step

    return candidates[-1]


def round_to_step(value, step):
    if step <= 0:
        return float(value)

    return float(
        round(float(value) / step) * step
    )


def make_exact_axis(start, end, count, axis_type):
    """
    Generates exactly `count` rounded, unique, increasing values.
    """

    count = int(count)

    if count <= 1:
        return [float(start)]

    start = float(start)
    end = float(end)

    if end <= start:
        end = start + float(count - 1)

    step = choose_axis_step(
        start,
        end,
        count,
        axis_type
    )

    raw = [
        start + (
            (end - start) * i / (count - 1)
        )
        for i in range(count)
    ]

    rounded = [
        round_to_step(value, step)
        for value in raw
    ]

    rounded[0] = round_to_step(
        start,
        step
    )

    rounded[-1] = round_to_step(
        end,
        step
    )

    for i in range(1, len(rounded)):
        if rounded[i] <= rounded[i - 1]:
            candidate = rounded[i]

            while candidate <= rounded[i - 1]:
                candidate += step

            rounded[i] = candidate

    if rounded[-1] > round_to_step(end, step):

        smaller_steps = (
            [250, 100, 50, 25, 10, 5, 1]
            if axis_type == "rpm"
            else [5, 2, 1, 0.5, 0.1]
        )

        for smaller_step in smaller_steps:

            if smaller_step >= step:
                continue

            candidate_axis = []

            for value in raw:
                candidate_axis.append(
                    round_to_step(
                        value,
                        smaller_step
                    )
                )

            valid = True

            for i in range(
                1,
                len(candidate_axis)
            ):
                if candidate_axis[i] <= candidate_axis[i - 1]:
                    valid = False
                    break

            if valid:
                rounded = candidate_axis
                break

    if len(unique_axis(rounded)) != count:

        minimum = round_to_step(
            start,
            step
        )

        maximum = round_to_step(
            end,
            step
        )

        if maximum <= minimum:
            maximum = (
                minimum
                + step * (count - 1)
            )

        safe_spacing = (
            maximum - minimum
        ) / max(
            1,
            count - 1
        )

        if safe_spacing <= 0:
            safe_spacing = step

        rounded = [
            minimum + safe_spacing * i
            for i in range(count)
        ]

    result = []

    for value in rounded:

        value = float(value)

        if not result:
            result.append(value)
            continue

        if value <= result[-1]:
            value = (
                result[-1]
                + step
            )

        result.append(value)

    if len(result) != count:

        result = [
            start + (
                (end - start) * i / (count - 1)
            )
            for i in range(count)
        ]

    return result


def build_rpm_axis(idle, cutoff, count):

    idle = max(
        300.0,
        float(idle)
    )

    cutoff = max(
        idle + 100.0,
        float(cutoff)
    )

    return make_exact_axis(
        idle,
        cutoff,
        count,
        "rpm"
    )


def build_map_axis(baro_kpa, boost_psi, count):

    atmospheric = max(
        50.0,
        float(baro_kpa)
    )

    max_map = boost_to_map(
        boost_psi,
        atmospheric
    )

    min_map = max(
        20.0,
        atmospheric * 0.20
    )

    if max_map <= min_map:
        max_map = min_map + 20.0

    return make_exact_axis(
        min_map,
        max_map,
        count,
        "map"
    )


# ============================================================
# INFO BUTTON
# ============================================================

class InfoButton(QPushButton):

    def __init__(
        self,
        title,
        text,
        parent=None
    ):
        super().__init__(
            "ⓘ",
            parent
        )

        self.title = title
        self.info_text = text

        self.setFixedSize(
            30,
            30
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setStyleSheet("""
            QPushButton {
                background-color: #151515;
                color: #ff3030;
                border: 1px solid #650000;
                border-radius: 15px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }

            QPushButton:hover {
                background-color: #350000;
                color: #ff5050;
                border: 1px solid #ff2020;
            }

            QPushButton:pressed {
                background-color: #650000;
            }
        """)

        self.clicked.connect(
            self.show_info
        )

    def show_info(self):

        QMessageBox.information(
            self,
            f"راهنمای {self.title}",
            self.info_text
        )


# ============================================================
# VE ENGINE
# ============================================================

class VEEngine:
    """
    ASLAN TUNER
    FINAL ENGINEERING VE MODEL

    MODEL PHILOSOPHY
    ----------------

    VE is cylinder filling efficiency.

    The final model separates:

    1. Engine-specific breathing capability
       -> BMEP anchor + bounded power-density correction

    2. RPM breathing behavior
       -> idle / peak torque / peak power / cutoff

    3. MAP/load behavior
       -> vacuum/load effect
       -> very small bounded boost-side correction

    4. Intake/exhaust efficiency
       -> small bounded hardware correction

    IMPORTANT:

    IAT and atmospheric pressure are NOT multiplied directly
    into physical VE.

    They belong to air-density calculations.

    IMPORTANT:

    Boost is NOT multiplied directly as a large VE multiplier.

    Absolute MAP already contains manifold pressure.
    Only a very small bounded boost-side breathing correction
    is allowed to represent the fact that boosted engines can
    show some change in filling efficiency.

    IMPORTANT:

    Lambda correction is NOT physical VE.

    It creates a separate Fuel Model VE table.
    """

    MODEL_VERSION = "Engineering FINAL"

    def __init__(self, params):

        self.params = params

        self.displacement = float(
            params.get(
                "displacement",
                1600.0
            )
        )

        self.cylinders = int(
            params.get(
                "cylinders",
                4
            )
        )

        self.hp = float(
            params.get(
                "horsepower",
                params.get(
                    "hp",
                    80.0
                )
            )
        )

        self.torque = float(
            params.get(
                "torque",
                110.0
            )
        )

        self.compression = float(
            params.get(
                "compression",
                9.0
            )
        )

        self.idle_rpm = float(
            params.get(
                "idle_rpm",
                800.0
            )
        )

        self.rpm_torque = float(
            params.get(
                "rpm_torque",
                3000.0
            )
        )

        self.rpm_power = float(
            params.get(
                "rpm_power",
                5000.0
            )
        )

        self.cutoff = float(
            params.get(
                "cutoff",
                7000.0
            )
        )

        self.boost_psi = max(
            0.0,
            float(
                params.get(
                    "boost",
                    0.0
                )
            )
        )

        self.baro_kpa = float(
            params.get(
                "baro_kpa",
                101.325
            )
        )

        self.iat_c = float(
            params.get(
                "iat_c",
                20.0
            )
        )

        self.engine_type = params.get(
            "engine_type",
            "Naturally Aspirated"
        )

        self.intake_efficiency = clamp(
            float(
                params.get(
                    "intake_efficiency",
                    90.0
                )
            ),
            50.0,
            110.0
        )

        self.exhaust_efficiency = clamp(
            float(
                params.get(
                    "exhaust_efficiency",
                    90.0
                )
            ),
            50.0,
            110.0
        )

    # ========================================================
    # BASIC ENGINE VALIDATION
    # ========================================================

    def is_turbo(self):
        return self.engine_type.lower().startswith(
            "turbo"
        )

    def normalized_rpm_points(self):

        idle = max(
            300.0,
            self.idle_rpm
        )

        torque_rpm = max(
            idle + 300.0,
            self.rpm_torque
        )

        power_rpm = max(
            torque_rpm + 300.0,
            self.rpm_power
        )

        cutoff = max(
            power_rpm + 300.0,
            self.cutoff
        )

        return (
            idle,
            torque_rpm,
            power_rpm,
            cutoff
        )

    # ========================================================
    # BMEP
    # ========================================================

    def bmep_bar(self):
        """
        Four-stroke BMEP:

        BMEP(Pa) =
            Torque(Nm) * 4*pi
            / displacement(m^3)

        BMEP is used as an engine-specific anchor.

        It is NOT treated as a direct identity between
        BMEP and VE.
        """

        displacement_m3 = (
            self.displacement
            / 1_000_000.0
        )

        if displacement_m3 <= 0.0:
            return 0.0

        bmep_pa = (
            self.torque
            * 4.0
            * math.pi
            / displacement_m3
        )

        return (
            bmep_pa
            / 100000.0
        )

    # ========================================================
    # POWER DENSITY
    # ========================================================

    def power_density(self):
        """
        Horsepower per liter.

        This is used only as a bounded secondary indicator
        of the engine's breathing capability.

        HP is NOT multiplied directly into VE.
        """

        displacement_liters = (
            self.displacement
            / 1000.0
        )

        if displacement_liters <= 0.0:
            return 0.0

        return (
            self.hp
            / displacement_liters
        )

    # ========================================================
    # PEAK VE ESTIMATION
    # ========================================================

    def physical_reference_ve(self):
        """
        FINAL ENGINEERING PEAK VE ANCHOR

        BMEP provides the main engine-specific anchor.

        Approximate calibration:

            BMEP ~ 6 bar   -> ~80% peak VE
            BMEP ~10 bar   -> ~90% peak VE
            BMEP ~14 bar   -> ~100% peak VE

        Formula:

            PeakVE =
                0.80
                + 0.025 * (BMEP - 6)

        Secondary corrections:

        1. Compression:
           very small bounded correction.

        2. Power density:
           very small bounded correction.

        These corrections are intentionally weak so that
        no single input can dominate the model.
        """

        bmep = self.bmep_bar()

        peak_ve = (
            0.80
            + 0.025 * (
                bmep - 6.0
            )
        )

        # ----------------------------------------------------
        # COMPRESSION CORRECTION
        # ----------------------------------------------------

        compression_delta = (
            self.compression
            - 9.0
        )

        compression_correction = clamp(
            compression_delta * 0.0015,
            -0.0075,
            0.0075
        )

        peak_ve += compression_correction

        # ----------------------------------------------------
        # POWER DENSITY CORRECTION
        # ----------------------------------------------------

        hp_per_liter = self.power_density()

        power_correction = clamp(
            (
                hp_per_liter - 50.0
            ) / 500.0,
            -0.025,
            0.025
        )

        peak_ve += power_correction

        # ----------------------------------------------------
        # PRACTICAL BOUNDARIES
        # ----------------------------------------------------

        if self.is_turbo():

            return clamp(
                peak_ve,
                0.72,
                1.10
            )

        return clamp(
            peak_ve,
            0.72,
            1.05
        )

    # ========================================================
    # SMOOTHSTEP
    # ========================================================

    @staticmethod
    def smoothstep(x):

        x = clamp(
            float(x),
            0.0,
            1.0
        )

        return (
            x * x
            * (
                3.0
                - 2.0 * x
            )
        )

    @staticmethod
    def smootherstep(x):

        x = clamp(
            float(x),
            0.0,
            1.0
        )

        return (
            x
            * x
            * x
            * (
                x
                * (
                    x * 6.0
                    - 15.0
                )
                + 10.0
            )
        )

    # ========================================================
    # RPM BREATHING
    # ========================================================

    def rpm_breathing_factor(self, rpm):
        """
        FINAL RPM BREATHING MODEL

        Landmarks:

            idle        -> reduced cylinder filling
            peak torque -> maximum breathing reference
            peak power  -> slightly below peak torque
            cutoff      -> controlled high-RPM decline

        The high-RPM behavior is slightly adapted using
        horsepower per liter.

        Higher power density allows the engine to retain
        more breathing efficiency toward peak power/cutoff.

        All transitions use smootherstep so the curve remains
        continuous and smooth.
        """

        rpm = float(rpm)

        (
            idle,
            torque_rpm,
            power_rpm,
            cutoff
        ) = self.normalized_rpm_points()

        # ----------------------------------------------------
        # ENGINE BREATHING CHARACTER
        # ----------------------------------------------------

        density = self.power_density()

        high_rpm_cap = clamp(
            0.88
            + (
                density - 50.0
            ) * 0.0008,
            0.84,
            0.96
        )

        power_peak_factor = clamp(
            0.975
            + (
                density - 50.0
            ) * 0.00015,
            0.955,
            0.995
        )

        # ----------------------------------------------------
        # IDLE
        # ----------------------------------------------------

        idle_factor = 0.72

        # ----------------------------------------------------
        # IDLE -> PEAK TORQUE
        # ----------------------------------------------------

        if rpm <= idle:

            return idle_factor

        if rpm < torque_rpm:

            x = (
                rpm - idle
            ) / max(
                1.0,
                torque_rpm - idle
            )

            s = self.smootherstep(x)

            return (
                idle_factor
                + (
                    1.00
                    - idle_factor
                ) * s
            )

        # ----------------------------------------------------
        # PEAK TORQUE -> PEAK POWER
        # ----------------------------------------------------

        if rpm < power_rpm:

            x = (
                rpm - torque_rpm
            ) / max(
                1.0,
                power_rpm - torque_rpm
            )

            s = self.smootherstep(x)

            return (
                1.00
                + (
                    power_peak_factor
                    - 1.00
                ) * s
            )

        # ----------------------------------------------------
        # PEAK POWER -> CUTOFF
        # ----------------------------------------------------

        if rpm < cutoff:

            x = (
                rpm - power_rpm
            ) / max(
                1.0,
                cutoff - power_rpm
            )

            s = self.smootherstep(x)

            return (
                power_peak_factor
                + (
                    high_rpm_cap
                    - power_peak_factor
                ) * s
            )

        return high_rpm_cap

    # ========================================================
    # MAP / LOAD
    # ========================================================

    def map_load_factor(self, map_kpa):
        """
        FINAL MAP / LOAD MODEL

        Below atmospheric pressure:

            VE decreases smoothly with vacuum/load reduction.

        At atmospheric pressure:

            factor = 1.000

        Above atmospheric pressure:

            only a small bounded correction is allowed.

        This avoids treating boost as a huge direct VE multiplier
        while still allowing a realistic small pressure-side
        breathing change.
        """

        atmospheric = max(
            1.0,
            self.baro_kpa
        )

        ratio = (
            float(map_kpa)
            / atmospheric
        )

        ratio = max(
            0.0,
            ratio
        )

        # ----------------------------------------------------
        # NATURALLY ASPIRATED / VACUUM SIDE
        # ----------------------------------------------------

        if ratio <= 1.0:

            factor = (
                0.64
                + 0.36 * (
                    ratio ** 0.55
                )
            )

            return clamp(
                factor,
                0.64,
                1.0
            )

        # ----------------------------------------------------
        # BOOST SIDE
        # ----------------------------------------------------

        boost_ratio = (
            ratio - 1.0
        )

        # Saturating, bounded boost-side correction.
        #
        # Maximum additional effect is only ~2.5%.
        boost_effect = (
            1.0
            + 0.025 * (
                1.0
                - math.exp(
                    -boost_ratio
                )
            )
        )

        return clamp(
            boost_effect,
            1.0,
            1.025
        )

    # ========================================================
    # INTAKE CORRECTION
    # ========================================================

    def intake_factor(self, rpm):
        """
        Intake efficiency correction.

        90% = neutral.

        The effect is deliberately small.
        """

        (
            idle,
            torque_rpm,
            power_rpm,
            cutoff
        ) = self.normalized_rpm_points()

        rpm_progress = clamp(
            (
                float(rpm)
                - torque_rpm
            ) / max(
                1.0,
                cutoff - torque_rpm
            ),
            0.0,
            1.0
        )

        delta = (
            self.intake_efficiency
            - 90.0
        ) / 100.0

        influence = (
            0.20
            + 0.80 * rpm_progress
        )

        factor = (
            1.0
            + delta
            * 0.20
            * influence
        )

        return clamp(
            factor,
            0.90,
            1.04
        )

    # ========================================================
    # EXHAUST CORRECTION
    # ========================================================

    def exhaust_factor(self, rpm):
        """
        Exhaust efficiency correction.

        90% = neutral.

        The effect is deliberately small.
        """

        (
            idle,
            torque_rpm,
            power_rpm,
            cutoff
        ) = self.normalized_rpm_points()

        rpm_progress = clamp(
            (
                float(rpm)
                - torque_rpm
            ) / max(
                1.0,
                cutoff - torque_rpm
            ),
            0.0,
            1.0
        )

        delta = (
            self.exhaust_efficiency
            - 90.0
        ) / 100.0

        influence = (
            0.15
            + 0.85 * rpm_progress
        )

        factor = (
            1.0
            + delta
            * 0.18
            * influence
        )

        return clamp(
            factor,
            0.92,
            1.04
        )

    # ========================================================
    # FINAL PHYSICAL VE
    # ========================================================

    def calculate_engineering_ve(
        self,
        rpm,
        map_kpa
    ):
        """
        FINAL ENGINEERING VE EQUATION:

            VE =
                PeakVE
                × RPMBreathing
                × MAPLoad
                × IntakeFactor
                × ExhaustFactor

        IAT is not directly multiplied into physical VE.

        Barometric density is not directly multiplied into
        physical VE.

        Boost is not used as a large direct multiplier.

        MAP already carries manifold pressure information.
        """

        rpm = max(
            1.0,
            float(rpm)
        )

        map_kpa = max(
            1.0,
            float(map_kpa)
        )

        peak_ve = (
            self.physical_reference_ve()
        )

        rpm_factor = (
            self.rpm_breathing_factor(
                rpm
            )
        )

        map_factor = (
            self.map_load_factor(
                map_kpa
            )
        )

        intake_factor = (
            self.intake_factor(
                rpm
            )
        )

        exhaust_factor = (
            self.exhaust_factor(
                rpm
            )
        )

        ve = (
            peak_ve
            * rpm_factor
            * map_factor
            * intake_factor
            * exhaust_factor
        )

        # ----------------------------------------------------
        # FINAL PRACTICAL LIMIT
        # ----------------------------------------------------

        if self.is_turbo():
            maximum = 115.0
        else:
            maximum = 105.0

        return clamp(
            ve * 100.0,
            20.0,
            maximum
        )

    # ========================================================
    # LEGACY ESTIMATED MODEL
    # ========================================================

    def estimate_peak_ve(self):
        """
        Legacy estimated model kept for compatibility.

        The FINAL Engineering model should be used for the
        actual engineering VE table.
        """

        if self.displacement <= 0.0:
            return 0.80

        hp_per_liter = (
            self.hp
            / (
                self.displacement
                / 1000.0
            )
        )

        torque_per_liter = (
            self.torque
            / (
                self.displacement
                / 1000.0
            )
        )

        if self.is_turbo():

            base = 0.90
            low = 0.72
            high = 1.10

        else:

            base = 0.86
            low = 0.68
            high = 1.02

        hp_factor = clamp(
            (
                hp_per_liter
                - 35.0
            ) / 120.0,
            -0.10,
            0.10
        )

        torque_factor = clamp(
            (
                torque_per_liter
                - 75.0
            ) / 180.0,
            -0.06,
            0.06
        )

        compression_factor = clamp(
            (
                self.compression
                - 9.0
            ) * 0.008,
            -0.04,
            0.04
        )

        peak = (
            base
            + hp_factor
            + torque_factor
            + compression_factor
        )

        return clamp(
            peak,
            low,
            high
        )

    def calculate_estimated_ve(
        self,
        rpm,
        map_kpa
    ):
        """
        Compatibility estimator.

        This is not the primary engineering model.
        """

        peak_ve = (
            self.estimate_peak_ve()
        )

        rpm_factor = (
            self.rpm_breathing_factor(
                rpm
            )
        )

        map_factor = (
            self.map_load_factor(
                map_kpa
            )
        )

        ve = (
            peak_ve
            * rpm_factor
            * map_factor
        )

        return clamp(
            ve * 100.0,
            20.0,
            110.0
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def calculate_ve(
        self,
        rpm,
        map_kpa
    ):
        return self.calculate_engineering_ve(
            rpm,
            map_kpa
        )

    def calculate_both(
        self,
        rpm,
        map_kpa
    ):

        estimated = (
            self.calculate_estimated_ve(
                rpm,
                map_kpa
            )
        )

        engineering = (
            self.calculate_engineering_ve(
                rpm,
                map_kpa
            )
        )

        return (
            estimated,
            engineering
        )


# ============================================================
# LAMBDA CORRECTION
# ============================================================

def calculate_lambda_correction(
    target_lambda,
    actual_lambda
):
    """
    Fuel correction factor:

        Fuel Factor =
            Actual Lambda / Target Lambda

    Example:

        Actual = 1.377
        Target = 1.000

        Correction = +37.7%

    IMPORTANT:
    This is a fuel-model correction.
    It is NOT physical VE.
    """

    target = float(
        target_lambda
    )

    actual = float(
        actual_lambda
    )

    if target <= 0.0 or actual <= 0.0:
        return 0.0

    return (
        (
            actual / target
        ) - 1.0
    ) * 100.0


def corrected_ve(
    calculated_ve,
    target_lambda,
    actual_lambda
):
    """
    Creates a separate fuel-model VE.

    Physical VE remains untouched.
    """

    target = float(
        target_lambda
    )

    actual = float(
        actual_lambda
    )

    if target <= 0.0 or actual <= 0.0:
        return float(
            calculated_ve
        )

    factor = (
        actual / target
    )

    corrected = (
        float(calculated_ve)
        * factor
    )

    return clamp(
        corrected,
        5.0,
        160.0
    )


# ============================================================
# CURVE WIDGET
# ============================================================

class VECurveWidget(QWidget):

    def __init__(
        self,
        parent=None
    ):
        super().__init__(
            parent
        )

        self.rpms = []
        self.values = []

        self.setMinimumHeight(
            250
        )

        self.setStyleSheet("""
            QWidget {
                background-color: #090909;
            }
        """)

    def set_data(
        self,
        rpms,
        values
    ):

        self.rpms = list(
            rpms
        )

        self.values = list(
            values
        )

        self.update()

    def paintEvent(
        self,
        event
    ):

        if (
            not self.rpms
            or not self.values
        ):
            return

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#090909")
        )

        margin_left = 55
        margin_right = 20
        margin_top = 25
        margin_bottom = 40

        graph = QRectF(
            margin_left,
            margin_top,
            self.width()
            - margin_left
            - margin_right,
            self.height()
            - margin_top
            - margin_bottom
        )

        painter.setPen(
            QPen(
                QColor("#222222"),
                1
            )
        )

        for i in range(6):

            y = (
                graph.top()
                + graph.height()
                * i / 5.0
            )

            painter.drawLine(
                int(graph.left()),
                int(y),
                int(graph.right()),
                int(y)
            )

        for i in range(6):

            x = (
                graph.left()
                + graph.width()
                * i / 5.0
            )

            painter.drawLine(
                int(x),
                int(graph.top()),
                int(x),
                int(graph.bottom())
            )

        min_rpm = min(
            self.rpms
        )

        max_rpm = max(
            self.rpms
        )

        min_ve = min(
            self.values
        )

        max_ve = max(
            self.values
        )

        if max_ve - min_ve < 1.0:

            max_ve += 1.0
            min_ve -= 1.0

        painter.setPen(
            QColor("#aaaaaa")
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                9
            )
        )

        painter.drawText(
            8,
            int(
                graph.top() + 5
            ),
            f"{max_ve:.0f}%"
        )

        painter.drawText(
            8,
            int(
                graph.bottom()
            ),
            f"{min_ve:.0f}%"
        )

        painter.drawText(
            int(graph.left()),
            self.height() - 12,
            f"{min_rpm:.0f}"
        )

        painter.drawText(
            int(graph.right() - 45),
            self.height() - 12,
            f"{max_rpm:.0f}"
        )

        points = []

        for rpm, ve in zip(
            self.rpms,
            self.values
        ):

            x = (
                graph.left()
                + (
                    (
                        rpm - min_rpm
                    )
                    / max(
                        1.0,
                        max_rpm - min_rpm
                    )
                )
                * graph.width()
            )

            y = (
                graph.bottom()
                - (
                    (
                        ve - min_ve
                    )
                    / max(
                        0.001,
                        max_ve - min_ve
                    )
                )
                * graph.height()
            )

            points.append(
                (x, y)
            )

        painter.setPen(
            QPen(
                QColor("#ff2020"),
                3
            )
        )

        for i in range(
            len(points) - 1
        ):

            painter.drawLine(
                int(points[i][0]),
                int(points[i][1]),
                int(points[i + 1][0]),
                int(points[i + 1][1])
            )

        painter.setBrush(
            QBrush(
                QColor("#ff2020")
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        for x, y in points:

            painter.drawEllipse(
                int(x - 3),
                int(y - 3),
                6,
                6
            )

        painter.end()


# ============================================================
# TABLE WINDOW
# ============================================================

class VETableWindow(QDialog):

    def __init__(
        self,
        rpms,
        maps,
        calculated,
        corrected,
        target_lambda,
        actual_lambda,
        engineering=None,
        engineering_corrected=None,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.rpms = list(
            rpms
        )

        self.maps = list(
            maps
        )

        self.calculated = calculated

        self.corrected = corrected

        self.engineering = (
            engineering
            if engineering is not None
            else calculated
        )

        self.engineering_corrected = (
            engineering_corrected
            if engineering_corrected is not None
            else self.engineering
        )

        self.target_lambda = float(
            target_lambda
        )

        self.actual_lambda = float(
            actual_lambda
        )

        self.setWindowTitle(
            "ASLAN TUNER • VE MAP"
        )

        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.resize(
            1250,
            720
        )

        self.setStyleSheet("""
            QDialog {
                background-color: #080808;
                color: #eeeeee;
            }

            QLabel {
                color: #eeeeee;
            }

            QTableWidget {
                background-color: #0d0d0d;
                color: #eeeeee;
                gridline-color: #252525;
                border: 1px solid #252525;
                selection-background-color: #8b0000;
                selection-color: white;
            }

            QHeaderView::section {
                background-color: #151515;
                color: #ff3030;
                border: 1px solid #252525;
                padding: 7px;
                font-weight: bold;
            }

            QComboBox {
                background-color: #111111;
                color: #eeeeee;
                border: 1px solid #333333;
                padding: 7px;
            }

            QPushButton {
                background-color: #151515;
                color: #eeeeee;
                border: 1px solid #7a0000;
                padding: 8px 18px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #8b0000;
            }
        """)

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            14,
            14,
            14,
            14
        )

        root.setSpacing(
            10
        )

        title = QLabel(
            "VOLUMETRIC EFFICIENCY • FINAL ENGINEERING"
        )

        title.setStyleSheet("""
            QLabel {
                color: #ff3030;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        root.addWidget(
            title
        )

        correction = calculate_lambda_correction(
            self.target_lambda,
            self.actual_lambda
        )

        info = QLabel(
            f"Target λ: {self.target_lambda:.3f}"
            f"    |    "
            f"Actual λ: {self.actual_lambda:.3f}"
            f"    |    "
            f"Fuel Correction: {correction:+.2f}%"
        )

        info.setStyleSheet("""
            QLabel {
                color: #bbbbbb;
                padding: 4px;
            }
        """)

        root.addWidget(
            info
        )

        note = QLabel(
            "Physical VE and Lambda-Corrected Fuel Model are kept separate."
        )

        note.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 10px;
            }
        """)

        root.addWidget(
            note
        )

        # ====================================================
        # MODEL SELECTOR
        # ====================================================

        model_layout = QHBoxLayout()

        model_label = QLabel(
            "VE MODEL:"
        )

        model_label.setStyleSheet("""
            QLabel {
                color: #ff3030;
                font-weight: bold;
            }
        """)

        self.model_combo = QComboBox()

        self.model_combo.addItems([
            "اصولی VE FINAL • Physical",
            "Fuel Model VE • Lambda Corrected",
            "Estimated VE • Legacy"
        ])

        self.model_combo.currentIndexChanged.connect(
            self.refresh_table
        )

        model_layout.addWidget(
            model_label
        )

        model_layout.addWidget(
            self.model_combo
        )

        model_layout.addStretch()

        root.addLayout(
            model_layout
        )

        self.table = QTableWidget()

        self.table.verticalHeader().setVisible(
            False
        )

        root.addWidget(
            self.table,
            1
        )

        buttons = QHBoxLayout()

        export_button = QPushButton(
            "EXPORT CSV"
        )

        export_button.clicked.connect(
            self.export_csv
        )

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.clicked.connect(
            self.close
        )

        buttons.addWidget(
            export_button
        )

        buttons.addStretch()

        buttons.addWidget(
            close_button
        )

        root.addLayout(
            buttons
        )

        self.refresh_table()

    # ========================================================
    # DATA SELECTION
    # ========================================================

    def selected_data(self):

        index = (
            self.model_combo.currentIndex()
        )

        if index == 0:
            return self.engineering

        if index == 1:
            return self.engineering_corrected

        return self.calculated

    # ========================================================
    # TABLE REFRESH
    # ========================================================

    def refresh_table(self):

        data = self.selected_data()

        rows = len(
            self.maps
        )

        cols = len(
            self.rpms
        )

        self.table.clear()

        self.table.setRowCount(
            rows
        )

        self.table.setColumnCount(
            cols + 1
        )

        headers = [
            "MAP / kPa"
        ]

        for rpm in self.rpms:

            headers.append(
                f"{rpm:.0f}"
            )

        self.table.setHorizontalHeaderLabels(
            headers
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        for r, map_kpa in enumerate(
            self.maps
        ):

            map_item = QTableWidgetItem(
                f"{map_kpa:.1f}"
            )

            map_item.setTextAlignment(
                Qt.AlignCenter
            )

            map_item.setForeground(
                QColor("#ff3030")
            )

            self.table.setItem(
                r,
                0,
                map_item
            )

            for c in range(cols):

                value = float(
                    data[r][c]
                )

                item = QTableWidgetItem(
                    f"{value:.1f}"
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                ratio = clamp(
                    (
                        value - 40.0
                    ) / 70.0,
                    0.0,
                    1.0
                )

                red = int(
                    45
                    + 150 * ratio
                )

                green = int(
                    12
                    + 28 * (
                        1.0 - ratio
                    )
                )

                item.setBackground(
                    QColor(
                        red,
                        green,
                        green
                    )
                )

                item.setForeground(
                    QColor("#ffffff")
                )

                self.table.setItem(
                    r,
                    c + 1,
                    item
                )

    # ========================================================
    # EXPORT
    # ========================================================

    def export_csv(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export VE CSV",
            "aslan_ve_map.csv",
            "CSV Files (*.csv)"
        )

        if not path:
            return

        try:

            data = self.selected_data()

            with open(
                path,
                "w",
                encoding="utf-8-sig"
            ) as file:

                headers = [
                    "MAP_kPa"
                ]

                headers.extend(
                    [
                        f"{rpm:.0f}_RPM"
                        for rpm in self.rpms
                    ]
                )

                file.write(
                    ",".join(headers)
                    + "\n"
                )

                for r, map_kpa in enumerate(
                    self.maps
                ):

                    row = [
                        f"{map_kpa:.1f}"
                    ]

                    row.extend(
                        [
                            f"{data[r][c]:.2f}"
                            for c in range(
                                len(self.rpms)
                            )
                        ]
                    )

                    file.write(
                        ",".join(row)
                        + "\n"
                    )

            QMessageBox.information(
                self,
                "ASLAN TUNER",
                "VE MAP successfully exported."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Export Error",
                str(e)
            )


# ============================================================
# MAIN VE CALCULATOR
# ============================================================

class VECalculator(QDialog):

    def __init__(
        self,
        params=None,
        parent=None
    ):

        super().__init__(
            parent
        )

        if params is None:
            params = {}

        self.params = params

        self.setWindowTitle(
            "ASLAN TUNER • FINAL VE ENGINE"
        )

        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.resize(
            1050,
            760
        )

        self.setStyleSheet("""
            QDialog {
                background-color: #080808;
                color: #eeeeee;
            }

            QWidget {
                background-color: #080808;
                color: #eeeeee;
            }

            QLabel {
                color: #eeeeee;
                background-color: transparent;
            }

            QGroupBox {
                background-color: #0c0c0c;
                color: #ff3030;
                border: 1px solid #292929;
                border-radius: 5px;
                margin-top: 12px;
                padding: 12px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #ff3030;
                background-color: #080808;
            }

            QLineEdit,
            QSpinBox,
            QDoubleSpinBox,
            QComboBox {
                background-color: #111111;
                color: #eeeeee;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 7px;
            }

            QLineEdit:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus,
            QComboBox:focus {
                border: 1px solid #b00000;
            }

            QPushButton {
                background-color: #151515;
                color: #eeeeee;
                border: 1px solid #770000;
                border-radius: 4px;
                padding: 9px 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #8b0000;
            }

            QPushButton:pressed {
                background-color: #5c0000;
            }

            QScrollArea {
                background-color: #080808;
                border: none;
            }

            QScrollBar:vertical {
                background-color: #101010;
                width: 12px;
            }

            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 5px;
            }
        """)

        self.table_window = None

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        main_layout.setSpacing(
            12
        )

        title = QLabel(
            "ASLAN TUNER • FINAL VE ENGINE"
        )

        title.setStyleSheet("""
            QLabel {
                color: #ff2020;
                font-size: 23px;
                font-weight: bold;
            }
        """)

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Final deterministic engineering VE model • "
            "BMEP anchored • Power-density bounded • "
            "Smooth RPM/MAP behavior • "
            "No boost double-counting • "
            "Separate Lambda Fuel Model"
        )

        subtitle.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 11px;
            }
        """)

        main_layout.addWidget(
            subtitle
        )

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        content = QWidget()

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )

        # ====================================================
        # ENGINE PARAMETERS
        # ====================================================

        engine_box = QGroupBox(
            "ENGINE PARAMETERS"
        )

        engine_grid = QGridLayout(
            engine_box
        )

        self.displacement = self.make_double(
            self.params.get(
                "displacement",
                1600.0
            ),
            100,
            20000,
            1
        )

        self.cylinders = self.make_spin(
            self.params.get(
                "cylinders",
                4
            ),
            1,
            16
        )

        self.hp = self.make_double(
            self.params.get(
                "horsepower",
                self.params.get(
                    "hp",
                    80.0
                )
            ),
            1,
            5000,
            1
        )

        self.torque = self.make_double(
            self.params.get(
                "torque",
                110.0
            ),
            1,
            5000,
            1
        )

        self.compression = self.make_double(
            self.params.get(
                "compression",
                9.0
            ),
            3,
            30,
            0.1
        )

        self.idle_rpm = self.make_spin(
            self.params.get(
                "idle_rpm",
                800
            ),
            300,
            5000
        )

        self.rpm_torque = self.make_spin(
            self.params.get(
                "rpm_torque",
                3000
            ),
            500,
            15000
        )

        self.rpm_power = self.make_spin(
            self.params.get(
                "rpm_power",
                5000
            ),
            1000,
            20000
        )

        self.cutoff = self.make_spin(
            self.params.get(
                "cutoff",
                7000
            ),
            1500,
            25000
        )

        self.add_field(
            engine_grid,
            0,
            "Displacement (cc)",
            self.displacement,
            "حجم موتور",
            "حجم موتور یعنی مجموع حجم جابه‌جایی تمام سیلندرها.\n\n"
            "مثلاً موتور ۱.۶ لیتری تقریباً ۱۶۰۰ cc است."
        )

        self.add_field(
            engine_grid,
            1,
            "Cylinders",
            self.cylinders,
            "تعداد سیلندر",
            "تعداد سیلندرهای موتور.\n\n"
            "مثلاً موتور چهارسیلندر = 4."
        )

        self.add_field(
            engine_grid,
            2,
            "Horsepower (HP)",
            self.hp,
            "توان موتور",
            "توان موتور بر حسب HP.\n\n"
            "در مدل نهایی برای جلوگیری از دوباره‌شماری، "
            "HP مستقیماً در VE ضرب نمی‌شود؛ فقط به‌صورت "
            "یک correction بسیار محدود روی breathing capability "
            "اثر دارد."
        )

        self.add_field(
            engine_grid,
            3,
            "Torque (Nm)",
            self.torque,
            "گشتاور موتور",
            "گشتاور اوج موتور بر حسب نیوتن‌متر.\n\n"
            "این مقدار برای محاسبه BMEP و تعیین سطح پایه VE استفاده می‌شود."
        )

        self.add_field(
            engine_grid,
            4,
            "Compression Ratio",
            self.compression,
            "نسبت تراکم",
            "نسبت تراکم هندسی موتور.\n\n"
            "اثر آن در مدل VE عمداً کوچک نگه داشته شده است."
        )

        self.add_field(
            engine_grid,
            5,
            "Idle RPM",
            self.idle_rpm,
            "دور آرام",
            "دور آرام موتور."
        )

        self.add_field(
            engine_grid,
            6,
            "Peak Torque RPM",
            self.rpm_torque,
            "دور اوج گشتاور",
            "دوری که موتور به بیشترین گشتاور می‌رسد."
        )

        self.add_field(
            engine_grid,
            7,
            "Peak Power RPM",
            self.rpm_power,
            "دور اوج توان",
            "دوری که موتور به بیشترین توان می‌رسد."
        )

        self.add_field(
            engine_grid,
            8,
            "RPM Cutoff",
            self.cutoff,
            "محدوده قطع دور",
            "حداکثر دور جدول VE."
        )

        content_layout.addWidget(
            engine_box
        )

        # ====================================================
        # AIR / BOOST
        # ====================================================

        air_box = QGroupBox(
            "AIR / BOOST"
        )

        air_grid = QGridLayout(
            air_box
        )

        self.boost = self.make_double(
            self.params.get(
                "boost",
                0.0
            ),
            0,
            100,
            0.1
        )

        self.baro = self.make_double(
            self.params.get(
                "baro_kpa",
                101.325
            ),
            50,
            120,
            0.1
        )

        self.iat = self.make_double(
            self.params.get(
                "iat_c",
                20.0
            ),
            -40,
            150,
            0.1
        )

        self.engine_type = QComboBox()

        self.engine_type.addItems([
            "Naturally Aspirated",
            "Turbo"
        ])

        current_type = self.params.get(
            "engine_type",
            "Naturally Aspirated"
        )

        index = self.engine_type.findText(
            current_type
        )

        if index >= 0:

            self.engine_type.setCurrentIndex(
                index
            )

        self.intake_efficiency = self.make_double(
            self.params.get(
                "intake_efficiency",
                90.0
            ),
            50.0,
            110.0,
            1.0
        )

        self.exhaust_efficiency = self.make_double(
            self.params.get(
                "exhaust_efficiency",
                90.0
            ),
            50.0,
            110.0,
            1.0
        )

        self.add_field(
            air_grid,
            0,
            "Boost (PSI)",
            self.boost,
            "فشار بوست",
            "بوست برای ساخت MAP مطلق استفاده می‌شود.\n\n"
            "بوست مستقیماً به‌عنوان یک multiplier بزرگ وارد VE نمی‌شود."
        )

        self.add_field(
            air_grid,
            1,
            "Barometric (kPa)",
            self.baro,
            "فشار جو",
            "فشار مطلق محیط بر حسب kPa.\n\n"
            "در سطح دریا حدود 101.3 kPa است."
        )

        self.add_field(
            air_grid,
            2,
            "Intake Temp (°C)",
            self.iat,
            "دمای هوای ورودی",
            "دمای هوای ورودی.\n\n"
            "در مدل نهایی مستقیماً VE را ضرب نمی‌کند؛ "
            "دما باید در محاسبه چگالی و جرم هوا استفاده شود."
        )

        self.add_field(
            air_grid,
            3,
            "Engine Type",
            self.engine_type,
            "نوع موتور",
            "Naturally Aspirated یا Turbo."
        )

        self.add_field(
            air_grid,
            4,
            "Intake Efficiency (%)",
            self.intake_efficiency,
            "بازده ورودی",
            "تخمین کیفیت مسیر ورودی هوا.\n\n"
            "90% مقدار خنثی است."
        )

        self.add_field(
            air_grid,
            5,
            "Exhaust Efficiency (%)",
            self.exhaust_efficiency,
            "بازده خروجی",
            "تخمین کیفیت تخلیه دود.\n\n"
            "90% مقدار خنثی است."
        )

        content_layout.addWidget(
            air_box
        )

        # ====================================================
        # LAMBDA
        # ====================================================

        lambda_box = QGroupBox(
            "WIDEBAND LAMBDA • FUEL MODEL CORRECTION"
        )

        lambda_grid = QGridLayout(
            lambda_box
        )

        self.target_lambda = self.make_double(
            self.params.get(
                "target_lambda",
                1.000
            ),
            0.50,
            1.50,
            0.001
        )

        self.actual_lambda = self.make_double(
            self.params.get(
                "actual_lambda",
                1.000
            ),
            0.50,
            1.50,
            0.001
        )

        self.lambda_correction_label = QLabel(
            "+0.00 %"
        )

        self.lambda_correction_label.setStyleSheet("""
            QLabel {
                color: #ff3030;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
        """)

        self.target_lambda.valueChanged.connect(
            self.update_lambda_preview
        )

        self.actual_lambda.valueChanged.connect(
            self.update_lambda_preview
        )

        self.add_field(
            lambda_grid,
            0,
            "Target Lambda",
            self.target_lambda,
            "لامبدای هدف",
            "لامبدایی که می‌خواهید موتور به آن برسد."
        )

        self.add_field(
            lambda_grid,
            1,
            "Actual Lambda",
            self.actual_lambda,
            "لامبدای واقعی",
            "لامبدای اندازه‌گیری‌شده توسط Wideband."
        )

        self.add_field(
            lambda_grid,
            2,
            "Fuel Correction",
            self.lambda_correction_label,
            "تصحیح سوخت",
            "تصحیح مورد نیاز سوخت بر اساس اختلاف Lambda واقعی "
            "و Lambda هدف.\n\n"
            "این مقدار Physical VE را تغییر نمی‌دهد."
        )

        lambda_note = QLabel(
            "Lambda correction is kept separate from Physical VE."
        )

        lambda_note.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 10px;
            }
        """)

        lambda_grid.addWidget(
            lambda_note,
            3,
            0,
            1,
            4
        )

        content_layout.addWidget(
            lambda_box
        )

        # ====================================================
        # MAP GRID
        # ====================================================

        grid_box = QGroupBox(
            "VE MAP GRID"
        )

        grid_layout = QGridLayout(
            grid_box
        )

        self.map_rows = self.make_spin(
            self.params.get(
                "rows",
                16
            ),
            8,
            32
        )

        self.rpm_columns = self.make_spin(
            self.params.get(
                "columns",
                16
            ),
            8,
            32
        )

        self.add_field(
            grid_layout,
            0,
            "MAP Rows",
            self.map_rows,
            "تعداد ردیف MAP",
            "تعداد نقاط محور MAP."
        )

        self.add_field(
            grid_layout,
            1,
            "RPM Columns",
            self.rpm_columns,
            "تعداد ستون RPM",
            "تعداد نقاط محور RPM."
        )

        content_layout.addWidget(
            grid_box
        )

        content_layout.addStretch()

        scroll.setWidget(
            content
        )

        main_layout.addWidget(
            scroll,
            1
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        buttons = QHBoxLayout()

        generate = QPushButton(
            "GENERATE VE"
        )

        generate.setMinimumHeight(
            44
        )

        generate.setStyleSheet("""
            QPushButton {
                background-color: #8b0000;
                border: 1px solid #ff2020;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #b00000;
            }
        """)

        generate.clicked.connect(
            self.generate
        )

        close = QPushButton(
            "CLOSE"
        )

        close.setMinimumHeight(
            44
        )

        close.clicked.connect(
            self.close
        )

        buttons.addWidget(
            generate
        )

        buttons.addWidget(
            close
        )

        main_layout.addLayout(
            buttons
        )

        self.update_lambda_preview()

    # ========================================================
    # WIDGET HELPERS
    # ========================================================

    def make_double(
        self,
        value,
        minimum,
        maximum,
        step
    ):

        widget = QDoubleSpinBox()

        widget.setRange(
            minimum,
            maximum
        )

        widget.setSingleStep(
            step
        )

        widget.setValue(
            float(value)
        )

        if step < 0.01:
            decimals = 3
        elif step < 0.1:
            decimals = 2
        else:
            decimals = 1

        widget.setDecimals(
            decimals
        )

        return widget

    def make_spin(
        self,
        value,
        minimum,
        maximum
    ):

        widget = QSpinBox()

        widget.setRange(
            minimum,
            maximum
        )

        widget.setValue(
            int(value)
        )

        return widget

    def add_field(
        self,
        layout,
        row,
        label,
        widget,
        info_title=None,
        info_text=None
    ):

        label_widget = QLabel(
            label
        )

        label_widget.setStyleSheet("""
            QLabel {
                color: #bbbbbb;
            }
        """)

        base_row = row // 2

        base_col = (
            row % 2
        ) * 4

        layout.addWidget(
            label_widget,
            base_row,
            base_col
        )

        layout.addWidget(
            widget,
            base_row,
            base_col + 1
        )

        if (
            info_title
            and info_text
        ):

            info_button = InfoButton(
                info_title,
                info_text
            )

            layout.addWidget(
                info_button,
                base_row,
                base_col + 2,
                Qt.AlignCenter
            )

    # ========================================================
    # LAMBDA PREVIEW
    # ========================================================

    def update_lambda_preview(self):

        correction = calculate_lambda_correction(
            self.target_lambda.value(),
            self.actual_lambda.value()
        )

        self.lambda_correction_label.setText(
            f"{correction:+.2f} %"
        )

    # ========================================================
    # GENERATE
    # ========================================================

    def generate(self):

        # ----------------------------------------------------
        # BASIC INPUT VALIDATION
        # ----------------------------------------------------

        displacement = (
            self.displacement.value()
        )

        torque = (
            self.torque.value()
        )

        idle = float(
            self.idle_rpm.value()
        )

        rpm_torque = float(
            self.rpm_torque.value()
        )

        rpm_power = float(
            self.rpm_power.value()
        )

        cutoff = float(
            self.cutoff.value()
        )

        if displacement <= 0.0:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "Displacement must be greater than zero."
            )

            return

        if torque <= 0.0:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "Torque must be greater than zero."
            )

            return

        if not (
            idle
            < rpm_torque
            < rpm_power
            < cutoff
        ):

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "RPM order must be:\n\n"
                "Idle RPM < Peak Torque RPM < "
                "Peak Power RPM < Cutoff RPM"
            )

            return

        # ----------------------------------------------------
        # PARAMETERS
        # ----------------------------------------------------

        params = {

            "displacement":
                displacement,

            "cylinders":
                self.cylinders.value(),

            "horsepower":
                self.hp.value(),

            "torque":
                torque,

            "compression":
                self.compression.value(),

            "idle_rpm":
                idle,

            "rpm_torque":
                rpm_torque,

            "rpm_power":
                rpm_power,

            "cutoff":
                cutoff,

            "boost":
                self.boost.value(),

            "baro_kpa":
                self.baro.value(),

            "iat_c":
                self.iat.value(),

            "engine_type":
                self.engine_type.currentText(),

            "intake_efficiency":
                self.intake_efficiency.value(),

            "exhaust_efficiency":
                self.exhaust_efficiency.value(),
        }

        engine = VEEngine(
            params
        )

        # ----------------------------------------------------
        # AXES
        # ----------------------------------------------------

        rows = (
            self.map_rows.value()
        )

        columns = (
            self.rpm_columns.value()
        )

        rpms = build_rpm_axis(
            idle,
            cutoff,
            columns
        )

        maps = build_map_axis(
            self.baro.value(),
            self.boost.value(),
            rows
        )

        # ----------------------------------------------------
        # AXIS VALIDATION
        # ----------------------------------------------------

        if len(rpms) != columns:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "RPM axis could not create the requested "
                f"{columns} unique points."
            )

            return

        if len(maps) != rows:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "MAP axis could not create the requested "
                f"{rows} unique points."
            )

            return

        if len(set(rpms)) != columns:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "RPM axis contains duplicate values."
            )

            return

        if len(set(maps)) != rows:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "MAP axis contains duplicate values."
            )

            return

        # ----------------------------------------------------
        # LAMBDA
        # ----------------------------------------------------

        target_lambda = (
            self.target_lambda.value()
        )

        actual_lambda = (
            self.actual_lambda.value()
        )

        # ----------------------------------------------------
        # MAP GENERATION
        # ----------------------------------------------------

        engineering = []
        engineering_corrected = []

        estimated = []
        estimated_corrected = []

        for map_kpa in maps:

            engineering_row = []
            engineering_corrected_row = []

            estimated_row = []
            estimated_corrected_row = []

            for rpm in rpms:

                (
                    estimated_value,
                    engineering_value
                ) = engine.calculate_both(
                    rpm,
                    map_kpa
                )

                engineering_fuel_value = corrected_ve(
                    engineering_value,
                    target_lambda,
                    actual_lambda
                )

                estimated_fuel_value = corrected_ve(
                    estimated_value,
                    target_lambda,
                    actual_lambda
                )

                engineering_row.append(
                    engineering_value
                )

                engineering_corrected_row.append(
                    engineering_fuel_value
                )

                estimated_row.append(
                    estimated_value
                )

                estimated_corrected_row.append(
                    estimated_fuel_value
                )

            engineering.append(
                engineering_row
            )

            engineering_corrected.append(
                engineering_corrected_row
            )

            estimated.append(
                estimated_row
            )

            estimated_corrected.append(
                estimated_corrected_row
            )

        # ----------------------------------------------------
        # OPEN TABLE
        # ----------------------------------------------------

        self.table_window = VETableWindow(
            rpms=rpms,
            maps=maps,
            calculated=estimated,
            corrected=estimated_corrected,
            target_lambda=target_lambda,
            actual_lambda=actual_lambda,
            engineering=engineering,
            engineering_corrected=engineering_corrected,
            parent=self
        )

        self.table_window.show()
        self.table_window.raise_()
        self.table_window.activateWindow()