# calculators/engine_dyno.py

from math import pi, sqrt, exp, log
from bisect import bisect_left

from ui.topbar import ASLANTopBar

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QScrollArea,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
)

try:
    from ui.topbar import ASLANTopBar
except Exception:
    ASLANTopBar = None


# ============================================================
# ASLAN ENGINE DYNO SIMULATOR
# Engineering Model V1
# ============================================================

HP_PER_KW = 1.34102209
KW_PER_HP = 0.745699872

ATM_PSI = 14.5037738
AIR_DENSITY_STD_LB_FT3 = 0.076474

# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def clamp(value, low, high):
    return max(low, min(high, value))


def lerp(x1, y1, x2, y2, x):
    if x2 == x1:
        return y1
    return y1 + (y2 - y1) * ((x - x1) / (x2 - x1))


def interpolate(xs, ys, x):
    if not xs or not ys:
        return 0.0

    if x <= xs[0]:
        return ys[0]

    if x >= xs[-1]:
        return ys[-1]

    i = bisect_left(xs, x)

    return lerp(
        xs[i - 1],
        ys[i - 1],
        xs[i],
        ys[i],
        x,
    )


# ============================================================
# ENGINE CALCULATIONS
# ============================================================

def displacement_cc(bore_mm, stroke_mm, cylinders):
    bore_m = bore_mm / 1000.0
    stroke_m = stroke_mm / 1000.0

    volume_m3 = (
        pi
        / 4.0
        * bore_m ** 2
        * stroke_m
        * cylinders
    )

    return volume_m3 * 1_000_000.0


def displacement_cid(displacement_cc_value):
    return displacement_cc_value / 16.387064


def torque_from_hp(hp, rpm):
    if rpm <= 0:
        return 0.0

    return hp * 9549.297 / rpm


def hp_from_torque_nm(torque_nm, rpm):
    if rpm <= 0:
        return 0.0

    return torque_nm * rpm / 9549.297


def pressure_ratio(baro_psi, boost_psi):
    if baro_psi <= 0:
        return 1.0

    return (baro_psi + boost_psi) / baro_psi


def intake_temperature_after_intercooler(
    ambient_c,
    compressor_out_c,
    intercooler_efficiency,
):
    efficiency = clamp(intercooler_efficiency / 100.0, 0.0, 1.0)

    return (
        compressor_out_c
        - efficiency
        * (compressor_out_c - ambient_c)
    )


def compressor_temperature(
    ambient_c,
    pressure_ratio_value,
    compressor_efficiency,
):
    """
    Ideal-gas compressor temperature estimate.

    T2/T1 =
        1 + (PR^((gamma-1)/gamma)-1) / eta
    """

    gamma = 1.4

    t1 = ambient_c + 273.15

    eta = clamp(
        compressor_efficiency / 100.0,
        0.30,
        0.95,
    )

    ratio_term = (
        pressure_ratio_value ** ((gamma - 1.0) / gamma)
        - 1.0
    )

    t2 = t1 * (
        1.0 + ratio_term / eta
    )

    return t2 - 273.15


def air_density_lb_ft3(
    pressure_psi,
    temperature_c,
):
    """
    Ideal-gas air-density estimate.
    """

    pressure_pa = pressure_psi * 6894.757293

    temperature_k = temperature_c + 273.15

    R = 287.058

    density_kg_m3 = (
        pressure_pa
        / (R * temperature_k)
    )

    return density_kg_m3 * 0.06242796


def theoretical_engine_cfm(
    displacement_cid_value,
    rpm,
    ve,
):
    """
    Standard 4-stroke airflow relation.
    """

    ve_decimal = ve / 100.0

    return (
        displacement_cid_value
        * rpm
        * ve_decimal
        / 3456.0
    )


# ============================================================
# CAM MODEL
# ============================================================

def cam_center_from_events(
    ivo,
    ivc,
    evo,
    evc,
):
    """
    Approximate intake/exhaust centerlines.

    IVO = BTDC
    IVC = ABDC
    EVO = BBDC
    EVC = ATDC
    """

    intake_duration = 180.0 + ivo + ivc
    exhaust_duration = 180.0 + evo + evc

    intake_center = (
        180.0
        + ivc
        - intake_duration / 2.0
    )

    exhaust_center = (
        180.0
        + evo
        - exhaust_duration / 2.0
    )

    return (
        intake_duration,
        exhaust_duration,
        intake_center,
        exhaust_center,
    )


