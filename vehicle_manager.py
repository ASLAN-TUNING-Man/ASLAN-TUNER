
import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

# These are engineering-oriented baseline specifications. They are deliberately
# kept separate from calculator formulas so a vehicle profile only supplies
# inputs; it never changes a calculator's math.
VEHICLES = {
    "RD.i": {
        "display_name": "Peugeot RD.i",
        "engine_name": "Paykan / Avenger 1.6",
        "engine_code": "Hillman/Avenger-derived",
        "displacement": 1599.0, "bore": 87.35, "stroke": 66.7,
        "cylinders": 4, "compression": 9.5, "power": 74.0,
        "power_rpm": 5000.0, "torque": 135.0, "torque_rpm": 3000.0,
        "idle_rpm": 850.0, "redline_rpm": 5500.0, "boost": 0.0,
        "ve": 78.0, "iat": 20.0, "baro": 101.325,
        "throttle": 50.0, "injector_count": 4, "injector_flow": 180.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "Baseline assembled from published RD/ROA and Avenger/Paykan engine data.",
    },
    "ROA": {
        "display_name": "Peugeot ROA",
        "engine_name": "1.7 CNG / Paykan-derived",
        "engine_code": "ROA 1700",
        "displacement": 1697.0, "bore": 87.35, "stroke": 66.7,
        "cylinders": 4, "compression": 9.5, "power": 83.0,
        "power_rpm": 5000.0, "torque": 135.0, "torque_rpm": 3000.0,
        "idle_rpm": 850.0, "redline_rpm": 5500.0, "boost": 0.0,
        "ve": 78.0, "iat": 20.0, "baro": 101.325,
        "throttle": 50.0, "injector_count": 4, "injector_flow": 180.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "CNG / Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "Published ROA specifications list approximately 1,697 cc, 9.5:1 compression and 61 kW at 5,000 rpm.",
    },
    "405": {
        "display_name": "Peugeot 405 GLX",
        "engine_name": "XU7JP/L3",
        "engine_code": "XU7JP/L3",
        "displacement": 1761.0, "bore": 83.0, "stroke": 81.4,
        "cylinders": 4, "compression": 9.25, "power": 100.0,
        "power_rpm": 6000.0, "torque": 153.0, "torque_rpm": 3000.0,
        "idle_rpm": 850.0, "redline_rpm": 6500.0, "boost": 0.0,
        "ve": 82.0, "iat": 20.0, "baro": 101.325,
        "throttle": 50.0, "injector_count": 4, "injector_flow": 200.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "XU7 published data: 1,761 cc, 83 x 81.4 mm; output varies by market/version.",
    },
    "206/2": {
        "display_name": "Peugeot 206 1.4",
        "engine_name": "TU3JP",
        "engine_code": "TU3JP",
        "displacement": 1360.0, "bore": 75.0, "stroke": 77.0,
        "cylinders": 4, "compression": 10.2, "power": 75.0,
        "power_rpm": 5500.0, "torque": 120.0, "torque_rpm": 3400.0,
        "idle_rpm": 850.0, "redline_rpm": 6500.0, "boost": 0.0,
        "ve": 80.0, "iat": 20.0, "baro": 101.325,
        "throttle": 45.0, "injector_count": 4, "injector_flow": 160.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "TU3 family published data: 1,360 cc, 75 x 77 mm and approximately 10.2:1 for the TU3J variants.",
    },
    "206/5": {
        "display_name": "Peugeot 206 1.6 16V",
        "engine_name": "TU5JP4 / NFU",
        "engine_code": "NFU",
        "displacement": 1587.0, "bore": 78.5, "stroke": 82.0,
        "cylinders": 4, "compression": 10.8, "power": 110.0,
        "power_rpm": 6600.0, "torque": 145.0, "torque_rpm": 5200.0,
        "idle_rpm": 850.0, "redline_rpm": 7000.0, "boost": 0.0,
        "ve": 88.0, "iat": 20.0, "baro": 101.325,
        "throttle": 50.0, "injector_count": 4, "injector_flow": 210.0,
        "fuel_pressure": 3.5, "lambda": 0.90, "valves": 16,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "TU5JP4/NFU workshop data: 78.5 x 82 mm, 1,587 cc, 10.8:1 and 110 hp at 6,600 rpm.",
    },
    "PARS": {
        "display_name": "Peugeot Pars",
        "engine_name": "XU7JP/L3",
        "engine_code": "XU7JPL3",
        "displacement": 1761.0, "bore": 83.0, "stroke": 81.4,
        "cylinders": 4, "compression": 9.3, "power": 100.0,
        "power_rpm": 6000.0, "torque": 153.0, "torque_rpm": 3000.0,
        "idle_rpm": 850.0, "redline_rpm": 6500.0, "boost": 0.0,
        "ve": 82.0, "iat": 20.0, "baro": 101.325,
        "throttle": 50.0, "injector_count": 4, "injector_flow": 200.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "IKCO Pars manual data lists XU7JP/L3 at 1,761 cc and 83 x 81.4 mm; compression/output vary by revision.",
    },
    "PRIDE": {
        "display_name": "Saipa Pride",
        "engine_name": "Mazda B3",
        "engine_code": "B3",
        "displacement": 1323.0, "bore": 71.0, "stroke": 83.6,
        "cylinders": 4, "compression": 9.7, "power": 63.0,
        "power_rpm": 5500.0, "torque": 103.3, "torque_rpm": 2800.0,
        "idle_rpm": 850.0, "redline_rpm": 6000.0, "boost": 0.0,
        "ve": 76.0, "iat": 20.0, "baro": 101.325,
        "throttle": 42.0, "injector_count": 4, "injector_flow": 150.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "Saipa family owner's manual: 71 x 83.6 mm, 1,323 cc, 9.7:1, 63 hp @ 5,500 rpm.",
    },
    "PAYKAN": {
        "display_name": "Iran Khodro Paykan",
        "engine_name": "Hillman Hunter 1725",
        "engine_code": "Rootes 1725",
        "displacement": 1725.0, "bore": 81.53, "stroke": 82.87,
        "cylinders": 4, "compression": 9.0, "power": 68.0,
        "power_rpm": 5000.0, "torque": 135.0, "torque_rpm": 3000.0,
        "idle_rpm": 850.0, "redline_rpm": 5500.0, "boost": 0.0,
        "ve": 77.0, "iat": 20.0, "baro": 101.325,
        "throttle": 48.0, "injector_count": 4, "injector_flow": 170.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 8,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "source_note": "Paykan/Hillman Hunter published data and piston catalogues identify the 1,725 cc four-cylinder family.",
    },
}

