import httpx
import pytest

from game_statement.infrai_pdf import InfraiPdfClient


@pytest.mark.asyncio
async def test_generate_sends_the_pdf_boundary() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/pdf/generate"
        assert request.headers["Idempotency-Key"] == "statement-123"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.read() == b'{"markdown":"# Statement","page_size":"A4","orientation":"portrait","store":true}'
        return httpx.Response(200, json={"ok": True, "data": {"job_id": "job-7"}, "error": None, "metadata": {}})

    client = InfraiPdfClient("test-key", transport=httpx.MockTransport(handler))
    try:
        result = await client.generate("# Statement", "statement-123")
    finally:
        await client.close()

    assert result == {"job_id": "job-7"}