def cam_rpm_center(
    intake_duration,
    exhaust_duration,
):
    """
    Empirical center-RPM model.

    This is intentionally adjustable rather than
    pretending to reproduce a proprietary simulator.
    """

    average_duration = (
        intake_duration
        + exhaust_duration
    ) / 2.0

    delta = average_duration - 200.0

    rpm = (
        2200.0
        + 18.0 * delta
        + 0.025 * delta * delta
    )

    return clamp(
        rpm,
        1500.0,
        9000.0,
    )


def cam_efficiency(
    rpm,
    cam_peak_rpm,
    intake_duration,
    exhaust_duration,
    lsa,
):
    """
    Smooth cam efficiency envelope.
    """

    if cam_peak_rpm <= 0:
        return 1.0

    spread = (
        0.42
        + max(
            0.0,
            (intake_duration + exhaust_duration - 400.0)
            / 1000.0
        )
    )

    spread = clamp(
        spread,
        0.38,
        0.72,
    )

    x = (
        rpm - cam_peak_rpm
    ) / (
        cam_peak_rpm * spread
    )

    envelope = exp(
        -0.5 * x * x
    )

    # Wider LSA generally broadens the torque curve.
    lsa_factor = clamp(
        1.0
        + (lsa - 108.0) * 0.002,
        0.96,
        1.04,
    )

    return clamp(
        0.72
        + 0.28 * envelope * lsa_factor,
        0.60,
        1.05,
    )


# ============================================================
# HEAD FLOW MODEL
# ============================================================

def valve_area_mm2(diameter_mm):
    return pi * diameter_mm ** 2 / 4.0


def flow_capacity_factor(
    intake_valve_mm,
    exhaust_valve_mm,
    rpm,
    displacement_cc_value,
):
    """
    Approximate cylinder-head flow capacity.

    This does not replace a real flowbench table.
    """

    intake_area = valve_area_mm2(
        intake_valve_mm
    )

    exhaust_area = valve_area_mm2(
        exhaust_valve_mm
    )

    total_area = (
        intake_area
        + exhaust_area * 0.65
    )

    specific_area = (
        total_area
        / max(displacement_cc_value, 1.0)
        * 1000.0
    )

    rpm_factor = clamp(
        specific_area * 0.95,
        0.70,
        1.12,
    )

    rpm_penalty = max(
        0.0,
        rpm - 6500.0,
    ) / 7000.0

    return clamp(
        rpm_factor
        * (1.0 - 0.20 * rpm_penalty),
        0.55,
        1.15,
    )


# ============================================================
# THROTTLE MODEL
# ============================================================

def throttle_capacity_factor(
    throttle_diameter_mm,
    cylinders,
    rpm,
    displacement_cc_value,
):
    if throttle_diameter_mm <= 0:
        return 0.50

    area = (
        pi
        * throttle_diameter_mm ** 2
        / 4.0
    )

    effective_area = (
        area
        * max(cylinders, 1)
    )

    demand_index = (
        displacement_cc_value
        * rpm
        / 120000000.0
    )

    ratio = (
        effective_area
        / max(demand_index, 0.01)
    )

    factor = 0.70 + 0.30 * (
        ratio / (ratio + 1.0)
    )

    return clamp(
        factor,
        0.72,
        1.05,
    )


# ============================================================
# EXHAUST MODEL
# ============================================================

def header_tuned_rpm(
    primary_length_in,
    exhaust_valve_opening_bbdc,
):
    """
    Practical empirical header tuning relation.

    RPM = 850*(360-EVO)/(L+3)
    """

    if primary_length_in <= 0:
        return 0.0

    denominator = (
        primary_length_in + 3.0
    )

    return (
        850.0
        * (360.0 - exhaust_valve_opening_bbdc)
        / denominator
    )


