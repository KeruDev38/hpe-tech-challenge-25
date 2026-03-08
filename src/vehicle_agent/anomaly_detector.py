"""
Anomaly detection system for vehicle telemetry.

Uses rule-based thresholds to detect failures and generate predictive alerts.
"""

from src.models.alerts import PredictiveAlert
from src.models.enums import AlertSeverity, FailureCategory
from src.models.telemetry import VehicleTelemetry


class AnomalyDetector:
    """Rule-based anomaly detection for vehicle telemetry."""

    def __init__(self, vehicle_id: str) -> None:
        """
        Initialize the anomaly detector.

        Args:
            vehicle_id: Unique identifier for the vehicle
        """
        self.vehicle_id = vehicle_id

    def analyze(self, telemetry: VehicleTelemetry) -> list[PredictiveAlert]:
        """
        Analyze telemetry and generate alerts for anomalies.

        Args:
            telemetry: Current vehicle telemetry data

        Returns:
            List of predictive alerts (may be empty)
        """
        alerts: list[PredictiveAlert] = []

        # Check all failure conditions
        alerts.extend(self._check_engine_temp(telemetry))
        alerts.extend(self._check_battery(telemetry))
        alerts.extend(self._check_fuel(telemetry))

        return alerts

    def _check_engine_temp(self, telemetry: VehicleTelemetry) -> list[PredictiveAlert]:
        """
        Check engine temperature for overheating.

        Thresholds from SIMULATION.md:
        - WARNING: > 105°C
        - CRITICAL: > 120°C
        """
        alerts: list[PredictiveAlert] = []
        temp = telemetry.engine_temp_celsius

        if temp > 120.0:
            alerts.append(
                PredictiveAlert(
                    vehicle_id=self.vehicle_id,
                    timestamp=telemetry.timestamp,
                    severity=AlertSeverity.CRITICAL,
                    category=FailureCategory.ENGINE,
                    component="engine",
                    failure_probability=0.95,
                    confidence=0.98,
                    predicted_failure_min_hours=0.5,
                    predicted_failure_max_hours=2.0,
                    predicted_failure_likely_hours=1.0,
                    can_complete_current_mission=False,
                    safe_to_operate=False,
                    recommended_action="STOP IMMEDIATELY - Engine damage imminent. Activate limp mode.",
                    contributing_factors=[
                        f"engine_temp_celsius={temp:.1f}°C (critical threshold 120°C)",
                    ],
                    related_telemetry={
                        "engine_temp_celsius": temp,
                    },
                )
            )
        elif temp > 105.0:
            alerts.append(
                PredictiveAlert(
                    vehicle_id=self.vehicle_id,
                    timestamp=telemetry.timestamp,
                    severity=AlertSeverity.WARNING,
                    category=FailureCategory.ENGINE,
                    component="engine",
                    failure_probability=0.65,
                    confidence=0.85,
                    predicted_failure_min_hours=2.0,
                    predicted_failure_max_hours=8.0,
                    predicted_failure_likely_hours=4.0,
                    can_complete_current_mission=True,
                    safe_to_operate=True,
                    recommended_action="Monitor engine temperature closely. Schedule inspection.",
                    contributing_factors=[
                        f"engine_temp_celsius={temp:.1f}°C (warning threshold 105°C)",
                    ],
                    related_telemetry={
                        "engine_temp_celsius": temp,
                    },
                )
            )

        return alerts

    def _check_battery(self, telemetry: VehicleTelemetry) -> list[PredictiveAlert]:
        """
        Check battery voltage.

        Thresholds:
        - WARNING: < 12.0V
        - CRITICAL: < 11.5V
        """
        alerts: list[PredictiveAlert] = []
        volts = telemetry.battery_voltage

        if volts < 11.5:
            alerts.append(
                PredictiveAlert(
                    vehicle_id=self.vehicle_id,
                    timestamp=telemetry.timestamp,
                    severity=AlertSeverity.CRITICAL,
                    category=FailureCategory.ELECTRICAL,
                    component="battery",
                    failure_probability=0.95,
                    confidence=0.98,
                    predicted_failure_min_hours=0.1,
                    predicted_failure_max_hours=1.0,
                    predicted_failure_likely_hours=0.5,
                    can_complete_current_mission=False,
                    safe_to_operate=False,
                    recommended_action="STOP IMMEDIATELY - Critical electrical failure.",
                    contributing_factors=[
                        f"battery_voltage={volts:.1f}V (critical threshold 11.5V)",
                    ],
                    related_telemetry={
                        "battery_voltage": volts,
                    },
                )
            )
        elif volts < 12.0:
            alerts.append(
                PredictiveAlert(
                    vehicle_id=self.vehicle_id,
                    timestamp=telemetry.timestamp,
                    severity=AlertSeverity.WARNING,
                    category=FailureCategory.ELECTRICAL,
                    component="battery",
                    failure_probability=0.65,
                    confidence=0.85,
                    predicted_failure_min_hours=1.0,
                    predicted_failure_max_hours=4.0,
                    predicted_failure_likely_hours=2.0,
                    can_complete_current_mission=True,
                    safe_to_operate=True,
                    recommended_action="Monitor electrical system. Check alternator.",
                    contributing_factors=[
                        f"battery_voltage={volts:.1f}V (warning threshold 12.0V)",
                    ],
                    related_telemetry={
                        "battery_voltage": volts,
                    },
                )
            )

        return alerts

    def _check_fuel(self, telemetry: VehicleTelemetry) -> list[PredictiveAlert]:
        """
        Check fuel level.

        Thresholds:
        - WARNING: < 15%
        - CRITICAL: < 5%
        """
        alerts: list[PredictiveAlert] = []
        fuel = telemetry.fuel_level_percent

        if fuel < 5.0:
            alerts.append(
                PredictiveAlert(
                    vehicle_id=self.vehicle_id,
                    timestamp=telemetry.timestamp,
                    severity=AlertSeverity.CRITICAL,
                    category=FailureCategory.FUEL,
                    component="fuel",
                    failure_probability=0.99,
                    confidence=0.99,
                    predicted_failure_min_hours=0.1,
                    predicted_failure_max_hours=0.5,
                    predicted_failure_likely_hours=0.2,
                    can_complete_current_mission=False,
                    safe_to_operate=False,
                    recommended_action="REFUEL IMMEDIATELY - Vehicle will stop soon.",
                    contributing_factors=[
                        f"fuel_level_percent={fuel:.1f}% (critical threshold 5%)",
                    ],
                    related_telemetry={
                        "fuel_level_percent": fuel,
                    },
                )
            )
        elif fuel < 15.0:
            alerts.append(
                PredictiveAlert(
                    vehicle_id=self.vehicle_id,
                    timestamp=telemetry.timestamp,
                    severity=AlertSeverity.WARNING,
                    category=FailureCategory.FUEL,
                    component="fuel",
                    failure_probability=0.80,
                    confidence=0.90,
                    predicted_failure_min_hours=0.5,
                    predicted_failure_max_hours=2.0,
                    predicted_failure_likely_hours=1.0,
                    can_complete_current_mission=True,
                    safe_to_operate=True,
                    recommended_action="Refuel soon. Low fuel level warning.",
                    contributing_factors=[
                        f"fuel_level_percent={fuel:.1f}% (warning threshold 15%)",
                    ],
                    related_telemetry={
                        "fuel_level_percent": fuel,
                    },
                )
            )

        return alerts
