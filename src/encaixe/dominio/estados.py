"""Máquina de estados do agendamento (LS-32).

Todo agendamento tem um status, e ele só muda por transições permitidas.
Ninguém altera o status direto no banco: tudo passa por `mudar_status`,
que valida a transição e devolve um registro para o histórico.

Ações disparadas por uma transição (mandar mensagem, mudar a cor na agenda,
agendar tarefa) são registradas no `Despachante`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Status(StrEnum):
    PENDENTE_PAGAMENTO = "pendente_pagamento"
    CONFIRMADO = "confirmado"
    PRESENCA_CONFIRMADA = "presenca_confirmada"
    REALIZADO = "realizado"
    FALTOU = "faltou"
    CANCELADO_PACIENTE = "cancelado_paciente"
    CANCELADO_CLINICA = "cancelado_clinica"
    CANCELADO_FALTA_PAGAMENTO = "cancelado_falta_pagamento"


_CANCELAMENTOS = frozenset({Status.CANCELADO_PACIENTE, Status.CANCELADO_CLINICA})

TRANSICOES: dict[Status, frozenset[Status]] = {
    Status.PENDENTE_PAGAMENTO: frozenset({Status.CONFIRMADO, Status.CANCELADO_FALTA_PAGAMENTO} | _CANCELAMENTOS),
    Status.CONFIRMADO: frozenset({Status.PRESENCA_CONFIRMADA, Status.REALIZADO, Status.FALTOU} | _CANCELAMENTOS),
    Status.PRESENCA_CONFIRMADA: frozenset({Status.REALIZADO, Status.FALTOU} | _CANCELAMENTOS),
    # Pix pago depois do prazo, com o horário ainda livre: reativa (LS-37).
    Status.CANCELADO_FALTA_PAGAMENTO: frozenset({Status.CONFIRMADO}),
    Status.REALIZADO: frozenset(),
    Status.FALTOU: frozenset(),
    Status.CANCELADO_PACIENTE: frozenset(),
    Status.CANCELADO_CLINICA: frozenset(),
}

# Status que ocupam o horário na agenda (contam para conflito).
STATUS_ATIVOS = frozenset({Status.PENDENTE_PAGAMENTO, Status.CONFIRMADO, Status.PRESENCA_CONFIRMADA})

# colorId do Google Agenda por status. None = evento removido da agenda.
COR_AGENDA: dict[Status, str | None] = {
    Status.PENDENTE_PAGAMENTO: "5",  # amarelo (banana)
    Status.CONFIRMADO: "10",  # verde (manjericão)
    Status.PRESENCA_CONFIRMADA: "2",  # verde-claro (sálvia)
    Status.REALIZADO: "8",  # cinza (grafite)
    Status.FALTOU: "11",  # vermelho (tomate)
    Status.CANCELADO_PACIENTE: None,
    Status.CANCELADO_CLINICA: None,
    Status.CANCELADO_FALTA_PAGAMENTO: None,
}


class TransicaoInvalida(ValueError):
    def __init__(self, de: Status, para: Status) -> None:
        super().__init__(f"transição não permitida: {de} → {para}")
        self.de = de
        self.para = para


@dataclass(frozen=True)
class Transicao:
    """Registro de uma mudança de status (vira uma linha em `agendamento_historico`)."""

    de: Status
    para: Status
    motivo: str
    autor: str  # "bot", "secretaria:<id>", "sistema:pagamento", ...
    em: datetime


def pode_mudar(de: Status, para: Status) -> bool:
    return para in TRANSICOES[de]


def mudar_status(atual: Status, novo: Status, *, motivo: str, autor: str, em: datetime) -> Transicao:
    if em.tzinfo is None:
        raise ValueError("`em` precisa ter fuso horário")
    if not pode_mudar(atual, novo):
        raise TransicaoInvalida(atual, novo)
    return Transicao(de=atual, para=novo, motivo=motivo, autor=autor, em=em)


Acao = Callable[[Transicao], None]


class Despachante:
    """Liga transições a ações. Ex.: ao entrar em CONFIRMADO, mandar confirmação.

    despachante.ao_entrar(Status.CONFIRMADO, enviar_confirmacao)
    despachante.publicar(transicao)
    """

    def __init__(self) -> None:
        self._acoes: dict[Status, list[Acao]] = defaultdict(list)

    def ao_entrar(self, status: Status, acao: Acao) -> None:
        self._acoes[status].append(acao)

    def publicar(self, transicao: Transicao) -> None:
        for acao in self._acoes[transicao.para]:
            acao(transicao)
