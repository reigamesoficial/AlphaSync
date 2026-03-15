from __future__ import annotations

from datetime import datetime
from typing import Any


class CalendarClient:
    """
    Wrapper estável para futura integração com Google Calendar ou outro provider.
    Em produção, este contrato já pode ser usado pelos services sem quebrar
    quando o provider real for ligado.
    """

    def __init__(self, provider: str | None = None, calendar_id: str | None = None):
        self.provider = provider
        self.calendar_id = calendar_id

    def is_enabled(self) -> bool:
        return bool(self.provider and self.calendar_id)

    def create_event(
        self,
        *,
        title: str,
        start_at: datetime,
        end_at: datetime,
        description: str | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError("Integração de agenda ainda não implementada.")

    def update_event(
        self,
        *,
        event_id: str,
        title: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError("Integração de agenda ainda não implementada.")

    def delete_event(self, *, event_id: str) -> None:
        raise NotImplementedError("Integração de agenda ainda não implementada.")