import csv
import math

from ui.base_window import ASLANDialog

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QFrame,
    QApplication,
)


class AFRLambdaCalculator(ASLANDialog):

    ATMOSPHERIC_KPA = 101.325
    PSI_TO_KPA = 6.894757

    SAFE_MAX_LAMBDA = 1.045
    SAFE_MIN_NA = 0.875
    SAFE_MIN_BOOST = 0.780

    # =========================================================
    # FINAL ENGINEERING LAMBDA BASELINE
    # =========================================================

    CRUISE_LAMBDA = 1.000

    NA_WOT_BASE = 0.900
    NA_WOT_MIN = 0.885

    TURBO_LOW_BOOST = 0.890
    TURBO_MID_BOOST = 0.845
    TURBO_HIGH_BOOST = 0.800

    HIGH_LOAD_START = 0.58

    def __init__(self, parent=None):

        super().__init__(
            parent=parent,
            title="AFR / LAMBDA",
            window_title="ASLAN TUNER - AFR / LAMBDA",
            minimum_size=(1080, 700),
            size=(1250, 820)
        )

        self.rpm_axis = []
        self.map_axis = []
        self.lambda_table = []
        self.result_window = None

        self._build_style()
        self._build_ui()

    # =========================================================
    # STYLE
    # =========================================================

    def _build_style(self):

        self.setStyleSheet("""
            QDialog {
                background-color: #181818;
                color: #eeeeee;
            }

            QLabel {
                color: #eeeeee;
            }

            QLineEdit {
                background-color: #242424;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
                selection-background-color: #d71920;
            }

            QLineEdit:focus {
                border: 1px solid #e21b23;
            }

            QPushButton {
                background-color: #242424;
                border: 1px solid #444444;
                border-radius: 7px;
                color: #eeeeee;
                padding: 9px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #351719;
                border: 1px solid #e21b23;
            }

            QPushButton:pressed {
                background-color: #d71920;
                color: #ffffff;
            }

            QFrame#Panel {
                background-color: #202020;
                border: 1px solid #333333;
                border-radius: 10px;
            }

            QFrame#InfoPanel {
                background-color: #241718;
                border: 1px solid #572326;
                border-radius: 8px;
            }
        """)

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        main_layout = self.content_layout

        main_layout.setContentsMargins(
            22,
            18,
            22,
            18
        )

        main_layout.setSpacing(14)

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

        title = QLabel(
            "ASLAN TUNER"
        )

        title.setFont(
            QFont(
                "Arial",
                22,
                QFont.Bold
            )
        )

        title.setStyleSheet(
            "color: #e21b23;"
        )

        subtitle = QLabel(
            "AFR / LAMBDA TARGET TABLE GENERATOR"
        )

        subtitle.setFont(
            QFont(
                "Arial",
                10,
                QFont.Bold
            )
        )

        subtitle.setStyleSheet(
            "color: #888888;"
        )

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            subtitle
        )

        # -----------------------------------------------------
        # PARAMETERS PANEL
        # -----------------------------------------------------

        panel = QFrame()

        panel.setObjectName(
            "Panel"
        )

        panel_layout = QVBoxLayout(
            panel
        )

        panel_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        panel_layout.setSpacing(
            12
        )

        panel_title = QLabel(
            "ENGINE PARAMETERS"
        )

        panel_title.setFont(
            QFont(
                "Arial",
                12,
                QFont.Bold
            )
        )

        panel_title.setStyleSheet(
            "color: #e21b23;"
        )

        panel_layout.addWidget(
            panel_title
        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(
            12
        )

        grid.setVerticalSpacing(
            10
        )

        self.rows_input = self._create_input(
            "16"
        )

        self.cols_input = self._create_input(
            "16"
        )

        self.idle_input = self._create_input(
            "900"
        )

        self.cutoff_input = self._create_input(
            "7000"
        )

        self.hp_input = self._create_input(
            "100"
        )

        self.hp_rpm_input = self._create_input(
            "5000"
        )

        self.torque_input = self._create_input(
            "170"
        )

        self.torque_rpm_input = self._create_input(
            "3000"
        )

        self.displacement_input = self._create_input(
            "2000"
        )

        self.boost_input = self._create_input(
            "0"
        )

        fields = [
            (
                "تعداد سطر",
                self.rows_input,
                "تعداد ردیف‌های جدول"
            ),
            (
                "تعداد ستون",
                self.cols_input,
                "تعداد ستون‌های جدول"
            ),
            (
                "دور آرام",
                self.idle_input,
                "Idle RPM"
            ),
            (
                "دور موتور کاتاف",
                self.cutoff_input,
                "Maximum RPM"
            ),
            (
                "اوج توان (HP)",
                self.hp_input,
                "Peak Horsepower"
            ),
            (
                "دور اوج توان",
                self.hp_rpm_input,
                "RPM at peak power"
            ),
            (
                "اوج گشتاور (Nm)",
                self.torque_input,
                "Peak Torque"
            ),
            (
                "دور اوج گشتاور",
                self.torque_rpm_input,
                "RPM at peak torque"
            ),
            (
                "حجم موتور (cc)",
                self.displacement_input,
                "Engine displacement"
            ),
            (
                "بوست توربو (PSI)",
                self.boost_input,
                "Turbo boost"
            ),
        ]

        for index, (
            label_text,
            widget,
            info_text
        ) in enumerate(fields):

            row = index // 2
            col = (index % 2) * 2

            label = QLabel(
                label_text
            )

            label.setFont(
                QFont(
                    "Arial",
                    10,
                    QFont.Bold
                )
            )

            info = QLabel(
                "ⓘ"
            )

            info.setToolTip(
                info_text
            )

            info.setStyleSheet("""
                QLabel {
                    color: #e21b23;
                    font-size: 15px;
                    font-weight: bold;
                }
            """)

            label_box = QHBoxLayout()

            label_box.setSpacing(
                5
            )

            label_box.addWidget(
                label
            )

            label_box.addWidget(
                info
            )

            label_box.addStretch()

            grid.addLayout(
                label_box,
                row,
                col
            )

            grid.addWidget(
                widget,
                row,
                col + 1
            )

        panel_layout.addLayout(
            grid
        )

        main_layout.addWidget(
            panel
        )

        # -----------------------------------------------------
        # INFO
        # -----------------------------------------------------

        info_panel = QFrame()

        info_panel.setObjectName(
            "InfoPanel"
        )

        info_layout = QHBoxLayout(
            info_panel
        )

        info_layout.setContentsMargins(
            14,
            10,
            14,
            10
        )

        info_label = QLabel(
            "ⓘ  جدول هدف Lambda بر اساس دور موتور، بار موتور، "
            "توان، گشتاور، حجم موتور و فشار بوست تولید می‌شود."
        )

        info_label.setWordWrap(
            True
        )

        info_label.setStyleSheet(
            "color: #bbbbbb;"
        )

        info_layout.addWidget(
            info_label
        )

        main_layout.addWidget(
            info_panel
        )

        # -----------------------------------------------------
        # BUTTONS
        # -----------------------------------------------------

        buttons = QHBoxLayout()

        buttons.setSpacing(
            10
        )

        self.generate_button = QPushButton(
            "GENERATE LAMBDA TABLE"
        )

        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #c9141c;
                border: 1px solid #e21b23;
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 11px 20px;
            }

            QPushButton:hover {
                background-color: #e21b23;
            }
        """)

        self.export_button = QPushButton(
            "EXPORT CSV"
        )

        self.reset_button = QPushButton(
            "RESET"
        )

        self.generate_button.clicked.connect(
            lambda checked=False:
            self.generate_table(
                open_window=True
            )
        )

        self.export_button.clicked.connect(
            self.export_csv
        )

        self.reset_button.clicked.connect(
            self.reset
        )

        buttons.addWidget(
            self.generate_button
        )

        buttons.addWidget(
            self.export_button
        )

        buttons.addWidget(
            self.reset_button
        )

        buttons.addStretch()

        main_layout.addLayout(
            buttons
        )

        # -----------------------------------------------------
        # STATUS
        # -----------------------------------------------------

        self.status_label = QLabel(
            "Ready."
        )

        self.status_label.setStyleSheet(
            "color: #888888; padding: 5px;"
        )

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addStretch()

    # =========================================================
    # INPUT
    # =========================================================

    def _create_input(
        self,
        value
    ):

        edit = QLineEdit()

        edit.setText(
            value
        )

        edit.setMinimumHeight(
            36
        )

        return edit

    def _read_inputs(self):

        try:

            rows = int(
                self.rows_input.text()
            )

            cols = int(
                self.cols_input.text()
            )

            idle_rpm = float(
                self.idle_input.text()
            )

            cutoff_rpm = float(
                self.cutoff_input.text()
            )

            hp = float(
                self.hp_input.text()
            )

            hp_rpm = float(
                self.hp_rpm_input.text()
            )

            torque = float(
                self.torque_input.text()
            )

            torque_rpm = float(
                self.torque_rpm_input.text()
            )

            displacement = float(
                self.displacement_input.text()
            )

            boost = float(
                self.boost_input.text()
            )

        except ValueError:

            raise ValueError(
                "همه مقادیر باید عددی باشند."
            )

        if not 2 <= rows <= 64:

            raise ValueError(
                "تعداد سطر باید بین 2 تا 64 باشد."
            )

        if not 2 <= cols <= 64:

            raise ValueError(
                "تعداد ستون باید بین 2 تا 64 باشد."
            )

        if idle_rpm <= 0:

            raise ValueError(
                "دور آرام باید بیشتر از صفر باشد."
            )

        if cutoff_rpm <= idle_rpm:

            raise ValueError(
                "دور کاتاف باید از دور آرام بیشتر باشد."
            )

        if hp <= 0:

            raise ValueError(
                "توان باید بیشتر از صفر باشد."
            )

        if torque <= 0:

            raise ValueError(
                "گشتاور باید بیشتر از صفر باشد."
            )

        if displacement <= 0:

            raise ValueError(
                "حجم موتور باید بیشتر از صفر باشد."
            )

        if boost < 0:

            raise ValueError(
                "بوست نمی‌تواند منفی باشد."
            )

        if not idle_rpm <= hp_rpm <= cutoff_rpm:

            raise ValueError(
                "دور اوج توان باید بین دور آرام و کاتاف باشد."
            )

        if not idle_rpm <= torque_rpm <= cutoff_rpm:

            raise ValueError(
                "دور اوج گشتاور باید بین دور آرام و کاتاف باشد."
            )

        return {
            "rows": rows,
            "cols": cols,
            "idle_rpm": idle_rpm,
            "cutoff_rpm": cutoff_rpm,
            "hp": hp,
            "hp_rpm": hp_rpm,
            "torque": torque,
            "torque_rpm": torque_rpm,
            "displacement": displacement,
            "boost": boost,
        }

    # =========================================================
    # RPM AXIS
    # =========================================================

    def _rpm_round_step(
        self,
        rpm_range
    ):

        if rpm_range <= 7000:
            return 100

        return 250

    def _build_rpm_axis(
        self,
        count,
        idle_rpm,
        cutoff_rpm,
        torque_rpm,
        power_rpm
    ):

        if count == 2:

            return [
                int(
                    round(idle_rpm)
                ),
                int(
                    round(cutoff_rpm)
                )
            ]

        landmarks = [
            idle_rpm,
            torque_rpm,
            power_rpm,
            cutoff_rpm
        ]

        landmarks = sorted(
            set(
                max(
                    idle_rpm,
                    min(
                        cutoff_rpm,
                        x
                    )
                )
                for x in landmarks
            )
        )

        if len(landmarks) > count:

            landmarks = [
                idle_rpm,
                cutoff_rpm
            ]

        axis = list(
            landmarks
        )

        remaining = (
            count
            - len(axis)
        )

        if remaining > 0:

            gaps = []

            for i in range(
                len(axis) - 1
            ):

                gap = (
                    axis[i + 1]
                    - axis[i]
                )

                gaps.append(
                    (
                        gap,
                        i
                    )
                )

            for _ in range(
                remaining
            ):

                gaps.sort(
                    reverse=True
                )

                gap, index = gaps[0]

                left = axis[index]
                right = axis[
                    index + 1
                ]

                midpoint = (
                    left
                    + right
                ) / 2.0

                axis.insert(
                    index + 1,
                    midpoint
                )

                gaps = []

                for i in range(
                    len(axis) - 1
                ):

                    gaps.append(
                        (
                            axis[i + 1]
                            - axis[i],
                            i
                        )
                    )

        step = self._rpm_round_step(
            cutoff_rpm
            - idle_rpm
        )

        rounded = []

        for value in axis:

            if value == idle_rpm:

                rounded_value = int(
                    round(
                        idle_rpm
                    )
                )

            elif value == cutoff_rpm:

                rounded_value = int(
                    round(
                        cutoff_rpm
                    )
                )

            else:

                rounded_value = int(
                    round(
                        value / step
                    )
                    * step
                )

            rounded_value = max(
                int(
                    round(
                        idle_rpm
                    )
                ),
                min(
                    int(
                        round(
                            cutoff_rpm
                        )
                    ),
                    rounded_value
                )
            )

            if (
                not rounded
                or rounded_value
                > rounded[-1]
            ):

                rounded.append(
                    rounded_value
                )

        required = [
            int(
                round(
                    idle_rpm
                )
            ),
            int(
                round(
                    torque_rpm
                )
            ),
            int(
                round(
                    power_rpm
                )
            ),
            int(
                round(
                    cutoff_rpm
                )
            )
        ]

        required = sorted(
            set(required)
        )

        for value in required:

            if value not in rounded:

                if len(rounded) < count:

                    rounded.append(
                        value
                    )

                else:

                    nearest_index = min(
                        range(
                            len(rounded)
                        ),
                        key=lambda i:
                        abs(
                            rounded[i]
                            - value
                        )
                    )

                    rounded[
                        nearest_index
                    ] = value

        rounded = sorted(
            set(rounded)
        )

        while len(rounded) < count:

            best_gap = -1
            best_index = None

            for i in range(
                len(rounded) - 1
            ):

                gap = (
                    rounded[i + 1]
                    - rounded[i]
                )

                if gap > best_gap:

                    best_gap = gap
                    best_index = i

            if best_index is None:
                break

            left = rounded[
                best_index
            ]

            right = rounded[
                best_index + 1
            ]

            new_value = int(
                round(
                    (
                        (
                            left
                            + right
                        ) / 2
                    )
                    / step
                )
                * step
            )

            if new_value <= left:

                new_value = (
                    left
                    + step
                )

            if new_value >= right:

                new_value = (
                    right
                    - step
                )

            if (
                new_value <= left
                or new_value >= right
            ):

                break

            rounded.insert(
                best_index + 1,
                new_value
            )

        if len(rounded) > count:

            important = set(
                required
            )

            while len(rounded) > count:

                removable = [
                    i
                    for i, value
                    in enumerate(
                        rounded
                    )
                    if value not in important
                ]

                if not removable:
                    break

                index = min(
                    removable,
                    key=lambda i:
                    min(
                        abs(
                            rounded[i]
                            - rounded[j]
                        )
                        for j in range(
                            len(rounded)
                        )
                        if j != i
                    )
                )

                rounded.pop(
                    index
                )

        if len(rounded) < count:

            exact = [
                int(
                    round(
                        idle_rpm
                        + (
                            cutoff_rpm
                            - idle_rpm
                        )
                        * i
                        / (
                            count - 1
                        )
                    )
                )
                for i in range(
                    count
                )
            ]

            for value in exact:

                value = int(
                    round(
                        value / step
                    )
                    * step
                )

                value = max(
                    int(
                        round(
                            idle_rpm
                        )
                    ),
                    min(
                        int(
                            round(
                                cutoff_rpm
                            )
                        ),
                        value
                    )
                )

                if value not in rounded:

                    rounded.append(
                        value
                    )

                if len(rounded) >= count:
                    break

            rounded = sorted(
                rounded
            )

        return rounded[:count]

    # =========================================================
    # MAP AXIS
    # =========================================================

    def _build_map_axis(
        self,
        count,
        boost
    ):

        min_map = 25.0

        max_map = (
            self.ATMOSPHERIC_KPA
            + boost
            * self.PSI_TO_KPA
        )

        if count == 1:

            return [
                max_map
            ]

        axis = []

        for i in range(
            count
        ):

            ratio = (
                i
                / (
                    count - 1
                )
            )

            value = (
                min_map
                + (
                    max_map
                    - min_map
                )
                * ratio
            )

            value = round(
                value,
                1
            )

            if (
                not axis
                or value > axis[-1]
            ):

                axis.append(
                    value
                )

        while len(axis) < count:

            last = axis[-1]

            if last >= max_map:
                break

            extra = (
                last
                + (
                    max_map
                    - min_map
                )
                / count
            )

            extra = min(
                extra,
                max_map
            )

            if extra > last:

                axis.append(
                    round(
                        extra,
                        1
                    )
                )

            else:

                break

        return axis[:count]

    # =========================================================
    # ENGINE CHARACTERISTICS
    # =========================================================

    def _engine_characteristics(
        self,
        data
    ):

        displacement_l = (
            data["displacement"]
            / 1000.0
        )

        hp_per_liter = (
            data["hp"]
            / max(
                displacement_l,
                0.001
            )
        )

        torque_per_liter = (
            data["torque"]
            / max(
                displacement_l,
                0.001
            )
        )

        displacement_m3 = (
            data["displacement"]
            / 1_000_000.0
        )

        bmep_pa = (
            4.0
            * math.pi
            * data["torque"]
            / max(
                displacement_m3,
                1e-9
            )
        )

        bmep_bar = (
            bmep_pa
            / 100000.0
        )

        implied_torque = (
            9550.0
            * data["hp"]
            / max(
                data["hp_rpm"],
                1.0
            )
        )

        torque_consistency = (
            data["torque"]
            / max(
                implied_torque,
                1.0
            )
        )

        output_intensity = (
            0.45
            * min(
                hp_per_liter
                / 120.0,
                2.0
            )
            + 0.35
            * min(
                torque_per_liter
                / 120.0,
                2.0
            )
            + 0.20
            * min(
                bmep_bar
                / 15.0,
                2.0
            )
        )

        return {
            "displacement_l":
                displacement_l,

            "hp_per_liter":
                hp_per_liter,

            "torque_per_liter":
                torque_per_liter,

            "bmep_bar":
                bmep_bar,

            "implied_torque":
                implied_torque,

            "torque_consistency":
                torque_consistency,

            "output_intensity":
                output_intensity,
        }

    # =========================================================
    # HELPER
    # =========================================================

    def _clamp(
        self,
        value,
        low,
        high
    ):

        return max(
            low,
            min(
                high,
                value
            )
        )

    def _smoothstep(
        self,
        value
    ):

        value = self._clamp(
            value,
            0.0,
            1.0
        )

        return (
            value
            * value
            * (
                3.0
                - 2.0
                * value
            )
        )

    # =========================================================
    # LOAD
    # =========================================================

    def _load_factor(
        self,
        map_kpa
    ):

        load = (
            map_kpa
            / self.ATMOSPHERIC_KPA
        )

        return self._clamp(
            load,
            0.0,
            2.0
        )

    # =========================================================
    # HIGH RPM FACTOR
    # =========================================================

    def _high_rpm_factor(
        self,
        rpm,
        data
    ):

        idle = data[
            "idle_rpm"
        ]

        cutoff = data[
            "cutoff_rpm"
        ]

        rpm_range = max(
            cutoff
            - idle,
            1.0
        )

        ratio = (
            rpm
            - idle
        ) / rpm_range

        ratio = self._clamp(
            ratio,
            0.0,
            1.0
        )

        factor = (
            ratio
            - 0.68
        ) / 0.32

        return self._smoothstep(
            factor
        )

    # =========================================================
    # TORQUE ZONE
    # =========================================================

    def _torque_zone_factor(
        self,
        rpm,
        data
    ):

        idle = data[
            "idle_rpm"
        ]

        cutoff = data[
            "cutoff_rpm"
        ]

        rpm_range = max(
            cutoff
            - idle,
            1.0
        )

        sigma = max(
            rpm_range
            * 0.12,
            250.0
        )

        distance = (
            rpm
            - data["torque_rpm"]
        )

        return math.exp(
            -0.5
            * (
                distance
                / sigma
            ) ** 2
        )

    # =========================================================
    # POWER ZONE
    # =========================================================

    def _power_zone_factor(
        self,
        rpm,
        data
    ):

        idle = data[
            "idle_rpm"
        ]

        cutoff = data[
            "cutoff_rpm"
        ]

        rpm_range = max(
            cutoff
            - idle,
            1.0
        )

        sigma = max(
            rpm_range
            * 0.14,
            300.0
        )

        distance = (
            rpm
            - data["hp_rpm"]
        )

        return math.exp(
            -0.5
            * (
                distance
                / sigma
            ) ** 2
        )

    # =========================================================
    # ENGINE STRESS
    # =========================================================

    def _engine_stress_factor(
        self,
        data,
        characteristics
    ):

        hp_intensity = self._clamp(
            characteristics[
                "hp_per_liter"
            ]
            / 120.0,
            0.0,
            1.5
        )

        torque_intensity = self._clamp(
            characteristics[
                "torque_per_liter"
            ]
            / 120.0,
            0.0,
            1.5
        )

        bmep_intensity = self._clamp(
            characteristics[
                "bmep_bar"
            ]
            / 15.0,
            0.0,
            1.5
        )

        stress = (
            0.40
            * hp_intensity
            + 0.35
            * torque_intensity
            + 0.25
            * bmep_intensity
        )

        return self._clamp(
            stress,
            0.0,
            1.5
        )

    # =========================================================
    # NA WOT TARGET
    # =========================================================

    def _na_wot_target(
        self,
        rpm,
        data,
        characteristics
    ):

        stress = (
            self._engine_stress_factor(
                data,
                characteristics
            )
        )

        torque_factor = (
            self._torque_zone_factor(
                rpm,
                data
            )
        )

        power_factor = (
            self._power_zone_factor(
                rpm,
                data
            )
        )

        high_rpm = (
            self._high_rpm_factor(
                rpm,
                data
            )
        )

        value = self.NA_WOT_BASE

        value -= (
            0.006
            * self._clamp(
                stress,
                0.0,
                1.0
            )
        )

        zone_factor = (
            0.55
            * torque_factor
            + 0.45
            * power_factor
        )

        value -= (
            0.004
            * zone_factor
        )

        value -= (
            0.010
            * high_rpm
        )

        return self._clamp(
            value,
            self.NA_WOT_MIN,
            self.NA_WOT_BASE
        )

    # =========================================================
    # TURBO WOT TARGET
    # =========================================================

    def _turbo_wot_target(
        self,
        map_kpa,
        rpm,
        data,
        characteristics
    ):

        atmospheric = (
            self.ATMOSPHERIC_KPA
        )

        commanded_boost_psi = max(
            data["boost"],
            0.0
        )

        commanded_boost_kpa = (
            commanded_boost_psi
            * self.PSI_TO_KPA
        )

        actual_boost_kpa = max(
            0.0,
            map_kpa
            - atmospheric
        )

        if commanded_boost_kpa <= 0:

            return self._na_wot_target(
                rpm,
                data,
                characteristics
            )

        boost_ratio = (
            actual_boost_kpa
            / commanded_boost_kpa
        )

        boost_ratio = self._clamp(
            boost_ratio,
            0.0,
            1.0
        )

        boost_psi = (
            actual_boost_kpa
            / self.PSI_TO_KPA
        )

        if boost_psi <= 4.0:

            t = (
                boost_psi
                / 4.0
            )

            t = self._smoothstep(
                t
            )

            target = (
                self.TURBO_LOW_BOOST
                + (
                    0.870
                    - self.TURBO_LOW_BOOST
                )
                * t
            )

        elif boost_psi <= 8.0:

            t = (
                boost_psi
                - 4.0
            ) / 4.0

            t = self._smoothstep(
                t
            )

            target = (
                0.870
                + (
                    0.850
                    - 0.870
                )
                * t
            )

        elif boost_psi <= 12.0:

            t = (
                boost_psi
                - 8.0
            ) / 4.0

            t = self._smoothstep(
                t
            )

            target = (
                0.850
                + (
                    0.825
                    - 0.850
                )
                * t
            )

        elif boost_psi <= 16.0:

            t = (
                boost_psi
                - 12.0
            ) / 4.0

            t = self._smoothstep(
                t
            )

            target = (
                0.825
                + (
                    self.TURBO_HIGH_BOOST
                    - 0.825
                )
                * t
            )

        else:

            t = self._clamp(
                (
                    boost_psi
                    - 16.0
                ) / 10.0,
                0.0,
                1.0
            )

            t = self._smoothstep(
                t
            )

            target = (
                self.TURBO_HIGH_BOOST
                - 0.010
                * t
            )

        stress = (
            self._engine_stress_factor(
                data,
                characteristics
            )
        )

        target -= (
            0.005
            * self._clamp(
                stress,
                0.0,
                1.0
            )
            * boost_ratio
        )

        torque_factor = (
            self._torque_zone_factor(
                rpm,
                data
            )
        )

        power_factor = (
            self._power_zone_factor(
                rpm,
                data
            )
        )

        zone_factor = (
            0.55
            * torque_factor
            + 0.45
            * power_factor
        )

        target -= (
            0.004
            * zone_factor
            * boost_ratio
        )

        high_rpm = (
            self._high_rpm_factor(
                rpm,
                data
            )
        )

        target -= (
            0.010
            * high_rpm
            * boost_ratio
        )

        return self._clamp(
            target,
            self.SAFE_MIN_BOOST,
            self.TURBO_LOW_BOOST
        )

    # =========================================================
    # FINAL LAMBDA CALCULATION
    # =========================================================

    def _calculate_lambda(
        self,
        rpm,
        map_kpa,
        data,
        characteristics
    ):

        load = (
            self._load_factor(
                map_kpa
            )
        )

        if load <= self.HIGH_LOAD_START:

            x = (
                load
                / self.HIGH_LOAD_START
            )

            x = self._clamp(
                x,
                0.0,
                1.0
            )

            light_load_drop = (
                0.0035
                * (
                    x ** 2.2
                )
            )

            value = (
                self.CRUISE_LAMBDA
                - light_load_drop
            )

            idle_distance = abs(
                rpm
                - data["idle_rpm"]
            )

            if idle_distance < 250.0:

                idle_factor = (
                    1.0
                    - idle_distance
                    / 250.0
                )

                idle_factor = self._clamp(
                    idle_factor,
                    0.0,
                    1.0
                )

                value += (
                    0.0015
                    * idle_factor
                )

            return self._clamp(
                value,
                0.990,
                self.SAFE_MAX_LAMBDA
            )

        blend_raw = (
            load
            - self.HIGH_LOAD_START
        ) / (
            1.0
            - self.HIGH_LOAD_START
        )

        blend = self._smoothstep(
            blend_raw
        )

        if data["boost"] > 0.0:

            wot_target = (
                self._turbo_wot_target(
                    map_kpa,
                    rpm,
                    data,
                    characteristics
                )
            )

        else:

            wot_target = (
                self._na_wot_target(
                    rpm,
                    data,
                    characteristics
                )
            )

        value = (
            self.CRUISE_LAMBDA
            + (
                wot_target
                - self.CRUISE_LAMBDA
            )
            * blend
        )

        torque_factor = (
            self._torque_zone_factor(
                rpm,
                data
            )
        )

        power_factor = (
            self._power_zone_factor(
                rpm,
                data
            )
        )

        zone_factor = (
            0.55
            * torque_factor
            + 0.45
            * power_factor
        )

        value -= (
            0.0025
            * zone_factor
            * blend
        )

        high_rpm = (
            self._high_rpm_factor(
                rpm,
                data
            )
        )

        if data["boost"] <= 0.0:

            value -= (
                0.004
                * high_rpm
                * blend
            )

        else:

            value -= (
                0.003
                * high_rpm
                * blend
            )

        stress = (
            self._engine_stress_factor(
                data,
                characteristics
            )
        )

        value -= (
            0.0015
            * self._clamp(
                stress,
                0.0,
                1.0
            )
            * blend
        )

        minimum = (
            self.SAFE_MIN_BOOST
            if data["boost"] > 0
            else self.SAFE_MIN_NA
        )

        return self._clamp(
            value,
            minimum,
            self.SAFE_MAX_LAMBDA
        )

    # =========================================================
    # SMOOTHING
    # =========================================================

    def _smooth_table(
        self,
        table
    ):

        if not table:
            return table

        rows = len(
            table
        )

        cols = len(
            table[0]
        )

        result = [
            row[:]
            for row in table
        ]

        new_table = [
            row[:]
            for row in result
        ]

        center_weight = 0.96
        neighbour_weight = 0.04

        for r in range(
            rows
        ):

            for c in range(
                cols
            ):

                center = (
                    result[r][c]
                )

                neighbours = []

                if r > 0:

                    neighbours.append(
                        result[r - 1][c]
                    )

                if r < rows - 1:

                    neighbours.append(
                        result[r + 1][c]
                    )

                if c > 0:

                    neighbours.append(
                        result[r][c - 1]
                    )

                if c < cols - 1:

                    neighbours.append(
                        result[r][c + 1]
                    )

                if not neighbours:

                    new_table[r][c] = (
                        center
                    )

                    continue

                average = (
                    sum(
                        neighbours
                    )
                    / len(
                        neighbours
                    )
                )

                new_table[r][c] = (
                    center
                    * center_weight
                    + average
                    * neighbour_weight
                )

        return new_table

    # =========================================================
    # GENERATE
    # =========================================================

    def generate_table(
        self,
        open_window=True
    ):

        try:

            data = self._read_inputs()

            self.rpm_axis = (
                self._build_rpm_axis(
                    data["cols"],
                    data["idle_rpm"],
                    data["cutoff_rpm"],
                    data["torque_rpm"],
                    data["hp_rpm"]
                )
            )

            self.map_axis = (
                self._build_map_axis(
                    data["rows"],
                    data["boost"]
                )
            )

            if len(
                self.rpm_axis
            ) != data["cols"]:

                self.rpm_axis = [
                    int(
                        round(
                            data["idle_rpm"]
                            + (
                                data["cutoff_rpm"]
                                - data["idle_rpm"]
                            )
                            * i
                            / (
                                data["cols"]
                                - 1
                            )
                        )
                    )
                    for i in range(
                        data["cols"]
                    )
                ]

            if len(
                self.map_axis
            ) != data["rows"]:

                self.map_axis = [
                    round(
                        25.0
                        + (
                            self.ATMOSPHERIC_KPA
                            + data["boost"]
                            * self.PSI_TO_KPA
                            - 25.0
                        )
                        * i
                        / (
                            data["rows"]
                            - 1
                        ),
                        1
                    )
                    for i in range(
                        data["rows"]
                    )
                ]

            characteristics = (
                self._engine_characteristics(
                    data
                )
            )

            raw_table = []

            for map_kpa in self.map_axis:

                row = []

                for rpm in self.rpm_axis:

                    value = (
                        self._calculate_lambda(
                            rpm,
                            map_kpa,
                            data,
                            characteristics
                        )
                    )

                    row.append(
                        value
                    )

                raw_table.append(
                    row
                )

            self.lambda_table = (
                self._smooth_table(
                    raw_table
                )
            )

            minimum = (
                self.SAFE_MIN_BOOST
                if data["boost"] > 0
                else self.SAFE_MIN_NA
            )

            for r in range(
                len(
                    self.lambda_table
                )
            ):

                for c in range(
                    len(
                        self.lambda_table[r]
                    )
                ):

                    value = (
                        self.lambda_table[r][c]
                    )

                    value = max(
                        minimum,
                        min(
                            self.SAFE_MAX_LAMBDA,
                            value
                        )
                    )

                    self.lambda_table[r][c] = (
                        round(
                            value,
                            3
                        )
                    )

            self.status_label.setText(
                "Lambda table generated successfully."
            )

            if open_window:

                if (
                    self.result_window
                    is not None
                ):

                    try:
                        self.result_window.close()
                    except RuntimeError:
                        pass

                    self.result_window = None

                self.result_window = (
                    LambdaTableWindow(
                        self,
                        self.rpm_axis,
                        self.map_axis,
                        self.lambda_table,
                        data,
                        characteristics
                    )
                )

                self.result_window.setModal(
                    False
                )

                self.result_window.show()
                self.result_window.raise_()
                self.result_window.activateWindow()

                QApplication.processEvents()

            return True

        except Exception as e:

            QMessageBox.critical(
                self,
                "ASLAN TUNER",
                f"خطا در ساخت جدول:\n\n{str(e)}"
            )

            self.status_label.setText(
                "Generation failed."
            )

            return False

    # =========================================================
    # EXPORT
    # =========================================================

    def export_csv(self):

        if not self.lambda_table:

            QMessageBox.warning(
                self,
                "ASLAN TUNER",
                "ابتدا جدول Lambda را تولید کنید."
            )

            return

        path, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Export Lambda Table",
                "lambda_table.csv",
                "CSV Files (*.csv)"
            )
        )

        if not path:
            return

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

                writer.writerow(
                    [
                        "MAP / RPM"
                    ]
                    + self.rpm_axis
                )

                for map_value, row in zip(
                    self.map_axis,
                    self.lambda_table
                ):

                    writer.writerow(
                        [map_value]
                        + row
                    )

            QMessageBox.information(
                self,
                "ASLAN TUNER",
                "فایل CSV با موفقیت ذخیره شد."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "ASLAN TUNER",
                f"خطا در ذخیره فایل:\n\n{str(e)}"
            )

    # =========================================================
    # RESET
    # =========================================================

    def reset(self):

        if self.result_window is not None:

            try:
                self.result_window.close()
            except RuntimeError:
                pass

            self.result_window = None

        self.rows_input.setText("16")
        self.cols_input.setText("16")
        self.idle_input.setText("900")
        self.cutoff_input.setText("7000")
        self.hp_input.setText("100")
        self.hp_rpm_input.setText("5000")
        self.torque_input.setText("170")
        self.torque_rpm_input.setText("3000")
        self.displacement_input.setText("2000")
        self.boost_input.setText("0")

        self.rpm_axis = []
        self.map_axis = []
        self.lambda_table = []

        self.status_label.setText(
            "Ready."
        )


# =============================================================
# RESULT WINDOW
# =============================================================

class LambdaTableWindow(ASLANDialog):

    def __init__(
        self,
        parent,
        rpm_axis,
        map_axis,
        lambda_table,
        data,
        characteristics
    ):

        super().__init__(
            parent=parent,
            title="LAMBDA TARGET TABLE",
            window_title="ASLAN TUNER - LAMBDA TARGET TABLE",
            minimum_size=(1100, 650),
            size=(1400, 800)
        )

        self.rpm_axis = rpm_axis
        self.map_axis = map_axis
        self.lambda_table = lambda_table
        self.data = data
        self.characteristics = characteristics

        self.setStyleSheet("""
            QDialog {
                background-color: #151515;
                color: #eeeeee;
            }

            QLabel {
                color: #eeeeee;
            }

            QTableWidget {
                background-color: #171717;
                alternate-background-color: #1e1e1e;
                color: #eeeeee;
                gridline-color: #393939;
                border: 1px solid #383838;
                selection-background-color: #7d1116;
                selection-color: white;
            }

            QHeaderView::section {
                background-color: #252525;
                color: #e21b23;
                border: 1px solid #3c3c3c;
                padding: 6px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #242424;
                border: 1px solid #444444;
                border-radius: 7px;
                color: #eeeeee;
                padding: 9px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #351719;
                border: 1px solid #e21b23;
            }

            QPushButton:pressed {
                background-color: #d71920;
            }
        """)

        self._build_ui()

    # =========================================================
    # RESULT UI
    # =========================================================

    def _build_ui(self):

        layout = self.content_layout

        layout.setContentsMargins(
            18,
            16,
            18,
            16
        )

        layout.setSpacing(
            12
        )

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        title = QLabel(
            "ASLAN TUNER • LAMBDA TARGET TABLE"
        )

        title.setFont(
            QFont(
                "Arial",
                18,
                QFont.Bold
            )
        )

        title.setStyleSheet(
            "color: #e21b23;"
        )

        layout.addWidget(
            title
        )

        meta = QLabel(
            f"Engine: "
            f"{self.data['displacement']:.0f} cc   |   "
            f"Power: "
            f"{self.data['hp']:.1f} HP @ "
            f"{self.data['hp_rpm']:.0f} RPM   |   "
            f"Torque: "
            f"{self.data['torque']:.1f} Nm @ "
            f"{self.data['torque_rpm']:.0f} RPM   |   "
            f"Boost: "
            f"{self.data['boost']:.1f} PSI"
        )

        meta.setStyleSheet(
            "color: #999999;"
        )

        layout.addWidget(
            meta
        )

        # -----------------------------------------------------
        # TABLE
        # -----------------------------------------------------

        self.table = QTableWidget()

        self.table.setRowCount(
            len(
                self.map_axis
            )
        )

        self.table.setColumnCount(
            len(
                self.rpm_axis
            )
            + 1
        )

        headers = [
            "MAP kPa"
        ]

        headers += [
            str(x)
            for x in self.rpm_axis
        ]

        self.table.setHorizontalHeaderLabels(
            headers
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectItems
        )

        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.cellClicked.connect(
            self._cell_clicked
        )

        self._populate_table()

        layout.addWidget(
            self.table,
            1
        )

        # -----------------------------------------------------
        # SELECTED CELL
        # -----------------------------------------------------

        self.selected_label = QLabel(
            "یک سلول را انتخاب کنید."
        )

        self.selected_label.setStyleSheet("""
            QLabel {
                color: #bbbbbb;
                background-color: #202020;
                border: 1px solid #353535;
                border-radius: 7px;
                padding: 9px;
            }
        """)

        layout.addWidget(
            self.selected_label
        )

        # -----------------------------------------------------
        # BUTTONS
        # -----------------------------------------------------

        buttons = QHBoxLayout()

        copy_button = QPushButton(
            "COPY TABLE"
        )

        export_button = QPushButton(
            "EXPORT CSV"
        )

        close_button = QPushButton(
            "CLOSE"
        )

        copy_button.clicked.connect(
            self._copy_table
        )

        export_button.clicked.connect(
            self._export_csv
        )

        close_button.clicked.connect(
            self.close
        )

        buttons.addWidget(
            copy_button
        )

        buttons.addWidget(
            export_button
        )

        buttons.addStretch()

        buttons.addWidget(
            close_button
        )

        layout.addLayout(
            buttons
        )

    # =========================================================
    # TABLE
    # =========================================================

    def _populate_table(self):

        for r, map_value in enumerate(
            self.map_axis
        ):

            map_item = QTableWidgetItem(
                f"{map_value:.1f}"
            )

            map_item.setTextAlignment(
                Qt.AlignCenter
            )

            map_item.setForeground(
                QColor("#e21b23")
            )

            map_item.setFont(
                QFont(
                    "Arial",
                    9,
                    QFont.Bold
                )
            )

            self.table.setItem(
                r,
                0,
                map_item
            )

            for c, value in enumerate(
                self.lambda_table[r]
            ):

                item = QTableWidgetItem(
                    f"{value:.3f}"
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                if value >= 0.98:

                    item.setBackground(
                        QColor("#222222")
                    )

                    item.setForeground(
                        QColor("#eeeeee")
                    )

                elif value >= 0.94:

                    item.setBackground(
                        QColor("#352727")
                    )

                    item.setForeground(
                        QColor("#ffffff")
                    )

                elif value >= 0.90:

                    item.setBackground(
                        QColor("#4a2525")
                    )

                    item.setForeground(
                        QColor("#ffffff")
                    )

                elif value >= 0.85:

                    item.setBackground(
                        QColor("#6a2023")
                    )

                    item.setForeground(
                        QColor("#ffffff")
                    )

                else:

                    item.setBackground(
                        QColor("#8e171d")
                    )

                    item.setForeground(
                        QColor("#ffffff")
                    )

                self.table.setItem(
                    r,
                    c + 1,
                    item
                )

    # =========================================================
    # CELL CLICK
    # =========================================================

    def _cell_clicked(
        self,
        row,
        column
    ):

        if column == 0:

            self.selected_label.setText(
                f"MAP: "
                f"{self.map_axis[row]:.1f} kPa"
            )

            return

        rpm = self.rpm_axis[
            column - 1
        ]

        map_kpa = self.map_axis[
            row
        ]

        value = self.lambda_table[
            row
        ][
            column - 1
        ]

        load = (
            map_kpa
            / AFRLambdaCalculator.ATMOSPHERIC_KPA
        )

        self.selected_label.setText(
            f"RPM: {rpm}   |   "
            f"MAP: {map_kpa:.1f} kPa   |   "
            f"Load: {load:.2f}   |   "
            f"Target Lambda: {value:.3f}"
        )

    # =========================================================
    # COPY
    # =========================================================

    def _copy_table(self):

        lines = []

        header = [
            "MAP"
        ] + [
            str(x)
            for x in self.rpm_axis
        ]

        lines.append(
            "\t".join(
                header
            )
        )

        for map_value, row in zip(
            self.map_axis,
            self.lambda_table
        ):

            values = [
                f"{map_value:.1f}"
            ]

            values += [
                f"{x:.3f}"
                for x in row
            ]

            lines.append(
                "\t".join(
                    values
                )
            )

        text = "\n".join(
            lines
        )

        QApplication.clipboard().setText(
            text
        )

        QMessageBox.information(
            self,
            "ASLAN TUNER",
            "جدول با موفقیت کپی شد."
        )

    # =========================================================
    # EXPORT
    # =========================================================

    def _export_csv(self):

        path, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Export Lambda Table",
                "lambda_table.csv",
                "CSV Files (*.csv)"
            )
        )

        if not path:
            return

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

                writer.writerow(
                    [
                        "MAP / RPM"
                    ]
                    + self.rpm_axis
                )

                for map_value, row in zip(
                    self.map_axis,
                    self.lambda_table
                ):

                    writer.writerow(
                        [map_value]
                        + row
                    )

            QMessageBox.information(
                self,
                "ASLAN TUNER",
                "فایل CSV با موفقیت ذخیره شد."
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "ASLAN TUNER",
                f"خطا در ذخیره CSV:\n\n{str(e)}"
            )

    # =========================================================
    # CLOSE
    # =========================================================

    def closeEvent(
        self,
        event
    ):

        parent = self.parent()

        if isinstance(
            parent,
            AFRLambdaCalculator
        ):

            parent.result_window = None

        event.accept()