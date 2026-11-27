"""Configuração lida de variáveis de ambiente (ver `.env.example`).

Nenhum segredo fica no código nem no repositório.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache


class ConfigIncompleta(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    ambiente: str
    database_url: str
    # WhatsApp Cloud API
    whatsapp_token: str
    whatsapp_phone_number_id: str
    whatsapp_app_secret: str
    whatsapp_verify_token: str
    whatsapp_graph_versao: str
    # Google Agenda
    google_credenciais_arquivo: str
    # IA
    anthropic_api_key: str

    @classmethod
    def de_ambiente(cls, env: Mapping[str, str] | None = None) -> Config:
        env = os.environ if env is None else env
        obrigatorias = {
            "database_url": "DATABASE_URL",
            "whatsapp_token": "WHATSAPP_TOKEN",
            "whatsapp_phone_number_id": "WHATSAPP_PHONE_NUMBER_ID",
            "whatsapp_app_secret": "WHATSAPP_APP_SECRET",
            "whatsapp_verify_token": "WHATSAPP_VERIFY_TOKEN",
            "whatsapp_graph_versao": "WHATSAPP_GRAPH_VERSAO",
        }
        faltando = [nome for nome in obrigatorias.values() if not env.get(nome)]
        if faltando:
            raise ConfigIncompleta("Variáveis de ambiente faltando: " + ", ".join(faltando))
        return cls(
            ambiente=env.get("AMBIENTE", "desenvolvimento"),
            **{campo: env[nome] for campo, nome in obrigatorias.items()},
            google_credenciais_arquivo=env.get("GOOGLE_CREDENCIAIS_ARQUIVO", "credenciais/google-service-account.json"),
            anthropic_api_key=env.get("ANTHROPIC_API_KEY", ""),
        )


@lru_cache(maxsize=1)
def config() -> Config:
    return Config.de_ambiente()