CUSTOM_KEY = "CUSTOM ENGINE"


def blank_custom():
    return {
        "display_name": "CUSTOM ENGINE", "engine_name": "Custom",
        "engine_code": "", "displacement": 2000.0, "bore": 86.0,
        "stroke": 86.0, "cylinders": 4, "compression": 10.0,
        "power": 150.0, "power_rpm": 6000.0, "torque": 220.0,
        "torque_rpm": 4000.0, "idle_rpm": 850.0, "redline_rpm": 7000.0,
        "boost": 0.0, "ve": 85.0, "iat": 20.0, "baro": 101.325,
        "throttle": 60.0, "injector_count": 4, "injector_flow": 250.0,
        "fuel_pressure": 3.0, "lambda": 0.90, "valves": 16,
        "fuel_type": "Gasoline", "aspiration": "Naturally Aspirated",
        "afr": 13.23, "cam_duration": 240.0, "runner_harmonic": 4.0,
        "gasket_diameter": 86.0, "gasket_thickness": 1.0,
        "chamber_volume": 50.0, "piston_volume": 0.0,
        "intake_efficiency": 90.0, "exhaust_efficiency": 90.0,
        "baro_kpa": 101.325, "fuel_density": 0.745,
        "base_ve": 85.0, "ambient": 20.0, "lambda_target": 0.90,
        "intake_valve": 42.0, "exhaust_valve": 34.0,
        "intake_duration": 240.0, "exhaust_duration": 235.0,
        "intake_lift": 10.0, "exhaust_lift": 9.0, "lsa": 110.0,
        "ivo": 15.0, "ivc": 45.0, "evo": 50.0, "evc": 15.0,
        "cam_peak_rpm": 5000.0, "intercooler_efficiency": 0.0,
        "compressor_efficiency": 72.0, "header_diameter": 38.0,
        "header_length": 32.0, "exhaust_diameter": 55.0,
        "stoich": 14.7, "bsfc": 0.50, "mechanical_efficiency": 88.0,
        "source_note": "User-created profile.",
    }