def header_effect(
    rpm,
    tuned_rpm,
    diameter_mm,
):
    if tuned_rpm <= 0:
        return 1.0

    x = (
        rpm - tuned_rpm
    ) / max(
        tuned_rpm * 0.28,
        1.0,
    )

    wave = exp(
        -0.5 * x * x
    )

    diameter_factor = clamp(
        diameter_mm / 38.0,
        0.75,
        1.30,
    )

    return clamp(
        0.90
        + 0.12 * wave
        + 0.03 * diameter_factor,
        0.82,
        1.08,
    )


# ============================================================
# FRICTION MODEL
# ============================================================

def fmep_psi(
    rpm,
    displacement_cc_value,
    compression_ratio,
):
    """
    Simplified friction mean effective pressure model.

    FMEP rises with RPM and compression.
    """

    rpm_k = rpm / 1000.0

    base = (
        2.2
        + 0.75 * rpm_k
        + 0.085 * rpm_k ** 2
    )

    compression_penalty = max(
        0.0,
        compression_ratio - 9.0,
    ) * 0.08

    return base + compression_penalty


def torque_from_bmep(
    bmep_psi,
    displacement_cid_value,
):
    """
    4-stroke BMEP relation.

    Torque(lb-ft) =
        BMEP(psi) * CID / (150.8)
    """

    return (
        bmep_psi
        * displacement_cid_value
        / 150.8
    )


# ============================================================
# ENGINE SIMULATION
# ============================================================

