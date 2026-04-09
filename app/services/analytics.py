import logging


logger = logging.getLogger("analytics")


class AnalyticsService:
    def track(self, event_name: str, payload: dict) -> None:
        logger.info("analytics_event", extra={"event_name": event_name, "payload": payload})