class VehicleManager:
    def __init__(self):
        self.selected_key = None
        self.selected_params = None
        self.custom_profiles = {}
        self._load_custom()

    def _path(self):
        return Path.home() / ".aslan_tuner" / "custom_vehicles.json"

    def _load_custom(self):
        try:
            data = json.loads(self._path().read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.custom_profiles = data
        except Exception:
            self.custom_profiles = {}

    def _save_custom(self):
        try:
            self._path().parent.mkdir(parents=True, exist_ok=True)
            self._path().write_text(
                json.dumps(self.custom_profiles, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def all_profiles(self):
        profiles = dict(VEHICLES)
        profiles.update(self.custom_profiles)
        return profiles

    def get(self, key):
        return self.all_profiles().get(key)

    def select(self, key):
        params = self.get(key)
        if not params:
            return None
        self.selected_key = key
        self.selected_params = dict(params)
        return self.selected_params

    def clear(self):
        self.selected_key = None
        self.selected_params = None

    def save_custom(self, key, params):
        self.custom_profiles[key] = dict(params)
        self._save_custom()

    def delete_custom(self, key):
        if key in self.custom_profiles:
            del self.custom_profiles[key]
            self._save_custom()
        if self.selected_key == key:
            self.clear()


VEHICLE_MANAGER = VehicleManager()


PARAM_ALIASES = {
    "displacement": ("displacement", "runner_displacement_input", "cr_displacement_input"),
    "bore": ("bore", "bore_input", "cr_bore_input"),
    "stroke": ("stroke", "stroke_input", "cr_stroke_input"),
    "cylinders": ("cylinders", "cylinders_input", "runner_cylinders_input"),
    "compression": ("compression", "compression_input", "cr_input"),
    "power": ("dyno_peak_power", "power", "hp", "hp_input", "pwr_power"),
    "power_rpm": ("power_rpm", "rpm_power", "hp_rpm_input"),
    "torque": ("dyno_peak_torque", "torque", "torque_input", "pwr_torque"),
    "torque_rpm": ("torque_rpm", "rpm_torque", "torque_rpm_input"),
    "idle_rpm": ("idle_rpm", "idle_input"),
    "redline_rpm": ("redline_rpm", "cutoff", "cutoff_input", "rpm_cutoff", "cutoff_rpm"),
    "boost": ("boost", "boost_input"),
    "ve": ("ve", "ve_input"),
    "iat": ("iat", "iat_c", "iat_input", "air_temp_input"),
    "baro": ("baro", "baro_kpa", "atmospheric"),
    "throttle": ("throttle", "diameter_input", "throttle_diameter"),
    "injector_count": ("injector_count",),
    "injector_flow": ("injector_flow", "flow_input"),
    "fuel_pressure": ("fuel_pressure", "rated_pressure", "rated_input", "actual_pressure", "actual_input"),
    "lambda": ("lambda", "target_lambda", "actual_lambda"),
    "afr": ("afr",),
    "cam_duration": ("cam_duration", "cam_duration_input"),
    "gasket_diameter": ("gasket_diameter", "gasket_diameter_input"),
    "gasket_thickness": ("gasket_thickness", "gasket_thickness_input"),
    "chamber_volume": ("chamber_volume", "chamber_input"),
    "piston_volume": ("piston_volume", "piston_volume_input"),
    "intake_efficiency": ("intake_efficiency",),
    "exhaust_efficiency": ("exhaust_efficiency",),
    "base_ve": ("base_ve", "ve"),
    "ambient": ("ambient", "iat"),
    "lambda_target": ("lambda_target", "lambda", "target_lambda"),
    "intake_valve": ("intake_valve",),
    "exhaust_valve": ("exhaust_valve",),
    "intake_duration": ("intake_duration", "cam_duration"),
    "exhaust_duration": ("exhaust_duration", "cam_duration"),
    "intake_lift": ("intake_lift",),
    "exhaust_lift": ("exhaust_lift",),
    "lsa": ("lsa",),
    "ivo": ("ivo",), "ivc": ("ivc",), "evo": ("evo",), "evc": ("evc",),
    "cam_peak_rpm": ("cam_peak_rpm", "rpm_torque"),
    "throttle_diameter": ("throttle_diameter", "throttle"),
    "intercooler_efficiency": ("intercooler_efficiency",),
    "compressor_efficiency": ("compressor_efficiency",),
    "header_diameter": ("header_diameter",), "header_length": ("header_length",),
    "exhaust_diameter": ("exhaust_diameter",),
    "stoich": ("stoich",), "bsfc": ("bsfc",),
    "mechanical_efficiency": ("mechanical_efficiency",),
}


def _set_widget_value(widget, value):
    if value is None:
        return False
    try:
        if hasattr(widget, "setValue"):
            widget.setValue(float(value))
            return True
        if hasattr(widget, "setText"):
            widget.setText(str(value))
            return True
    except Exception:
        return False
    return False


def apply_vehicle_parameters(calculator):
    params = VEHICLE_MANAGER.selected_params
    if not params:
        return 0
    changed = 0
    for key, aliases in PARAM_ALIASES.items():
        if key not in params:
            continue
        for attr in aliases:
            widget = getattr(calculator, attr, None)
            if widget is not None and _set_widget_value(widget, params[key]):
                changed += 1
                break
    # Generic fallback: calculator code can opt into the complete dictionary.
    try:
        calculator.aslan_vehicle_params = dict(params)
        calculator.aslan_active_vehicle = VEHICLE_MANAGER.selected_key
    except Exception:
        pass
    return changed


def _fit_dialog_to_screen(dialog, requested_size=(900, 700), min_size=(520, 420), parent=None):
    screen = None
    try:
        # Prefer the screen containing the dialog/active cursor. A nested
        # parent widget (for example a page inside a stacked widget) can have
        # a misleading geometry and previously caused dialogs to open in a
        # corner.
        screen = QApplication.screenAt(dialog.mapToGlobal(dialog.rect().center()))
    except Exception:
        screen = None
    if screen is None:
        try:
            owner = parent or dialog.parentWidget()
            if owner is not None:
                screen = QApplication.screenAt(owner.mapToGlobal(owner.rect().center()))
        except Exception:
            screen = None
    screen = screen or QApplication.primaryScreen()
    if screen is None:
        return
    area = screen.availableGeometry()
    max_w = max(420, int(area.width() * 0.94))
    max_h = max(320, int(area.height() * 0.90))
    min_w = min(max(420, min_size[0]), max_w)
    min_h = min(max(320, min_size[1]), max_h)
    w = min(max(requested_size[0], min_w), max_w)
    h = min(max(requested_size[1], min_h), max_h)
    dialog.setMinimumSize(1, 1)
    dialog.resize(w, h)
    dialog.setMinimumSize(min_w, min_h)
    frame = dialog.frameGeometry()
    frame.moveCenter(area.center())
    dialog.move(frame.topLeft())


class VehicleInfoDialog(QDialog):
    def __init__(self, key, params, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"ASLAN TUNER • {params.get('display_name', key)}")
        self._requested_size = (860, 680)
        self.setMinimumSize(1, 1)
        self.resize(860, 680)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint |
                            Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        from ui.topbar import ASLANTopBar
        root.addWidget(ASLANTopBar(self, "VEHICLE INFORMATION"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(28, 24, 28, 28)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        items = [
            ("Vehicle", params.get("display_name")), ("Engine", params.get("engine_name")),
            ("Engine code", params.get("engine_code")), ("Displacement (cc)", params.get("displacement")),
            ("Bore (mm)", params.get("bore")), ("Stroke (mm)", params.get("stroke")),
            ("Cylinders", params.get("cylinders")), ("Valves", params.get("valves")),
            ("Compression", params.get("compression")), ("Power (hp)", params.get("power")),
            ("Power RPM", params.get("power_rpm")), ("Torque (Nm)", params.get("torque")),
            ("Torque RPM", params.get("torque_rpm")), ("Idle RPM", params.get("idle_rpm")),
            ("Redline RPM", params.get("redline_rpm")), ("Boost (bar)", params.get("boost")),
            ("VE (%)", params.get("ve")), ("IAT (°C)", params.get("iat")),
            ("Barometric pressure (kPa)", params.get("baro")), ("Throttle (mm)", params.get("throttle")),
            ("Injector count", params.get("injector_count")), ("Injector flow (cc/min)", params.get("injector_flow")),
            ("Fuel pressure (bar)", params.get("fuel_pressure")), ("Target lambda", params.get("lambda")),
            ("Fuel", params.get("fuel_type")), ("Aspiration", params.get("aspiration")),
        ]
        for row, (label, value) in enumerate(items):
            l = QLabel(label)
            v = QLabel(str(value if value is not None else "—"))
            l.setObjectName("InfoLabel")
            v.setObjectName("InfoValue")
            grid.addWidget(l, row, 0)
            grid.addWidget(v, row, 1)

        note = QLabel(params.get("source_note", ""))
        note.setWordWrap(True)
        note.setObjectName("InfoNote")
        grid.addWidget(note, len(items), 0, 1, 2)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        self.setStyleSheet(_DIALOG_STYLE)

    def showEvent(self, event):
        _fit_dialog_to_screen(self, getattr(self, "_requested_size", (860, 680)), (520, 420), self.parentWidget())
        super().showEvent(event)



class CustomEngineDialog(QDialog):
    saved = Signal(str)

    FIELDS = [
        ("display_name", "Profile name"), ("engine_name", "Engine name"), ("engine_code", "Engine code"),
        ("displacement", "Displacement (cc)"), ("bore", "Bore (mm)"), ("stroke", "Stroke (mm)"),
        ("cylinders", "Cylinders"), ("valves", "Valves"), ("compression", "Compression ratio"),
        ("power", "Power (hp)"), ("power_rpm", "Power RPM"), ("torque", "Torque (Nm)"),
        ("torque_rpm", "Torque RPM"), ("idle_rpm", "Idle RPM"), ("redline_rpm", "Redline RPM"),
        ("boost", "Boost (bar)"), ("ve", "Volumetric efficiency (%)"), ("iat", "Intake temp (°C)"),
        ("baro", "Barometric pressure (kPa)"), ("throttle", "Throttle diameter (mm)"),
        ("injector_count", "Injector count"), ("injector_flow", "Injector flow (cc/min)"),
        ("fuel_pressure", "Fuel pressure (bar)"), ("lambda", "Target lambda"), ("afr", "Target AFR"),
        ("cam_duration", "Cam duration (deg)"), ("runner_harmonic", "Runner harmonic"),
        ("gasket_diameter", "Gasket diameter (mm)"), ("gasket_thickness", "Gasket thickness (mm)"),
        ("chamber_volume", "Chamber volume (cc)"), ("piston_volume", "Piston volume (cc)"),
        ("intake_efficiency", "Intake efficiency (%)"), ("exhaust_efficiency", "Exhaust efficiency (%)"),
        ("fuel_density", "Fuel density (g/cc)"), ("base_ve", "Dyno base VE (%)"),
        ("ambient", "Dyno ambient temp (°C)"), ("lambda_target", "Dyno target lambda"),
        ("intake_valve", "Intake valve (mm)"), ("exhaust_valve", "Exhaust valve (mm)"),
        ("intake_duration", "Intake duration (deg)"), ("exhaust_duration", "Exhaust duration (deg)"),
        ("intake_lift", "Intake lift (mm)"), ("exhaust_lift", "Exhaust lift (mm)"),
        ("lsa", "Cam LSA (deg)"), ("ivo", "IVO (deg)"), ("ivc", "IVC (deg)"),
        ("evo", "EVO (deg)"), ("evc", "EVC (deg)"), ("cam_peak_rpm", "Cam peak RPM"),
        ("intercooler_efficiency", "Intercooler efficiency (%)"),
        ("compressor_efficiency", "Compressor efficiency (%)"),
        ("header_diameter", "Header diameter (mm)"), ("header_length", "Header length (in)"),
        ("exhaust_diameter", "Exhaust diameter (mm)"), ("stoich", "Stoich AFR"),
        ("bsfc", "BSFC (lb/hp-hr)"), ("mechanical_efficiency", "Mechanical efficiency (%)"),
    ]

    def __init__(self, existing=None, parent=None, existing_key=None):
        super().__init__(parent)
        self.existing_key = existing_key
        self.setWindowTitle("ASLAN TUNER • Custom Engine")
        self._requested_size = (940, 760)
        self.setMinimumSize(1, 1)
        self.resize(940, 760)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint |
                            Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        data = blank_custom()
        if existing:
            data.update(existing)
        self.data = data
        self.edits = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        from ui.topbar import ASLANTopBar
        root.addWidget(ASLANTopBar(self, "CUSTOM ENGINE"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(28, 24, 28, 28)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setSizeConstraint(QGridLayout.SizeConstraint.SetMinimumSize)

        for i, (key, label) in enumerate(self.FIELDS):
            r, c = divmod(i, 2)
            box = QVBoxLayout()
            lab = QLabel(label)
            lab.setObjectName("CustomLabel")
            lab.setWordWrap(True)
            lab.setMinimumHeight(30)
            edit = QLineEdit(str(data.get(key, "")))
            edit.setObjectName("CustomInput")
            edit.setMinimumHeight(46)
            edit.setFont(QFont("Segoe UI", 11))
            box.addWidget(lab)
            box.addWidget(edit)
            grid.addLayout(box, r, c)
            self.edits[key] = edit

        # Keep the scroll range tied to the actual form content instead of
        # letting a resizable viewport create extra empty scroll space.
        content.setMinimumSize(grid.sizeHint().width(), grid.sizeHint().height())
        content.adjustSize()

        # The form must own the widgets through the scroll area.
        # Without this, the content widget is destroyed after construction,
        # leaving blank dialogs and stale QLineEdit references.
        scroll.setWidget(content)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        actions = QHBoxLayout()
        actions.setContentsMargins(28, 0, 28, 24)
        save = QPushButton("SAVE CUSTOM PROFILE")
        cancel = QPushButton("CANCEL")
        save.setObjectName("Primary")
        cancel.setObjectName("Secondary")
        save.clicked.connect(self._save)
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        actions.addStretch()
        actions.addWidget(save)
        root.addWidget(scroll, 1)
        root.addLayout(actions)

        self.setStyleSheet(_DIALOG_STYLE)

    def showEvent(self, event):
        _fit_dialog_to_screen(self, getattr(self, "_requested_size", (940, 760)), (520, 420), self.parentWidget())
        super().showEvent(event)

    def _save(self):
        data = dict(self.data)
        for key, edit in self.edits.items():
            value = edit.text().strip()
            if key in ("display_name", "engine_name", "engine_code"):
                data[key] = value
            elif key in ("fuel_type", "aspiration"):
                data[key] = value
            else:
                try:
                    data[key] = float(value)
                except ValueError:
                    QMessageBox.warning(self, "Invalid value", f"{key}: enter a numeric value.")
                    edit.setFocus()
                    return
        name = data.get("display_name", "").strip() or "CUSTOM ENGINE"
        key = f"CUSTOM::{name}"
        # Editing a profile should update it rather than leave an old
        # duplicate behind when the profile name changes.
        if self.existing_key and self.existing_key != key:
            VEHICLE_MANAGER.delete_custom(self.existing_key)
        VEHICLE_MANAGER.save_custom(key, data)
        self.saved.emit(key)
        self.accept()


_DIALOG_STYLE = """
QDialog { background:#090b0e; color:#f1f2f4; }
QWidget { color:#e4e6e9; }
QScrollArea, QScrollArea QWidget { background:#090b0e; border:none; }
QScrollBar:vertical { background:#0b0d10; width:10px; margin:2px; border-radius:5px; }
QScrollBar::handle:vertical { background:#5b1a24; min-height:28px; border-radius:5px; }
QScrollBar::handle:vertical:hover { background:#e31b2d; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
QLabel { color:#c8ccd2; }
QLabel#CustomLabel { color:#f0f2f5; font-size:13px; font-weight:700; padding-bottom:3px; }
QLabel#InfoLabel { color:#7f8791; font-size:11px; font-weight:700; text-transform:uppercase; }
QLabel#InfoValue { color:#f3f4f6; background:#12161b; border:1px solid #292e36; border-radius:10px; padding:11px; }
QLabel#InfoNote { color:#8f96a0; background:#111419; border:1px solid #3a1a20; border-radius:10px; padding:14px; margin-top:8px; }
QLineEdit#CustomInput { background:#111419; border:1px solid #30353d; border-radius:10px; padding:9px 12px; color:#fff; font-size:13px; min-height:42px; }
QLineEdit#CustomInput:focus { border:1px solid #e90018; background:#15191f; }
QPushButton { border-radius:10px; padding:11px 18px; font-weight:700; }
QPushButton#Primary { background:#e90018; color:white; border:1px solid #ff3045; }
QPushButton#Primary:hover { background:#ff172b; }
QPushButton#Secondary { background:#15181d; color:#d9dce1; border:1px solid #30353d; }
QPushButton#Secondary:hover { border-color:#e90018; }
"""


def calculator_style():
    return """
QDialog { background:#080a0d; color:#e8ebef; }
QDialog QWidget { color:#e0e4e9; }
QScrollArea { background:#080a0d; border:none; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background:#101419; color:#f4f5f7; border:1px solid #2a3038;
    border-radius:9px; padding:8px 10px; selection-background-color:#a90014;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border:1px solid #ef1730; background:#14181e; }
QPushButton { background:#12161b; color:#e7e9ed; border:1px solid #2b3139; border-radius:9px; padding:9px 13px; font-weight:700; }
QPushButton:hover { background:#1a2027; border-color:#ef1730; }
QPushButton#calculateButton, QPushButton#Primary { background:#d90f25; color:#fff; border:1px solid #ff4054; }
QPushButton#calculateButton:hover, QPushButton#Primary:hover { background:#ef1730; }
QFrame#SectionCard, QFrame#Panel, QFrame#ResultCard, QFrame#InfoPanel {
    background:#101419; border:1px solid #292f37; border-radius:13px;
}
QLabel#SectionTitle { color:#ff3349; font-weight:800; }
QLabel#SectionSubtitle { color:#858d98; }
QScrollBar:vertical { background:#0b0e12; width:9px; border:none; }
QScrollBar::handle:vertical { background:#343b44; border-radius:4px; min-height:28px; }
QScrollBar::handle:vertical:hover { background:#ef1730; }
QScrollBar:horizontal { background:#0b0e12; height:9px; border:none; }
QScrollBar::handle:horizontal { background:#343b44; border-radius:4px; min-width:28px; }
"""


def prepare_calculator(calculator, title=None):
    """Apply the shared calculator shell without changing calculator formulas."""
    from ui.topbar import ASLANTopBar
    calculator.setWindowFlags(
        Qt.Window | Qt.FramelessWindowHint |
        Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint |
        Qt.WindowCloseButtonHint
    )
    layout = calculator.layout()
    if layout is not None and not hasattr(calculator, "title_bar"):
        bar = ASLANTopBar(calculator, title or calculator.windowTitle())
        calculator.title_bar = bar
        layout.insertWidget(0, bar)
    calculator.setStyleSheet(calculator.styleSheet() + "\n" + calculator_style())
    apply_vehicle_parameters(calculator)

    # Responsive sizing for calculators implemented as plain QDialog.
    def fit():
        from PySide6.QtWidgets import QApplication
        screen = None
        try:
            parent = calculator.parentWidget()
            if parent is not None:
                screen = QApplication.screenAt(parent.mapToGlobal(parent.rect().center()))
        except Exception:
            pass
        screen = screen or QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        max_w = max(420, int(area.width() * 0.94))
        max_h = max(320, int(area.height() * 0.90))
        requested = (calculator.width(), calculator.height())
        old_min = (calculator.minimumWidth(), calculator.minimumHeight())
        min_w = min(max(420, old_min[0]), max_w)
        min_h = min(max(320, old_min[1]), max_h)
        target_w = min(max(requested[0], min_w), max_w)
        target_h = min(max(requested[1], min_h), max_h)
        calculator.setMinimumSize(1, 1)
        calculator.resize(target_w, target_h)
        calculator.setMinimumSize(min_w, min_h)
        frame = calculator.frameGeometry()
        frame.moveCenter(area.center())
        calculator.move(frame.topLeft())

    if not hasattr(calculator, "_aslan_responsive_installed"):
        calculator._aslan_responsive_installed = True
        original_show = calculator.showEvent
        def show_event(event):
            fit()
            original_show(event)
        calculator.showEvent = show_event
    fit()
    return calculator