def simulate_engine(data):
    bore = data["bore"]
    stroke = data["stroke"]
    cylinders = data["cylinders"]

    displacement = displacement_cc(
        bore,
        stroke,
        cylinders,
    )

    cid = displacement_cid(
        displacement
    )

    compression = data["compression"]

    baro = data["baro"]
    boost = data["boost"]

    engine_type = data["engine_type"]

    ambient_c = data["ambient"]

    intercooler_eff = data[
        "intercooler_efficiency"
    ]

    compressor_eff = data[
        "compressor_efficiency"
    ]

    throttle = data[
        "throttle_diameter"
    ]

    intake_valve = data[
        "intake_valve"
    ]

    exhaust_valve = data[
        "exhaust_valve"
    ]

    intake_duration = data[
        "intake_duration"
    ]

    exhaust_duration = data[
        "exhaust_duration"
    ]

    intake_lift = data[
        "intake_lift"
    ]

    exhaust_lift = data[
        "exhaust_lift"
    ]

    lsa = data[
        "lsa"
    ]

    ivo = data[
        "ivo"
    ]

    ivc = data[
        "ivc"
    ]

    evo = data[
        "evo"
    ]

    evc = data[
        "evc"
    ]

    header_diameter = data[
        "header_diameter"
    ]

    header_length = data[
        "header_length"
    ]

    exhaust_diameter = data[
        "exhaust_diameter"
    ]

    base_ve = data[
        "base_ve"
    ]

    stoich = data[
        "stoich"
    ]

    lambda_target = data[
        "lambda"
    ]

    bsfc = data[
        "bsfc"
    ]

    mechanical_efficiency = clamp(
        data["mechanical_efficiency"] / 100.0,
        0.70,
        0.99,
    )

    rpm_start = data[
        "rpm_start"
    ]

    rpm_end = data[
        "rpm_end"
    ]

    rpm_step = data[
        "rpm_step"
    ]

    # --------------------------------------------------------
    # Cam peak RPM
    # --------------------------------------------------------

    cam_peak = cam_rpm_center(
        intake_duration,
        exhaust_duration,
    )

    # If user supplied explicit peak RPM,
    # blend it into the cam prediction.
    if data.get("cam_peak_rpm", 0) > 0:
        cam_peak = (
            cam_peak * 0.40
            + data["cam_peak_rpm"] * 0.60
        )

    results = []

    for rpm in range(
        rpm_start,
        rpm_end + 1,
        rpm_step,
    ):

        # ----------------------------------------------------
        # Cam effect
        # ----------------------------------------------------

        cam_factor = cam_efficiency(
            rpm,
            cam_peak,
            intake_duration,
            exhaust_duration,
            lsa,
        )

        # ----------------------------------------------------
        # Head flow
        # ----------------------------------------------------

        head_factor = flow_capacity_factor(
            intake_valve,
            exhaust_valve,
            rpm,
            displacement,
        )

        # Lift influence
        lift_factor = clamp(
            (
                intake_lift
                + exhaust_lift
            ) / 20.0,
            0.80,
            1.12,
        )

        head_factor *= lift_factor

        # ----------------------------------------------------
        # RPM VE shape
        # ----------------------------------------------------

        # Broad naturally aspirated VE envelope
        rpm_relative = (
            rpm - cam_peak
        ) / max(
            cam_peak * 0.48,
            1.0,
        )

        rpm_shape = exp(
            -0.5
            * rpm_relative
            * rpm_relative
        )

        ve = (
            base_ve
            * (
                0.72
                + 0.28 * rpm_shape
            )
        )

        # Cam
        ve *= (
            0.90
            + 0.18 * cam_factor
        )

        # Head
        ve *= head_factor

        # Throttle
        ve *= throttle_capacity_factor(
            throttle,
            cylinders,
            rpm,
            displacement,
        )

        # Exhaust
        tuned_rpm = header_tuned_rpm(
            header_length,
            evo,
        )

        ve *= header_effect(
            rpm,
            tuned_rpm,
            header_diameter,
        )

        # ----------------------------------------------------
        # Compression effect
        # ----------------------------------------------------

        compression_factor = clamp(
            1.0
            + (
                compression - 9.0
            ) * 0.018,
            0.88,
            1.10,
        )

        ve *= compression_factor

        # ----------------------------------------------------
        # Forced induction
        # ----------------------------------------------------

        pr = pressure_ratio(
            baro,
            boost,
        )

        if engine_type == "Turbo":

            compressor_out = compressor_temperature(
                ambient_c,
                pr,
                compressor_eff,
            )

            intake_temp = (
                intake_temperature_after_intercooler(
                    ambient_c,
                    compressor_out,
                    intercooler_eff,
                )
            )

            pressure_multiplier = pr

        else:

            intake_temp = ambient_c
            pressure_multiplier = 1.0

        # Density ratio compared with standard air
        intake_pressure = (
            baro + boost
            if engine_type == "Turbo"
            else baro
        )

        actual_density = air_density_lb_ft3(
            intake_pressure,
            intake_temp,
        )

        density_ratio = (
            actual_density
            / AIR_DENSITY_STD_LB_FT3
        )

        # ----------------------------------------------------
        # Final VE
        # ----------------------------------------------------

        ve = clamp(
            ve * pressure_multiplier,
            35.0,
            280.0,
        )

        # ----------------------------------------------------
        # Airflow
        # ----------------------------------------------------

        cfm_standard = theoretical_engine_cfm(
            cid,
            rpm,
            ve,
        )

        actual_cfm = (
            cfm_standard
            * density_ratio
        )

        # ----------------------------------------------------
        # Fuel
        # ----------------------------------------------------

        actual_afr = (
            stoich
            * lambda_target
        )

        if actual_afr <= 0:
            actual_afr = 14.7

        air_lb_min = (
            actual_cfm
            * AIR_DENSITY_STD_LB_FT3
        )

        fuel_lb_hr = (
            air_lb_min
            * 60.0
            / actual_afr
        )

        # ----------------------------------------------------
        # Indicated power from BSFC
        # ----------------------------------------------------

        if bsfc <= 0:
            bsfc = 0.50

        indicated_hp = (
            fuel_lb_hr
            / bsfc
        )

        # Mechanical loss
        friction_loss = fmep_psi(
            rpm,
            displacement,
            compression,
        )

        # Convert FMEP loss into approximate torque loss
        friction_torque = torque_from_bmep(
            friction_loss,
            cid,
        )

        gross_torque = torque_from_hp(
            indicated_hp,
            rpm,
        )

        brake_torque = (
            gross_torque
            * mechanical_efficiency
            - friction_torque * 0.35
        )

        brake_torque = max(
            0.0,
            brake_torque,
        )

        brake_hp = hp_from_torque_nm(
            brake_torque,
            rpm,
        )

        # ----------------------------------------------------
        # Torque shaping
        # ----------------------------------------------------

        # Cam/flow response
        torque_shape = (
            0.88
            + 0.12 * cam_factor
        )

        brake_torque *= torque_shape

        brake_hp = hp_from_torque_nm(
            brake_torque,
            rpm,
        )

        # ----------------------------------------------------
        # IMEP / BMEP
        # ----------------------------------------------------

        # Torque Nm -> BMEP Pa
        displacement_m3 = (
            displacement / 1_000_000.0
        )

        bmep_pa = (
            brake_torque
            * 4.0
            * pi
            / max(
                displacement_m3,
                1e-9,
            )
        )

        bmep_bar = (
            bmep_pa / 100000.0
        )

        fmep_bar = (
            friction_loss
            * 0.0689476
        )

        imep_bar = (
            bmep_bar
            + fmep_bar
        )

        results.append({
            "rpm": rpm,
            "ve": ve,
            "cfm": actual_cfm,
            "air_lb_min": air_lb_min,
            "fuel_lb_hr": fuel_lb_hr,
            "hp": brake_hp,
            "torque_nm": brake_torque,
            "torque_lbft": brake_torque * 0.737562,
            "map_psi": intake_pressure,
            "intake_temp": intake_temp,
            "imep_bar": imep_bar,
            "bmep_bar": bmep_bar,
            "fmep_bar": fmep_bar,
        })

    # --------------------------------------------------------
    # Peak values
    # --------------------------------------------------------

    if results:

        peak_hp = max(
            results,
            key=lambda r: r["hp"],
        )

        peak_torque = max(
            results,
            key=lambda r: r["torque_nm"],
        )

    else:

        peak_hp = None
        peak_torque = None

    return {
        "displacement_cc": displacement,
        "displacement_cid": cid,
        "cam_peak_rpm": cam_peak,
        "tuned_header_rpm": tuned_rpm,
        "results": results,
        "peak_hp": peak_hp,
        "peak_torque": peak_torque,
    }


