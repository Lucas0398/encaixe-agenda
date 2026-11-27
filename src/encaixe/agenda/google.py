"""Implementação da `Agenda` com a Google Calendar API (LS-12).

Autenticação por conta de serviço: compartilhe cada agenda com o e-mail da
conta de serviço, com a permissão "Fazer alterações nos eventos".
Ver docs/setup-google.md.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

from encaixe.agenda.porta import EventoAgenda
from encaixe.dominio.disponibilidade import Intervalo

ESCOPOS = ["https://www.googleapis.com/auth/calendar"]
CHAVE_AGENDAMENTO = "encaixe_agendamento_id"


class AgendaGoogle:
    def __init__(self, arquivo_credenciais: str, fuso: str = "America/Maceio") -> None:
        credenciais = service_account.Credentials.from_service_account_file(arquivo_credenciais, scopes=ESCOPOS)
        self._api = build("calendar", "v3", credentials=credenciais, cache_discovery=False)
        self._fuso = fuso

    def _para_intervalo(self, inicio: dict, fim: dict) -> tuple[Intervalo, bool]:
        if "dateTime" in inicio:
            return Intervalo(datetime.fromisoformat(inicio["dateTime"]), datetime.fromisoformat(fim["dateTime"])), False
        zona = ZoneInfo(self._fuso)  # evento de dia inteiro: bloqueia o dia todo
        de = datetime.combine(date.fromisoformat(inicio["date"]), time(0), tzinfo=zona)
        ate = datetime.combine(date.fromisoformat(fim["date"]), time(0), tzinfo=zona)
        return Intervalo(de, ate), True

    def listar_eventos(self, calendario_id: str, intervalo: Intervalo) -> list[EventoAgenda]:
        eventos: list[EventoAgenda] = []
        pagina = None
        while True:
            resposta = (
                self._api.events()
                .list(
                    calendarId=calendario_id,
                    timeMin=intervalo.inicio.isoformat(),
                    timeMax=intervalo.fim.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=pagina,
                )
                .execute()
            )
            for item in resposta.get("items", []):
                # "Livre" no Google (transparent) não ocupa horário.
                if item.get("status") == "cancelled" or item.get("transparency") == "transparent":
                    continue
                periodo, dia_inteiro = self._para_intervalo(item["start"], item["end"])
                privado = item.get("extendedProperties", {}).get("private", {})
                eventos.append(
                    EventoAgenda(
                        id=item["id"],
                        intervalo=periodo,
                        titulo=item.get("summary", ""),
                        agendamento_id=privado.get(CHAVE_AGENDAMENTO),
                        dia_inteiro=dia_inteiro,
                    )
                )
            pagina = resposta.get("nextPageToken")
            if not pagina:
                return eventos

    def criar_evento(self, calendario_id, intervalo, *, titulo, descricao="", cor=None, agendamento_id):
        corpo = {
            "summary": titulo,
            "description": descricao,
            "start": {"dateTime": intervalo.inicio.isoformat(), "timeZone": self._fuso},
            "end": {"dateTime": intervalo.fim.isoformat(), "timeZone": self._fuso},
            "extendedProperties": {"private": {CHAVE_AGENDAMENTO: agendamento_id}},
        }
        if cor:
            corpo["colorId"] = cor
        return self._api.events().insert(calendarId=calendario_id, body=corpo).execute()["id"]

    def atualizar_evento(self, calendario_id, evento_id, *, intervalo=None, titulo=None, cor=None):
        corpo: dict = {}
        if intervalo:
            corpo["start"] = {"dateTime": intervalo.inicio.isoformat(), "timeZone": self._fuso}
            corpo["end"] = {"dateTime": intervalo.fim.isoformat(), "timeZone": self._fuso}
        if titulo:
            corpo["summary"] = titulo
        if cor:
            corpo["colorId"] = cor
        if corpo:
            self._api.events().patch(calendarId=calendario_id, eventId=evento_id, body=corpo).execute()

    def remover_evento(self, calendario_id, evento_id):
        self._api.events().delete(calendarId=calendario_id, eventId=evento_id).execute()


def janela_do_dia(dia: date, fuso: str) -> Intervalo:
    zona = ZoneInfo(fuso)
    inicio = datetime.combine(dia, time(0), tzinfo=zona)
    return Intervalo(inicio, inicio + timedelta(days=1))
