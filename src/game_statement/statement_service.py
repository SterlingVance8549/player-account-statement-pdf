import os

from fastapi import FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient
from .models import StatementExportRequest, StatementExportResponse
from .statement_renderer import render_statement, statement_id_for

service = FastAPI(title="Game account statement exporter")


@service.post("/statements/export", response_model=StatementExportResponse)
async def export_statement(request: StatementExportRequest) -> StatementExportResponse:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is not configured")

    statement_id = statement_id_for(request)
    client = InfraiPdfClient(api_key)
    try:
        document = await client.generate(render_statement(request), statement_id)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    finally:
        await client.close()
    return StatementExportResponse(statement_id=statement_id, document=document)

