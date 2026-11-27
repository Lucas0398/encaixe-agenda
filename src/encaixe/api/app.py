"""API HTTP: healthcheck e webhook do WhatsApp (LS-15).

Rodar localmente:
    uvicorn encaixe.api.app:app --reload
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

from encaixe import __version__
from encaixe.config import config
from encaixe.whatsapp.webhook import assinatura_valida, extrair_mensagens, extrair_status, responder_desafio

log = logging.getLogger("encaixe.api")

app = FastAPI(title="EncaixeAgenda", version=__version__)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "versao": __version__}


@app.get("/webhook/whatsapp")
async def verificar_webhook(request: Request) -> PlainTextResponse:
    """A Meta chama este endpoint uma vez, ao cadastrar o webhook."""
    desafio = responder_desafio(dict(request.query_params), config().whatsapp_verify_token)
    if desafio is None:
        raise HTTPException(status_code=403)
    return PlainTextResponse(desafio)


@app.post("/webhook/whatsapp")
async def receber_webhook(request: Request) -> Response:
    corpo = await request.body()
    if not assinatura_valida(corpo, request.headers.get("X-Hub-Signature-256"), config().whatsapp_app_secret):
        raise HTTPException(status_code=401)

    payload = json.loads(corpo)
    mensagens = extrair_mensagens(payload)
    for m in mensagens:
        # Não registrar o texto em log: pode conter dado de saúde (LGPD).
        log.info("mensagem recebida id=%s tipo=%s numero=%s", m.id, m.tipo, m.numero_destino_id)
    for s in extrair_status(payload):
        log.info("status de entrega id=%s status=%s", s.mensagem_id, s.status)

    # TODO(LS-33): gravar em `mensagens_whatsapp` (ON CONFLICT DO NOTHING pelo wamid)
    # e enfileirar o processamento. Responder 200 rápido: a Meta reenvia se demorar.
    return Response(status_code=200)
