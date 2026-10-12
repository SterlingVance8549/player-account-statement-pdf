from collections import Counter
from hashlib import sha256

from .models import ModerationState, StatementExportRequest


def statement_id_for(request: StatementExportRequest) -> str:
    identity = f"{request.player_id}:{request.period_start.isoformat()}:{request.period_end.isoformat()}"
    return f"statement-{sha256(identity.encode()).hexdigest()[:16]}"


def render_statement(request: StatementExportRequest) -> str:
    visible_assets = [
        asset
        for asset in request.assets
        if asset.moderation_state is ModerationState.APPROVED
        and request.period_start <= asset.created_at < request.period_end
    ]
    events = [
        event
        for event in request.live_events
        if request.period_start <= event.started_at < request.period_end
    ]
    queue_counts = Counter(item.state.value for item in request.moderation_queue)

    lines = [
        f"# Account statement for {request.display_name}",
        "",
        f"Player ID: `{request.player_id}`",
        f"Period: {request.period_start.date()} to {request.period_end.date()}",
        "",
        "## Published player creations",
    ]
    if visible_assets:
        lines.extend(
            f"- {asset.title} ({asset.kind}), created {asset.created_at.date()}"
            for asset in visible_assets
        )
    else:
        lines.append("No approved creations in this period.")

    lines.extend(["", "## Live events"])
    if events:
        lines.extend(
            f"- {event.title}: peak audience {event.peak_viewers}"
            for event in events
        )
    else:
        lines.append("No live events in this period.")

    lines.extend(
        [
            "",
            "## Moderation queue snapshot",
            f"- Approved: {queue_counts[ModerationState.APPROVED.value]}",
            f"- Pending: {queue_counts[ModerationState.PENDING.value]}",
            f"- Blocked: {queue_counts[ModerationState.BLOCKED.value]}",
        ]
    )
    return "\n".join(lines)

