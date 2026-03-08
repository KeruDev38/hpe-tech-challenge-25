"""
SQLAlchemy ORM models mapped to the PostgreSQL schema.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class VehicleRecord(Base):
    """Vehicle metadata and latest known state."""

    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    registration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), server_default="active")
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    telemetry_records: Mapped[list["TelemetryRecord"]] = relationship(
        "TelemetryRecord", back_populates="vehicle", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["AlertRecord"]] = relationship(
        "AlertRecord", back_populates="vehicle", cascade="all, delete-orphan"
    )


class TelemetryRecord(Base):
    """Time-series telemetry data."""

    __tablename__ = "telemetry"

    # Composite primary key according to init-db.sql: (vehicle_id, timestamp, id)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("vehicles.vehicle_id"), primary_key=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)

    # Location data
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Vehicle metrics
    engine_temp: Mapped[float | None] = mapped_column(Float, nullable=True)
    oil_pressure: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    tire_pressure: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Operational data
    rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    throttle_position: Mapped[float | None] = mapped_column(Float, nullable=True)
    brake_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    odometer: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Sensor data
    vibration_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    vibration_z: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Raw data
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    vehicle: Mapped["VehicleRecord"] = relationship(
        "VehicleRecord", back_populates="telemetry_records"
    )

    __table_args__ = (
        Index("idx_telemetry_timestamp", "timestamp", postgresql_using="btree"),
        Index(
            "idx_telemetry_vehicle_timestamp", "vehicle_id", "timestamp", postgresql_using="btree"
        ),
    )


class AlertRecord(Base):
    """Predictive alerts and anomalies."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("vehicles.vehicle_id"), nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Predictive metrics
    probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Context
    telemetry_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(20), server_default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    vehicle: Mapped["VehicleRecord"] = relationship("VehicleRecord", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_vehicle_id", "vehicle_id", postgresql_using="btree"),
        Index("idx_alerts_detected_at", "detected_at", postgresql_using="btree"),
        Index("idx_alerts_severity", "severity", postgresql_using="btree"),
        Index("idx_alerts_status", "status", postgresql_using="btree"),
    )


class EmergencyAnalyticsRecord(Base):
    """Denormalized emergency analytics snapshot for dashboard trend charts."""

    __tablename__ = "emergency_analytics"

    emergency_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    emergency_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_units: Mapped[int] = mapped_column(nullable=False, default=0)
    acknowledged_units: Mapped[int] = mapped_column(nullable=False, default=0)
    arrived_units: Mapped[int] = mapped_column(nullable=False, default=0)
    avg_estimated_eta_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_actual_eta_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_eta_error_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    coordination_status: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_emergency_analytics_status", "status", postgresql_using="btree"),
        Index("idx_emergency_analytics_type", "emergency_type", postgresql_using="btree"),
        Index("idx_emergency_analytics_dispatched", "dispatched_at", postgresql_using="btree"),
    )


class EmergencyTimelineRecord(Base):
    """Append-only emergency timeline events with phase transitions."""

    __tablename__ = "emergency_timeline"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emergency_id: Mapped[str] = mapped_column(String(100), nullable=False)
    phase: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    event_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_emergency_timeline_emergency", "emergency_id", postgresql_using="btree"),
        Index("idx_emergency_timeline_event_ts", "event_ts", postgresql_using="btree"),
        Index(
            "idx_emergency_timeline_emergency_ts",
            "emergency_id",
            "event_ts",
            postgresql_using="btree",
        ),
    )
