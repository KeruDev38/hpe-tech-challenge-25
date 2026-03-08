"""Unit tests for emergency duration hints and coordination tasks."""

from datetime import UTC, datetime

import pytest

from src.core.time import FastForwardClock
from src.models.dispatch import VehicleStatusSnapshot
from src.models.emergency import Emergency, EmergencySeverity, EmergencyType, UnitsRequired
from src.models.enums import OperationalStatus, VehicleType
from src.models.vehicle import Location
from src.orchestrator.emergency_service import EmergencyService


def _fleet() -> dict[str, VehicleStatusSnapshot]:
    return {
        "AMB-001": VehicleStatusSnapshot(
            vehicle_id="AMB-001",
            vehicle_type=VehicleType.AMBULANCE,
            operational_status=OperationalStatus.IDLE,
            location=Location(
                latitude=37.7749,
                longitude=-122.4194,
                timestamp=datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC),
            ),
        )
    }


def _emergency(description: str) -> Emergency:
    return Emergency(
        emergency_type=EmergencyType.MEDICAL,
        severity=EmergencySeverity.HIGH,
        location=Location(
            latitude=37.7750,
            longitude=-122.4193,
            timestamp=datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC),
        ),
        description=description,
        units_required=UnitsRequired(ambulances=1),
        created_at=datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC),
    )


@pytest.mark.unit
def test_duration_hint_increases_eta_for_complex_incident() -> None:
    """Subtype hints should increase planned duration for complex emergencies."""
    clock = FastForwardClock(start_at=datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC))
    service = EmergencyService(_fleet(), clock=clock)

    simple = _emergency("minor injury assistance")
    complex_case = _emergency("cardiac arrest with multi-vehicle pileup")

    simple_eta = service._planned_duration_minutes(simple)
    complex_eta = service._planned_duration_minutes(complex_case)

    assert complex_eta > simple_eta


@pytest.mark.unit
def test_coordination_tasks_initialize_for_dispatched_emergency() -> None:
    """Processing emergency should initialize coordination tasks by type."""
    clock = FastForwardClock(start_at=datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC))
    service = EmergencyService(_fleet(), clock=clock)

    emergency = _emergency("cardiac arrest")
    dispatch = service.process_emergency(emergency)

    assert dispatch.units
    assert emergency.coordination_status
    assert "scene_secure" in emergency.coordination_status
    assert "patient_stabilized" in emergency.coordination_status
    assert all(done is False for done in emergency.coordination_status.values())


@pytest.mark.unit
def test_coordination_tasks_complete_and_report_done() -> None:
    """All coordination tasks should become complete when marked one by one."""
    clock = FastForwardClock(start_at=datetime(2026, 3, 5, 9, 0, 0, tzinfo=UTC))
    service = EmergencyService(_fleet(), clock=clock)

    emergency = _emergency("cardiac arrest")
    service.process_emergency(emergency)

    for task in list(emergency.coordination_status.keys()):
        changed = service.mark_coordination_task_complete(emergency.emergency_id, task)
        assert changed is True

    assert service.all_coordination_tasks_completed(emergency.emergency_id) is True
