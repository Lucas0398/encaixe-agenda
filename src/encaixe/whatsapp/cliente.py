"""Envio de mensagens pela WhatsApp Cloud API.

Regra da Meta: texto livre e botões só podem ser enviados até 24h depois da
última mensagem do paciente. Fora dessa janela, só templates aprovados
(confirmação, lembrete D-1, pagamento).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx


class ErroWhatsApp(RuntimeError):
    def __init__(self, status: int, corpo: Any) -> None:
        super().__init__(f"WhatsApp respondeu {status}: {corpo}")
        self.status = status
        self.corpo = corpo


class ClienteWhatsApp:
    def __init__(self, *, token: str, phone_number_id: str, graph_versao: str, http: httpx.AsyncClient | None = None):
        self._url = f"https://graph.facebook.com/{graph_versao}/{phone_number_id}/messages"
        self._headers = {"Authorization": f"Bearer {token}"}
        self._http = http or httpx.AsyncClient(timeout=15)

    async def _enviar(self, telefone: str, conteudo: dict[str, Any]) -> str:
        corpo = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": telefone, **conteudo}
        resposta = await self._http.post(self._url, json=corpo, headers=self._headers)
        dados = resposta.json() if resposta.content else {}
        if resposta.status_code >= 400:
            raise ErroWhatsApp(resposta.status_code, dados)
        return dados["messages"][0]["id"]  # wamid, guardar para rastrear o status

    async def enviar_texto(self, telefone: str, texto: str) -> str:
        return await self._enviar(telefone, {"type": "text", "text": {"body": texto, "preview_url": False}})

    async def enviar_botoes(self, telefone: str, texto: str, botoes: Sequence[tuple[str, str]]) -> str:
        """Até 3 botões de resposta rápida: [(id, título), ...]. Título com até 20 caracteres."""
        if not 1 <= len(botoes) <= 3:
            raise ValueError("o WhatsApp aceita de 1 a 3 botões")
        return await self._enviar(
            telefone,
            {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": texto},
                    "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t[:20]}} for i, t in botoes]},
                },
            },
        )

    async def enviar_template(
        self, telefone: str, nome: str, *, idioma: str = "pt_BR", parametros: Sequence[str] = ()
    ) -> str:
        template: dict[str, Any] = {"name": nome, "language": {"code": idioma}}
        if parametros:
            template["components"] = [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parametros]}]
        return await self._enviar(telefone, {"type": "template", "template": template})

    async def fechar(self) -> None:
        await self._http.aclose()
