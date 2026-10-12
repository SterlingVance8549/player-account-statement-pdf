from datetime import datetime, timezone

from game_statement.models import (
    LiveEvent,
    ModerationItem,
    ModerationState,
    PlayerAsset,
    StatementExportRequest,
)
from game_statement.statement_renderer import render_statement


def test_statement_keeps_only_approved_assets_in_period() -> None:
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 9, 1, tzinfo=timezone.utc)
    request = StatementExportRequest(
        player_id="player-42",
        display_name="Mika",
        period_start=start,
        period_end=end,
        assets=[
            PlayerAsset(asset_id="a1", title="Sky Fortress", kind="map", created_at=start, moderation_state=ModerationState.APPROVED),
            PlayerAsset(asset_id="a2", title="Hidden Emote", kind="animation", created_at=start, moderation_state=ModerationState.PENDING),
            PlayerAsset(asset_id="a3", title="Old Banner", kind="image", created_at=datetime(2026, 7, 1, tzinfo=timezone.utc), moderation_state=ModerationState.APPROVED),
        ],
        live_events=[
            LiveEvent(event_id="e1", title="Build Night", started_at=start, ended_at=start, peak_viewers=184),
        ],
        moderation_queue=[
            ModerationItem(queue_id="q1", asset_id="a2", state=ModerationState.PENDING, submitted_at=start),
        ],
    )

    statement = render_statement(request)

    assert "Sky Fortress" in statement
    assert "Hidden Emote" not in statement
    assert "Old Banner" not in statement
    assert "Build Night: peak audience 184" in statement
    assert "Pending: 1" in statement

