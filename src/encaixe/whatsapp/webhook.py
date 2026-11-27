"""Recebimento de mensagens do WhatsApp (LS-15).

Funções puras para:
- responder o desafio de verificação (GET) quando o webhook é cadastrado na Meta;
- validar a assinatura `X-Hub-Signature-256` de cada chamada (POST);
- transformar o JSON da Meta em objetos simples (`MensagemRecebida`, `StatusEntrega`).
"""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

TipoMensagem = Literal["texto", "botao", "audio", "imagem", "documento", "localizacao", "nao_suportado"]


@dataclass(frozen=True)
class MensagemRecebida:
    id: str  # wamid — usado para idempotência
    telefone: str  # wa_id do paciente, ex.: "5582999990000"
    nome_perfil: str | None
    numero_destino_id: str  # phone_number_id da clínica (identifica a clínica)
    recebida_em: datetime
    tipo: TipoMensagem
    texto: str | None = None  # corpo do texto ou título do botão
    botao_id: str | None = None  # id/payload do botão clicado
    responde_a: str | None = None  # wamid da mensagem respondida, se houver


@dataclass(frozen=True)
class StatusEntrega:
    mensagem_id: str
    telefone: str
    status: str  # sent, delivered, read, failed
    em: datetime
    erros: tuple[dict[str, Any], ...] = ()


def responder_desafio(params: Mapping[str, str], verify_token: str) -> str | None:
    """Devolve o `hub.challenge` se o token bater; senão None (responder 403)."""
    if params.get("hub.mode") != "subscribe":
        return None
    token = params.get("hub.verify_token", "")
    if not verify_token or not hmac.compare_digest(token, verify_token):
        return None
    return params.get("hub.challenge")


def assinatura_valida(corpo: bytes, cabecalho: str | None, app_secret: str) -> bool:
    """Confere o HMAC-SHA256 do corpo com o App Secret do app na Meta."""
    if not cabecalho or not app_secret or not cabecalho.startswith("sha256="):
        return False
    esperado = hmac.new(app_secret.encode(), corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(cabecalho.removeprefix("sha256="), esperado)


def _quando(ts: str | int | None) -> datetime:
    return datetime.fromtimestamp(int(ts or 0), tz=UTC)


def _valores(payload: Mapping[str, Any]):
    for entrada in payload.get("entry", []):
        for mudanca in entrada.get("changes", []):
            if mudanca.get("field") == "messages":
                yield mudanca.get("value", {})


_TIPOS_MIDIA: dict[str, TipoMensagem] = {
    "audio": "audio",
    "voice": "audio",
    "image": "imagem",
    "document": "documento",
    "location": "localizacao",
}


def _converter(msg: Mapping[str, Any], nomes: dict[str, str], numero_id: str) -> MensagemRecebida:
    tipo_meta = msg.get("type")
    base = {
        "id": msg["id"],
        "telefone": msg["from"],
        "nome_perfil": nomes.get(msg["from"]),
        "numero_destino_id": numero_id,
        "recebida_em": _quando(msg.get("timestamp")),
        "responde_a": (msg.get("context") or {}).get("id"),
    }
    if tipo_meta == "text":
        return MensagemRecebida(**base, tipo="texto", texto=msg.get("text", {}).get("body"))
    if tipo_meta == "interactive":
        interativo = msg.get("interactive", {})
        resposta = interativo.get("button_reply") or interativo.get("list_reply") or {}
        return MensagemRecebida(**base, tipo="botao", texto=resposta.get("title"), botao_id=resposta.get("id"))
    if tipo_meta == "button":  # botão de resposta rápida de template
        botao = msg.get("button", {})
        return MensagemRecebida(**base, tipo="botao", texto=botao.get("text"), botao_id=botao.get("payload"))
    return MensagemRecebida(**base, tipo=_TIPOS_MIDIA.get(str(tipo_meta), "nao_suportado"))


def extrair_mensagens(payload: Mapping[str, Any]) -> list[MensagemRecebida]:
    mensagens: list[MensagemRecebida] = []
    for valor in _valores(payload):
        numero_id = valor.get("metadata", {}).get("phone_number_id", "")
        nomes = {c.get("wa_id"): c.get("profile", {}).get("name") for c in valor.get("contacts", [])}
        mensagens.extend(_converter(m, nomes, numero_id) for m in valor.get("messages", []))
    return mensagens


def extrair_status(payload: Mapping[str, Any]) -> list[StatusEntrega]:
    return [
        StatusEntrega(
            mensagem_id=s["id"],
            telefone=s.get("recipient_id", ""),
            status=s.get("status", ""),
            em=_quando(s.get("timestamp")),
            erros=tuple(s.get("errors", [])),
        )
        for valor in _valores(payload)
        for s in valor.get("statuses", [])
    ]
