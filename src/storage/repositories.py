"""
Repository classes for database operations.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alerts import PredictiveAlert
from src.models.dispatch import Dispatch
from src.models.telemetry import VehicleTelemetry
from src.storage.models import (
    AlertRecord,
    EmergencyAnalyticsRecord,
    EmergencyTimelineRecord,
    TelemetryRecord,
    VehicleRecord,
)


class TelemetryRepository:
    """Repository for telemetry data operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_telemetry(self, telemetry: VehicleTelemetry, vehicle_id: str) -> None:
        """
        Save a telemetry record to the database.

        Args:
            telemetry: The telemetry model to save.
            vehicle_id: The ID of the vehicle emitting this telemetry.
        """
        record = TelemetryRecord(
            vehicle_id=vehicle_id,
            timestamp=telemetry.timestamp,
            latitude=telemetry.latitude,
            longitude=telemetry.longitude,
            speed=telemetry.speed_kmh,
            engine_temp=telemetry.engine_temp_celsius,
            battery_voltage=telemetry.battery_voltage,
            fuel_level=telemetry.fuel_level_percent,
            odometer=telemetry.odometer_km,
        )
        self.session.add(record)

    async def upsert_vehicle(self, vehicle_id: str, vehicle_type: str, status: str) -> None:
        """
        Insert or update vehicle metadata.
        """
        stmt = insert(VehicleRecord).values(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            status=status,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["vehicle_id"],
            set_={
                "vehicle_type": stmt.excluded.vehicle_type,
                "status": stmt.excluded.status,
            },
        )
        await self.session.execute(stmt)


