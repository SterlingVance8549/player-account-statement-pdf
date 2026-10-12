from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ModerationState(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    BLOCKED = "blocked"


class PlayerAsset(BaseModel):
    asset_id: str
    title: str
    kind: str
    created_at: datetime
    moderation_state: ModerationState


class LiveEvent(BaseModel):
    event_id: str
    title: str
    started_at: datetime
    ended_at: datetime
    peak_viewers: int = Field(ge=0)


class ModerationItem(BaseModel):
    queue_id: str
    asset_id: str
    state: ModerationState
    submitted_at: datetime


class StatementExportRequest(BaseModel):
    player_id: str
    display_name: str
    period_start: datetime
    period_end: datetime
    assets: list[PlayerAsset] = Field(default_factory=list)
    live_events: list[LiveEvent] = Field(default_factory=list)
    moderation_queue: list[ModerationItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_period(self) -> "StatementExportRequest":
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be later than period_start")
        return self


class StatementExportResponse(BaseModel):
    statement_id: str
    document: dict[str, Any]

