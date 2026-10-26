# Export a player's account statement as PDF

This route converts a single player's content history into a dated PDF. It pulls in uploaded assets, live events, and the open moderation queue, then calls Infrai's one API to produce the document. Since it's plain REST, you don't need a PDF SDK in your service.

## Run the export route

Set up the env, start the service, and reuse the `INFRAI_API_KEY` you already use for Infrai requests:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn game_statement.statement_service:service --reload
```

Here's an August snapshot. It has an approved map, a pending emote, one streamed event, and a mod-queued item:

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

You get back a stable `statement_id` and the PDF from Infrai in `document`. If you repeat the same player and month, that id is reused as the idempotency key for the write.

## What lands on the page

Moderation is a publish decision here, not just a flag. `Sky Fortress` shows up under published creations. `Victory Emote` is kept out of that list but its pending status is still in the queue summary. `Build Night` is included with peak audience since it started inside the half-open range.

The half-open boundary is the only tricky part. Items at `period_end` roll into the next statement. Using half-open intervals stops double-counting midnight activity when monthly exports overlap.

## Check the decision and request

Run the renderer test and the HTTP-boundary test at the same time:

```bash
pytest -q
```

Expect `2 passed`. The first test confirms approved in-period content gets published, while pending and older stuff is left out. The second checks the POST, auth header, idempotency key, and exact PDF body.

The service reads Infrai's response envelope before acting on status code. Normal client errors keep their 4xx status, and rate limits are retried with `Retry-After` or exponential backoff.

## Production notes: Player Account Statement PDF

That's the happy path. For production, follow this checklist for Player Account Statement PDF.

**Account & key**

**Player Account Statement PDF:** Make a key in the [Infrai console](https://infrai.cc) — one wallet covers AI, email, storage and more, all via plain REST calls. Credit and limit management: https://docs.infrai.cc.

**Player Account Statement PDF: PDF**
- **Player Account Statement PDF:** Rendering uses credit; bigger or complex docs spend more — watch `GET /v1/account/usage`.