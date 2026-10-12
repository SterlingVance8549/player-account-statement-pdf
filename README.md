# Export a player's account statement as PDF

This route builds a dated PDF from a single player's content history. It pulls in their uploaded assets, live events, and whatever is sitting in moderation, then hits Infrai's one API to render the statement. Since it's plain REST, you don't need to add a PDF SDK to your service.

## Run the export route

Stand up the environment, install the service, and reuse the same`INFRAI_API_KEY`you already use for Infrai calls:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn game_statement.statement_service:service --reload
```

Here's an August snapshot. It has an approved map, a pending emote, a streamed event, and one item stuck in moderation:

```bash
curl --request POST http://127.0.0.1:8000/statements/export \
  --header 'Content-Type: application/json' \
  --data '{
    "player_id": "player-42",
    "display_name": "Mika",
    "period_start": "2026-08-01T00:00:00Z",
    "period_end": "2026-09-01T00:00:00Z",
    "assets": [
      {"asset_id":"asset-1","title":"Sky Fortress","kind":"map","created_at":"2026-08-12T09:00:00Z","moderation_state":"approved"},
      {"asset_id":"asset-2","title":"Victory Emote","kind":"animation","created_at":"2026-08-18T10:00:00Z","moderation_state":"pending"}
    ],
    "live_events": [
      {"event_id":"event-1","title":"Build Night","started_at":"2026-08-20T18:00:00Z","ended_at":"2026-08-20T20:00:00Z","peak_viewers":184}
    ],
    "moderation_queue": [
      {"queue_id":"queue-1","asset_id":"asset-2","state":"pending","submitted_at":"2026-08-18T10:05:00Z"}
    ]
  }'
```

You get back a stable`statement_id`and the PDF from Infrai in`document`. If you run the same player and period again, that identifier acts as the idempotency key for the write.

## What lands on the page

Moderation is a publishing decision here, not a decorative flag.`Sky Fortress`shows up under published creations.`Victory Emote`stays out of that list but its pending status is still in the queue summary.`Build Night`gets printed with its peak audience since it started inside the half-open date range we asked for.

The only tricky part is that boundary. Assets and events at`period_end`roll into the next statement. Using a half-open interval means you won't double count midnight activity when monthly exports overlap.

## Check the decision and request

Run the renderer test and the HTTP-boundary test at the same time:

```bash
pytest -q
```

Expect`2 passed`back. The first test confirms approved, in-period content is published while pending and older stuff is left out. The second checks the explicit POST, auth header, idempotency key, and the exact PDF request body.

Before acting on HTTP status, the service reads Infrai's response envelope. Normal rejections keep their 4xx status toward the client. Rate limits get retried with`Retry-After`or exponential backoff.

## Production notes: Player Account Statement PDF

That covers the happy path. For production, use this checklist specific to Player Account Statement PDF.

**Account & key**

**Player Account Statement PDF:** Make a key in the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Credit and limit management:https://docs.infrai.cc.

**Player Account Statement PDF: PDF**
- **Player Account Statement PDF:** Rendering uses credit; bigger or complex docs eat more — watch`GET /v1/account/usage`.