# ============================================================
# UI HELPERS
# ============================================================

STYLE = """
QDialog, QWidget {
    background-color: #171717;
    color: #eeeeee;
    font-family: Segoe UI;
}

QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: bold;
    color: #ff3030;
}

QLineEdit,
QDoubleSpinBox,
QSpinBox,
QComboBox {
    background-color: #222222;
    border: 1px solid #444444;
    border-radius: 5px;
    padding: 6px;
    color: #ffffff;
    min-height: 28px;
}

QLineEdit:focus,
QDoubleSpinBox:focus,
QSpinBox:focus,
QComboBox:focus {
    border: 1px solid #e00000;
}

QPushButton {
    background-color: #202020;
    border: 1px solid #8d0000;
    border-radius: 6px;
    padding: 8px 14px;
    color: white;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #8d0000;
}

QPushButton:pressed {
    background-color: #d00000;
}

QTableWidget {
    background-color: #121212;
    alternate-background-color: #1c1c1c;
    gridline-color: #3a3a3a;
    color: #eeeeee;
}

QHeaderView::section {
    background-color: #250000;
    color: #ff4444;
    padding: 6px;
    border: 1px solid #400000;
}
"""


class ResultCard(QFrame):

    def __init__(
        self,
        title,
        value,
        unit,
        parent=None,
    ):
        super().__init__(parent)

        self.setStyleSheet("""
        QFrame {
            background-color: #1e1e1e;
            border: 1px solid #550000;
            border-radius: 8px;
        }
        """)

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color:#999999;"
        )

        value_label = QLabel(
            f"{value} {unit}"
        )

        value_label.setStyleSheet(
            """
            color:#ff3030;
            font-size:22px;
            font-weight:bold;
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class EngineDynoSimulator(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_result = None

        self.setWindowTitle(
            "ASLAN ENGINE DYNO SIMULATOR"
        )

        self.resize(
            1250,
            850,
        )

        self.setStyleSheet(
            STYLE
        )

        self._build_ui()

    # --------------------------------------------------------

    def field(
        self,
        layout,
        row,
        label,
        value,
        minimum=0.0,
        maximum=100000.0,
        decimals=2,
    ):

        lbl = QLabel(label)

        box = QDoubleSpinBox()

        box.setRange(
            minimum,
            maximum,
        )

        box.setDecimals(
            decimals
        )

        box.setValue(
            value
        )

        layout.addWidget(
            lbl,
            row,
            0,
        )

        layout.addWidget(
            box,
            row,
            1,
        )

        return box

    # --------------------------------------------------------

    def _build_ui(self):

        root = QVBoxLayout(
            self
        )

        title = QLabel(
            "ASLAN ENGINE DYNO SIMULATOR"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                color:#ff2020;
                font-size:26px;
                font-weight:bold;
                padding:12px;
            }
            """
        )

        root.addWidget(
            title
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        container = QWidget()

        main = QVBoxLayout(
            container
        )

        # ====================================================
        # ENGINE
        # ====================================================

        engine_box = QGroupBox(
            "ENGINE / SHORT BLOCK"
        )

        engine_grid = QGridLayout(
            engine_box
        )

        self.bore = self.field(
            engine_grid,
            0,
            "Bore (mm)",
            86.0,
            20,
            200,
        )

        self.stroke = self.field(
            engine_grid,
            1,
            "Stroke (mm)",
            86.0,
            20,
            300,
        )

        self.cylinders = self.field(
            engine_grid,
            2,
            "Cylinders",
            4,
            1,
            16,
            0,
        )

        self.compression = self.field(
            engine_grid,
            3,
            "Compression Ratio",
            9.5,
            4,
            30,
        )

        self.rpm_start = self.field(
            engine_grid,
            4,
            "RPM Start",
            1000,
            500,
            20000,
            0,
        )

        self.rpm_end = self.field(
            engine_grid,
            5,
            "RPM End",
            7000,
            1000,
            25000,
            0,
        )

        self.rpm_step = self.field(
            engine_grid,
            6,
            "RPM Step",
            250,
            25,
            1000,
            0,
        )

        main.addWidget(
            engine_box
        )

        # ====================================================
        # HEAD
        # ====================================================

        head_box = QGroupBox(
            "CYLINDER HEAD"
        )

        head_grid = QGridLayout(
            head_box
        )

        self.intake_valve = self.field(
            head_grid,
            0,
            "Intake Valve (mm)",
            43.0,
            10,
            100,
        )

        self.exhaust_valve = self.field(
            head_grid,
            1,
            "Exhaust Valve (mm)",
            36.0,
            10,
            100,
        )

        self.base_ve = self.field(
            head_grid,
            2,
            "Base VE (%)",
            85.0,
            30,
            150,
        )

        main.addWidget(
            head_box
        )

        # ====================================================
        # CAM
        # ====================================================

        cam_box = QGroupBox(
            "CAMSHAFT"
        )

        cam_grid = QGridLayout(
            cam_box
        )

        self.intake_duration = self.field(
            cam_grid,
            0,
            "Intake Duration (°)",
            220,
            150,
            360,
        )

        self.exhaust_duration = self.field(
            cam_grid,
            1,
            "Exhaust Duration (°)",
            220,
            150,
            360,
        )

        self.intake_lift = self.field(
            cam_grid,
            2,
            "Intake Lift (mm)",
            10.0,
            2,
            30,
        )

        self.exhaust_lift = self.field(
            cam_grid,
            3,
            "Exhaust Lift (mm)",
            9.0,
            2,
            30,
        )

        self.lsa = self.field(
            cam_grid,
            4,
            "LSA (°)",
            110,
            90,
            130,
        )

        self.ivo = self.field(
            cam_grid,
            5,
            "IVO BTDC (°)",
            10,
            0,
            80,
        )

        self.ivc = self.field(
            cam_grid,
            6,
            "IVC ABDC (°)",
            50,
            0,
            100,
        )

        self.evo = self.field(
            cam_grid,
            7,
            "EVO BBDC (°)",
            55,
            0,
            120,
        )

        self.evc = self.field(
            cam_grid,
            8,
            "EVC ATDC (°)",
            10,
            0,
            80,
        )

        self.cam_peak = self.field(
            cam_grid,
            9,
            "Cam Peak RPM",
            0,
            0,
            15000,
            0,
        )

        main.addWidget(
            cam_box
        )

        # ====================================================
        # INDUCTION
        # ====================================================

        induction_box = QGroupBox(
            "INDUCTION / THROTTLE"
        )

        induction_grid = QGridLayout(
            induction_box
        )

        self.engine_type = QComboBox()

        self.engine_type.addItems(
            [
                "Naturally Aspirated",
                "Turbo",
            ]
        )

        induction_grid.addWidget(
            QLabel("Engine Type"),
            0,
            0,
        )

        induction_grid.addWidget(
            self.engine_type,
            0,
            1,
        )

        self.throttle = self.field(
            induction_grid,
            1,
            "Throttle Diameter (mm)",
            52,
            20,
            150,
        )

        self.boost = self.field(
            induction_grid,
            2,
            "Boost (PSI)",
            0,
            0,
            100,
        )

        self.baro = self.field(
            induction_grid,
            3,
            "Barometric Pressure (PSI)",
            14.7,
            8,
            18,
        )

        self.ambient = self.field(
            induction_grid,
            4,
            "Ambient Temperature (°C)",
            25,
            -30,
            80,
        )

        self.intercooler = self.field(
            induction_grid,
            5,
            "Intercooler Efficiency (%)",
            70,
            0,
            100,
        )

        self.compressor_eff = self.field(
            induction_grid,
            6,
            "Compressor Efficiency (%)",
            72,
            40,
            90,
        )

        main.addWidget(
            induction_box
        )

        # ====================================================
        # EXHAUST
        # ====================================================

        exhaust_box = QGroupBox(
            "EXHAUST / HEADER"
        )

        exhaust_grid = QGridLayout(
            exhaust_box
        )

        self.header_diameter = self.field(
            exhaust_grid,
            0,
            "Primary Diameter (mm)",
            38,
            20,
            100,
        )

        self.header_length = self.field(
            exhaust_grid,
            1,
            "Primary Length (inch)",
            28,
            10,
            80,
        )

        self.exhaust_diameter = self.field(
            exhaust_grid,
            2,
            "Exhaust Diameter (mm)",
            55,
            25,
            150,
        )

        main.addWidget(
            exhaust_box
        )

        # ====================================================
        # FUEL
        # ====================================================

        fuel_box = QGroupBox(
            "FUEL / COMBUSTION"
        )

        fuel_grid = QGridLayout(
            fuel_box
        )

        self.stoich = self.field(
            fuel_grid,
            0,
            "Stoich AFR",
            14.7,
            5,
            20,
        )

        self.lambda_target = self.field(
            fuel_grid,
            1,
            "Lambda Target",
            0.90,
            0.60,
            1.30,
        )

        self.bsfc = self.field(
            fuel_grid,
            2,
            "BSFC (lb/hp-hr)",
            0.50,
            0.25,
            2.0,
        )

        self.mechanical_efficiency = self.field(
            fuel_grid,
            3,
            "Mechanical Efficiency (%)",
            88,
            70,
            99,
        )

        main.addWidget(
            fuel_box
        )

        # ====================================================
        # RUN
        # ====================================================

        self.run_button = QPushButton(
            "▶  RUN DYNO SIMULATION"
        )

        self.run_button.setMinimumHeight(
            50
        )

        self.run_button.clicked.connect(
            self.run_simulation
        )

        main.addWidget(
            self.run_button
        )

        scroll.setWidget(
            container
        )

        root.addWidget(
            scroll
        )

    # --------------------------------------------------------

    def collect_data(self):

        engine_type = (
            "Turbo"
            if self.engine_type.currentText()
            == "Turbo"
            else "NA"
        )

        return {
            "bore": self.bore.value(),
            "stroke": self.stroke.value(),
            "cylinders": int(
                self.cylinders.value()
            ),

            "compression": self.compression.value(),

            "rpm_start": int(
                self.rpm_start.value()
            ),

            "rpm_end": int(
                self.rpm_end.value()
            ),

            "rpm_step": int(
                self.rpm_step.value()
            ),

            "intake_valve":
                self.intake_valve.value(),

            "exhaust_valve":
                self.exhaust_valve.value(),

            "base_ve":
                self.base_ve.value(),

            "intake_duration":
                self.intake_duration.value(),

            "exhaust_duration":
                self.exhaust_duration.value(),

            "intake_lift":
                self.intake_lift.value(),

            "exhaust_lift":
                self.exhaust_lift.value(),

            "lsa":
                self.lsa.value(),

            "ivo":
                self.ivo.value(),

            "ivc":
                self.ivc.value(),

            "evo":
                self.evo.value(),

            "evc":
                self.evc.value(),

            "cam_peak_rpm":
                self.cam_peak.value(),

            "engine_type":
                engine_type,

            "throttle_diameter":
                self.throttle.value(),

            "boost":
                self.boost.value(),

            "baro":
                self.baro.value(),

            "ambient":
                self.ambient.value(),

            "intercooler_efficiency":
                self.intercooler.value(),

            "compressor_efficiency":
                self.compressor_eff.value(),

            "header_diameter":
                self.header_diameter.value(),

            "header_length":
                self.header_length.value(),

            "exhaust_diameter":
                self.exhaust_diameter.value(),

            "stoich":
                self.stoich.value(),

            "lambda":
                self.lambda_target.value(),

            "bsfc":
                self.bsfc.value(),

            "mechanical_efficiency":
                self.mechanical_efficiency.value(),
        }

    # --------------------------------------------------------

    def run_simulation(self):

        try:

            data = self.collect_data()

            if data["rpm_end"] <= data["rpm_start"]:
                raise ValueError(
                    "RPM End must be greater than RPM Start."
                )

            result = simulate_engine(
                data
            )

            self.last_result = result
            self.show_results(
                result
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Simulation Error",
                str(exc),
            )

    # --------------------------------------------------------

    def show_results(self, result):

        dialog = QDialog(
            self
        )

        dialog.setWindowTitle(
            "ASLAN DYNO RESULTS"
        )

        dialog.resize(
            1250,
            800,
        )

        dialog.setStyleSheet(
            STYLE
        )

        layout = QVBoxLayout(
            dialog
        )

        title = QLabel(
            "ASLAN ENGINE DYNO RESULTS"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                color:#ff3030;
                font-size:25px;
                font-weight:bold;
            }
            """
        )

        layout.addWidget(
            title
        )

        peak_hp = result[
            "peak_hp"
        ]

        peak_torque = result[
            "peak_torque"
        ]

        cards = QHBoxLayout()

        if peak_hp:

            cards.addWidget(
                ResultCard(
                    "PEAK HORSEPOWER",
                    f'{peak_hp["hp"]:.1f}',
                    f'HP @ {peak_hp["rpm"]} RPM',
                )
            )

        if peak_torque:

            cards.addWidget(
                ResultCard(
                    "PEAK TORQUE",
                    f'{peak_torque["torque_nm"]:.1f}',
                    f'Nm @ {peak_torque["rpm"]} RPM',
                )
            )

        cards.addWidget(
            ResultCard(
                "DISPLACEMENT",
                f'{result["displacement_cc"]:.0f}',
                "cc",
            )
        )

        cards.addWidget(
            ResultCard(
                "CAM CENTER",
                f'{result["cam_peak_rpm"]:.0f}',
                "RPM",
            )
        )

        layout.addLayout(
            cards
        )

        table = QTableWidget()

        columns = [
            "RPM",
            "HP",
            "Torque Nm",
            "Torque lb-ft",
            "VE %",
            "Air CFM",
            "Fuel lb/hr",
            "MAP PSI",
            "IAT °C",
            "IMEP bar",
            "BMEP bar",
            "FMEP bar",
        ]

        table.setColumnCount(
            len(columns)
        )

        table.setHorizontalHeaderLabels(
            columns
        )

        rows = result[
            "results"
        ]

        table.setRowCount(
            len(rows)
        )

        for r, item in enumerate(rows):

            values = [
                item["rpm"],
                f'{item["hp"]:.2f}',
                f'{item["torque_nm"]:.2f}',
                f'{item["torque_lbft"]:.2f}',
                f'{item["ve"]:.2f}',
                f'{item["cfm"]:.2f}',
                f'{item["fuel_lb_hr"]:.2f}',
                f'{item["map_psi"]:.2f}',
                f'{item["intake_temp"]:.1f}',
                f'{item["imep_bar"]:.2f}',
                f'{item["bmep_bar"]:.2f}',
                f'{item["fmep_bar"]:.2f}',
            ]

            for c, value in enumerate(values):

                table.setItem(
                    r,
                    c,
                    QTableWidgetItem(
                        str(value)
                    ),
                )

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        layout.addWidget(
            table
        )

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addWidget(
            close_button
        )

        dialog.exec()