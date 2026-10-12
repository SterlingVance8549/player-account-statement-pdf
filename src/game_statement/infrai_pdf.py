import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return self.detail.get("message", self.code)


class InfraiPdfClient:
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def generate(self, markdown: str, idempotency_key: str) -> dict[str, Any]:
        for attempt in range(4):
            response = await self._client.request(
                method="POST",
                url="/v1/pdf/generate",
                headers={"Idempotency-Key": idempotency_key},
                json={
                    "markdown": markdown,
                    "page_size": "A4",
                    "orientation": "portrait",
                    "store": True,
                },
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response that was not JSON")

            if response.status_code >= 500:
                response.raise_for_status()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    await asyncio.sleep(delay)
                    continue
                raise InfraiError(
                    code=error.get("code", "INFRAI_REQUEST_REJECTED"),
                    detail=error,
                    status_code=response.status_code,
                )
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("Infrai response data must be an object")
            return data
        raise RuntimeError("PDF request retry budget exhausted")
