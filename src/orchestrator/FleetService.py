from datetime import datetime
from typing import Optional

from src.models.dispatch import VehicleStatusSnapshot
from src.models.enums import OperationalStatus, VehicleType
from src.models.telemetry import VehicleTelemetry
from src.models.vehicle import Location
from src.orchestrator.agent import _infer_vehicle_type


class FleetService:
    def __init__(self) -> None:
        self.fleet: dict[str, VehicleStatusSnapshot] = {}

        def process_telemetry(
            self, telemetry: VehicleTelemetry
        ) -> tuple[bool, Optional[VehicleType]]:
            """
            Update fleet state from telemetry.
            Returns a tuple: (is_new_vehicle: bool, vehicle_type: Optional[VehicleType])
            """
            vehicle_id = telemetry.vehicle_id
            is_new = False
            vehicle_type = None

            snap = self.fleet.get(vehicle_id)
            if snap is None:
                is_new = True
                vehicle_type = _infer_vehicle_type(vehicle_id)
                snap = VehicleStatusSnapshot(
                    vehicle_id=vehicle_id,
                    vehicle_type=vehicle_type,
                    operational_status=OperationalStatus.IDLE,
                )
                self.fleet[vehicle_id] = snap

            # Update last seen timestamp
            snap.last_seen_at = datetime.utcnow()

            # Update location
            try:
                snap.location = Location(
                    latitude=telemetry.latitude,
                    longitude=telemetry.longitude,
                    timestamp=telemetry.timestamp,
                )
            except Exception:
                pass  # Location parse failure is non-fatal

            # Update key health metrics
            snap.battery_voltage = float(telemetry.battery_voltage)
            snap.fuel_level_percent = float(telemetry.fuel_level_percent)

            return is_new, vehicle_type
