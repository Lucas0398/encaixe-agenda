"""Contrato da agenda. O domínio fala com esta interface, não com o Google.

Assim dá para testar os fluxos com uma agenda em memória e, no futuro,
suportar outra agenda (Outlook, sistema da clínica) sem mexer nas regras.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from typing import Protocol

from encaixe.dominio.disponibilidade import Intervalo


@dataclass(frozen=True)
class EventoAgenda:
    id: str
    intervalo: Intervalo
    titulo: str
    agendamento_id: str | None = None  # preenchido quando o evento foi criado pelo EncaixeAgenda
    dia_inteiro: bool = False


class Agenda(Protocol):
    def listar_eventos(self, calendario_id: str, intervalo: Intervalo) -> list[EventoAgenda]: ...

    def criar_evento(
        self,
        calendario_id: str,
        intervalo: Intervalo,
        *,
        titulo: str,
        descricao: str = "",
        cor: str | None = None,
        agendamento_id: str,
    ) -> str: ...

    def atualizar_evento(
        self,
        calendario_id: str,
        evento_id: str,
        *,
        intervalo: Intervalo | None = None,
        titulo: str | None = None,
        cor: str | None = None,
    ) -> None: ...

    def remover_evento(self, calendario_id: str, evento_id: str) -> None: ...


@dataclass
class AgendaEmMemoria:
    """Implementação fake para testes."""

    eventos: dict[str, dict[str, EventoAgenda]] = field(default_factory=dict)
    _ids: count = field(default_factory=lambda: count(1))

    def listar_eventos(self, calendario_id: str, intervalo: Intervalo) -> list[EventoAgenda]:
        todos = self.eventos.get(calendario_id, {}).values()
        return sorted((e for e in todos if e.intervalo.sobrepoe(intervalo)), key=lambda e: e.intervalo.inicio)

    def criar_evento(self, calendario_id, intervalo, *, titulo, descricao="", cor=None, agendamento_id):
        evento_id = f"evt{next(self._ids)}"
        self.eventos.setdefault(calendario_id, {})[evento_id] = EventoAgenda(
            evento_id, intervalo, titulo, agendamento_id
        )
        return evento_id

    def atualizar_evento(self, calendario_id, evento_id, *, intervalo=None, titulo=None, cor=None):
        atual = self.eventos[calendario_id][evento_id]
        self.eventos[calendario_id][evento_id] = EventoAgenda(
            evento_id, intervalo or atual.intervalo, titulo or atual.titulo, atual.agendamento_id
        )

    def remover_evento(self, calendario_id, evento_id):
        self.eventos.get(calendario_id, {}).pop(evento_id, None)
