"""AI-driven city crime prediction generator for Project AEGIS."""

import structlog

from src.core.time import Clock
from src.ml.predictor import CrimePredictor
from src.models.alerts import CrimePrediction
from src.models.enums import AlertSeverity
from src.orchestrator.agent import OrchestratorAgent
from src.vehicle_agent.config import SF_LAT_MAX, SF_LAT_MIN, SF_LON_MAX, SF_LON_MIN

logger = structlog.get_logger(__name__)


class EmergencyGenerator:
    """Generates non-dispatching crime predictions across city neighborhoods."""

    def __init__(
        self,
        orchestrator: OrchestratorAgent,
        clock: Clock,
        check_interval_seconds: float = 1800.0,  # 30 minutes by default
    ) -> None:
        self.orchestrator = orchestrator
        self.clock = clock
        self.check_interval_seconds = check_interval_seconds
        self.running = False

        self.predictor = CrimePredictor(confidence_threshold=0.90)
        self.active_predictions: dict[str, str] = {}

    async def start(self) -> None:
        """Start the ML generation loop."""
        self.running = True
        logger.info("predictive_generator_started", start_sim_time=self.clock.now().isoformat())

        while self.running:
            try:
                await self._generate_predictive_emergencies()
            except Exception as e:
                logger.error("predictive_generator_error", error=str(e), exc_info=True)

            # Let the clock abstraction handle the sleeping/advancing
            await self.clock.sleep(self.check_interval_seconds)

    def stop(self) -> None:
        self.running = False
        logger.info("predictive_generator_stopped")

    async def _generate_predictive_emergencies(self) -> None:
        if not self.predictor.is_ready:
            return

        current_time = self.clock.now()
        recommendations = self.predictor.predict_current_risk(current_time)
        current_high_risk_neighborhoods = {rec["neighborhood"] for rec in recommendations}

        # Resolve expired predictions
        expired_neighborhoods = (
            set(self.active_predictions.keys()) - current_high_risk_neighborhoods
        )
        for hood in expired_neighborhoods:
            prediction_id = self.active_predictions[hood]
            try:
                await self.orchestrator.resolve_crime_prediction(prediction_id)
                logger.info(
                    "ai_prediction_resolved",
                    neighborhood=hood,
                    prediction_id=prediction_id,
                )
            except Exception as e:
                logger.warning("failed_to_resolve_ai_prediction", error=str(e))
            del self.active_predictions[hood]

        # Create new predictions
        for rec in recommendations:
            neighborhood = rec["neighborhood"]
            if neighborhood in self.active_predictions:
                continue

            prob = rec["risk_probability"]
            severity = AlertSeverity.CRITICAL if prob > 0.95 else AlertSeverity.WARNING

            lat = max(SF_LAT_MIN, min(SF_LAT_MAX, rec["latitude"]))
            lon = max(SF_LON_MIN, min(SF_LON_MAX, rec["longitude"]))
            sim_time_str = current_time.strftime("%A %H:%M")
            predicted_crime_type = str(rec["common_crime_type"])

            prediction = CrimePrediction(
                neighborhood=neighborhood,
                timestamp=self.clock.now(),
                risk_probability=prob,
                confidence=prob,
                severity=severity,
                latitude=lat,
                longitude=lon,
                predicted_crime_type=predicted_crime_type,
                description=(
                    f"AI Prediction [{sim_time_str}]: High risk of "
                    f"{predicted_crime_type} ({prob:.1%} confidence)"
                ),
                source="ai_crime_predictor",
            )

            logger.info("ai_crime_prediction_created", neighborhood=neighborhood, probability=prob)
            await self.orchestrator.process_crime_prediction(prediction)
            self.active_predictions[neighborhood] = prediction.prediction_id
