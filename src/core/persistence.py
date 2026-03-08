"""Persistence contracts for orchestrator side effects."""

from __future__ import annotations

from typing import Protocol

from src.models.alerts import PredictiveAlert
from src.models.dispatch import Dispatch
from src.models.telemetry import VehicleTelemetry


class TelemetrySink(Protocol):
    """Consumes telemetry records for persistence or analytics."""

    async def enqueue(self, telemetry: VehicleTelemetry, vehicle_id: str) -> None:
        """Accept one telemetry record for asynchronous persistence."""

    async def flush(self) -> None:
        """Flush all pending records."""

    async def close(self) -> None:
        """Release resources and flush pending data."""


class AlertSink(Protocol):
    """Consumes alerts for persistence."""

    async def persist_alert(self, alert: PredictiveAlert, vehicle_id: str) -> None:
        """Persist one alert entry."""


class EmergencyAnalyticsSink(Protocol):
    """Consumes emergency lifecycle analytics for dashboards and reporting."""

    async def persist_dispatch_snapshot(self, emergency_id: str, dispatch: Dispatch) -> None:
        """Persist/update dispatch-level ETA and assignment analytics."""

    async def append_timeline_event(
        self,
        emergency_id: str,
        phase: str,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        """Append a single emergency timeline event."""