class AlertRepository:
    """Repository for predictive alerts operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_alert(self, alert: PredictiveAlert, vehicle_id: str) -> None:
        """
        Save an alert record to the database.

        Args:
            alert: The predictive alert to save.
            vehicle_id: The ID of the vehicle experiencing the alert.
        """
        record = AlertRecord(
            vehicle_id=vehicle_id,
            alert_type=alert.category.value,
            severity=alert.severity.value,
            title=f"Alert: {alert.category.value} - {alert.component}",
            description=alert.recommended_action,
            probability=alert.failure_probability,
            confidence=alert.confidence,
            detected_at=alert.timestamp,
            telemetry_snapshot=alert.related_telemetry,
            status="active",
        )
        self.session.add(record)


class EmergencyAnalyticsRepository:
    """Repository for emergency timeline and analytics snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_dispatch_snapshot(
        self,
        emergency_id: str,
        emergency_type: str,
        severity: int,
        status: str,
        dispatch: Dispatch,
        coordination_status: dict[str, bool],
        resolved_at: datetime | None,
        dismissed_at: datetime | None,
    ) -> None:
        estimated_etas = [
            u.estimated_eta_minutes for u in dispatch.units if u.estimated_eta_minutes is not None
        ]

        actual_etas = []
        eta_errors = []
        for unit in dispatch.units:
            if unit.actual_arrival_at is not None and dispatch.dispatched_at is not None:
                actual_etas.append(
                    (unit.actual_arrival_at - dispatch.dispatched_at).total_seconds() / 60.0
                )
            if unit.eta_error_minutes is not None:
                eta_errors.append(unit.eta_error_minutes)

        stmt = insert(EmergencyAnalyticsRecord).values(
            emergency_id=emergency_id,
            emergency_type=emergency_type,
            severity=severity,
            status=status,
            dispatched_at=dispatch.dispatched_at,
            resolved_at=resolved_at,
            dismissed_at=dismissed_at,
            assigned_units=len(dispatch.units),
            acknowledged_units=sum(1 for u in dispatch.units if u.acknowledged),
            arrived_units=sum(1 for u in dispatch.units if u.actual_arrival_at is not None),
            avg_estimated_eta_minutes=(
                sum(estimated_etas) / len(estimated_etas) if estimated_etas else None
            ),
            avg_actual_eta_minutes=(sum(actual_etas) / len(actual_etas) if actual_etas else None),
            avg_eta_error_minutes=(sum(eta_errors) / len(eta_errors) if eta_errors else None),
            coordination_status=coordination_status,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["emergency_id"],
            set_={
                "emergency_type": stmt.excluded.emergency_type,
                "severity": stmt.excluded.severity,
                "status": stmt.excluded.status,
                "dispatched_at": stmt.excluded.dispatched_at,
                "resolved_at": stmt.excluded.resolved_at,
                "dismissed_at": stmt.excluded.dismissed_at,
                "assigned_units": stmt.excluded.assigned_units,
                "acknowledged_units": stmt.excluded.acknowledged_units,
                "arrived_units": stmt.excluded.arrived_units,
                "avg_estimated_eta_minutes": stmt.excluded.avg_estimated_eta_minutes,
                "avg_actual_eta_minutes": stmt.excluded.avg_actual_eta_minutes,
                "avg_eta_error_minutes": stmt.excluded.avg_eta_error_minutes,
                "coordination_status": stmt.excluded.coordination_status,
            },
        )
        await self.session.execute(stmt)

    async def append_timeline_event(
        self,
        emergency_id: str,
        phase: str,
        event_type: str,
        event_ts: datetime,
        payload: dict[str, object],
    ) -> None:
        self.session.add(
            EmergencyTimelineRecord(
                emergency_id=emergency_id,
                phase=phase,
                event_type=event_type,
                event_ts=event_ts,
                payload_json=payload,
            )
        )

    async def get_timeline(self, emergency_id: str) -> list[EmergencyTimelineRecord]:
        stmt = (
            select(EmergencyTimelineRecord)
            .where(EmergencyTimelineRecord.emergency_id == emergency_id)
            .order_by(EmergencyTimelineRecord.event_ts.asc(), EmergencyTimelineRecord.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_trends(self) -> dict[str, object]:
        """Aggregate emergency analytics for dashboard trend charts."""
        by_status_stmt = (
            select(
                EmergencyAnalyticsRecord.status, func.count(EmergencyAnalyticsRecord.emergency_id)
            )
            .group_by(EmergencyAnalyticsRecord.status)
            .order_by(EmergencyAnalyticsRecord.status.asc())
        )
        by_type_stmt = (
            select(
                EmergencyAnalyticsRecord.emergency_type,
                func.count(EmergencyAnalyticsRecord.emergency_id),
            )
            .group_by(EmergencyAnalyticsRecord.emergency_type)
            .order_by(EmergencyAnalyticsRecord.emergency_type.asc())
        )
        summary_stmt = select(
            func.avg(EmergencyAnalyticsRecord.avg_estimated_eta_minutes),
            func.avg(EmergencyAnalyticsRecord.avg_actual_eta_minutes),
            func.avg(EmergencyAnalyticsRecord.avg_eta_error_minutes),
            func.avg(EmergencyAnalyticsRecord.assigned_units),
            func.avg(EmergencyAnalyticsRecord.acknowledged_units),
            func.avg(EmergencyAnalyticsRecord.arrived_units),
        )

        by_status_rows = await self.session.execute(by_status_stmt)
        by_type_rows = await self.session.execute(by_type_stmt)
        summary_row = (await self.session.execute(summary_stmt)).one()

        return {
            "counts_by_status": [
                {"status": status, "count": int(count)} for status, count in by_status_rows.all()
            ],
            "counts_by_type": [
                {"emergency_type": emergency_type, "count": int(count)}
                for emergency_type, count in by_type_rows.all()
            ],
            "averages": {
                "estimated_eta_minutes": float(summary_row[0])
                if summary_row[0] is not None
                else None,
                "actual_eta_minutes": float(summary_row[1]) if summary_row[1] is not None else None,
                "eta_error_minutes": float(summary_row[2]) if summary_row[2] is not None else None,
                "assigned_units": float(summary_row[3]) if summary_row[3] is not None else None,
                "acknowledged_units": float(summary_row[4]) if summary_row[4] is not None else None,
                "arrived_units": float(summary_row[5]) if summary_row[5] is not None else None,
            },
        }
