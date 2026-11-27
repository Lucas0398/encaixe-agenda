"""Horários livres e conflitos (LS-19).

Funções puras: recebem a grade da clínica, o que já está ocupado na agenda e
as regras, e devolvem opções de horário. Quem busca os eventos no Google
Agenda e quem grava o agendamento (com trava no banco) são outras camadas.

Garantia central: um horário só é oferecido se, durante toda a sessão, o
número de atendimentos simultâneos continuar abaixo da capacidade do serviço.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

from encaixe.dominio.feriados import feriados_nacionais, pontos_facultativos
from encaixe.dominio.regras import RegrasClinica

Periodo = Literal["manha", "tarde", "noite"]

_LIMITES_PERIODO: dict[Periodo, tuple[time, time]] = {
    "manha": (time(0, 0), time(12, 0)),
    "tarde": (time(12, 0), time(18, 0)),
    "noite": (time(18, 0), time(23, 59, 59)),
}


@dataclass(frozen=True)
class Intervalo:
    inicio: datetime
    fim: datetime

    def __post_init__(self) -> None:
        if self.inicio.tzinfo is None or self.fim.tzinfo is None:
            raise ValueError("Intervalo precisa de datas com fuso horário")
        if self.fim <= self.inicio:
            raise ValueError("fim precisa ser depois do início")

    def sobrepoe(self, outro: Intervalo) -> bool:
        return self.inicio < outro.fim and outro.inicio < self.fim

    def expandido(self, minutos: int) -> Intervalo:
        folga = timedelta(minutes=minutos)
        return Intervalo(self.inicio - folga, self.fim + folga)


@dataclass(frozen=True)
class Expediente:
    """Um bloco de atendimento. Almoço = dois blocos no mesmo dia (08–12 e 14–18)."""

    dia_semana: int  # 0 = segunda ... 6 = domingo
    inicio: time
    fim: time

    def __post_init__(self) -> None:
        if not 0 <= self.dia_semana <= 6:
            raise ValueError("dia_semana vai de 0 (segunda) a 6 (domingo)")
        if self.fim <= self.inicio:
            raise ValueError("fim do expediente precisa ser depois do início")


@dataclass(frozen=True)
class Servico:
    nome: str
    duracao_min: int
    capacidade: int = 1  # quantos pacientes ao mesmo tempo (ex.: pilates em grupo)

    def __post_init__(self) -> None:
        if self.duracao_min <= 0 or self.capacidade <= 0:
            raise ValueError("duração e capacidade precisam ser positivas")


def ocupacao_maxima(janela: Intervalo, ocupados: Iterable[Intervalo]) -> int:
    """Maior número de atendimentos simultâneos dentro da janela."""
    eventos: list[tuple[datetime, int]] = []
    for o in ocupados:
        if o.sobrepoe(janela):
            eventos.append((max(o.inicio, janela.inicio), 1))
            eventos.append((min(o.fim, janela.fim), -1))
    # No mesmo instante, quem termina sai antes de quem começa entrar.
    eventos.sort(key=lambda e: (e[0], e[1]))
    atual = maximo = 0
    for _, delta in eventos:
        atual += delta
        maximo = max(maximo, atual)
    return maximo


def tem_conflito(
    candidato: Intervalo,
    ocupados: Sequence[Intervalo],
    *,
    capacidade: int = 1,
    intervalo_entre_sessoes_min: int = 0,
    bloqueios: Sequence[Intervalo] = (),
) -> bool:
    """True se o candidato não cabe na agenda.

    `bloqueios` (almoço extra, férias, reunião) bloqueiam sempre, seja qual for a capacidade.
    """
    if any(b.sobrepoe(candidato) for b in bloqueios):
        return True
    janela = candidato.expandido(intervalo_entre_sessoes_min) if intervalo_entre_sessoes_min else candidato
    return ocupacao_maxima(janela, ocupados) >= capacidade


def dia_bloqueado(dia: date, regras: RegrasClinica) -> bool:
    if dia in regras.datas_bloqueadas:
        return True
    if regras.bloquear_feriados_nacionais and dia in feriados_nacionais(dia.year):
        return True
    return regras.bloquear_pontos_facultativos and dia in pontos_facultativos(dia.year)


def _no_periodo(inicio_local: time, periodo: Periodo | None) -> bool:
    if periodo is None:
        return True
    de, ate = _LIMITES_PERIODO[periodo]
    return de <= inicio_local < ate


def _candidatos(
    dia: date, expediente: Sequence[Expediente], servico: Servico, regras: RegrasClinica
) -> Iterator[Intervalo]:
    zona = regras.zona
    passo = timedelta(minutes=regras.granularidade_slots_min)
    duracao = timedelta(minutes=servico.duracao_min)
    for bloco in sorted((b for b in expediente if b.dia_semana == dia.weekday()), key=lambda b: b.inicio):
        inicio = datetime.combine(dia, bloco.inicio, tzinfo=zona)
        limite = datetime.combine(dia, bloco.fim, tzinfo=zona)
        while inicio + duracao <= limite:
            yield Intervalo(inicio, inicio + duracao)
            inicio += passo


def horarios_livres(
    *,
    de: date,
    ate: date,
    expediente: Sequence[Expediente],
    servico: Servico,
    ocupados: Sequence[Intervalo],
    regras: RegrasClinica,
    agora: datetime,
    bloqueios: Sequence[Intervalo] = (),
    periodo: Periodo | None = None,
    limite: int | None = None,
) -> list[Intervalo]:
    """Lista horários livres entre `de` e `ate` (inclusive), em ordem cronológica.

    `ocupados` deve conter só agendamentos ativos (ver `estados.STATUS_ATIVOS`).
    """
    if agora.tzinfo is None:
        raise ValueError("`agora` precisa ter fuso horário")
    if ate < de:
        return []
    limite = regras.max_opcoes_oferecidas if limite is None else limite
    mais_cedo = agora + timedelta(hours=regras.antecedencia_minima_agendamento_horas)

    livres: list[Intervalo] = []
    dia = de
    while dia <= ate and len(livres) < limite:
        if not dia_bloqueado(dia, regras):
            for candidato in _candidatos(dia, expediente, servico, regras):
                if candidato.inicio < mais_cedo:
                    continue
                if not _no_periodo(candidato.inicio.astimezone(regras.zona).time(), periodo):
                    continue
                if tem_conflito(
                    candidato,
                    ocupados,
                    capacidade=servico.capacidade,
                    intervalo_entre_sessoes_min=regras.intervalo_entre_sessoes_min,
                    bloqueios=bloqueios,
                ):
                    continue
                livres.append(candidato)
                if len(livres) >= limite:
                    break
        dia += timedelta(days=1)
    return livres


def pode_cancelar_sem_humano(inicio_sessao: datetime, agora: datetime, regras: RegrasClinica) -> bool:
    """Dentro da antecedência mínima o bot cancela sozinho; depois disso, chama a secretária."""
    return inicio_sessao - agora >= timedelta(hours=regras.antecedencia_minima_cancelamento_horas)
