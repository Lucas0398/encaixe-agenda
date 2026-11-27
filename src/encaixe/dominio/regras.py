"""Regras configuráveis por clínica (LS-31).

Toda regra que pode variar de uma clínica para outra fica aqui, e não
espalhada pelo código. Uma clínica nova começa com os valores padrão e
ajusta só o que for diferente.

Exemplo:
    regras = RegrasClinica.model_validate({"exige_pagamento_antecipado": True})
"""

from __future__ import annotations

from datetime import date, time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RegrasClinica(BaseModel):
    """Regras de negócio de uma clínica. Guardadas como JSON na tabela `clinicas`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Geral
    fuso: str = "America/Maceio"

    # Grade de horários
    granularidade_slots_min: int = Field(30, gt=0, description="De quanto em quanto tempo oferecer horários")
    intervalo_entre_sessoes_min: int = Field(0, ge=0, description="Folga obrigatória entre atendimentos")
    max_opcoes_oferecidas: int = Field(5, gt=0, description="Quantos horários o bot mostra por vez")

    # Antecedência
    antecedencia_minima_agendamento_horas: float = Field(2, ge=0)
    antecedencia_minima_cancelamento_horas: float = Field(24, ge=0)

    # Bloqueios de calendário
    bloquear_feriados_nacionais: bool = True
    bloquear_pontos_facultativos: bool = True  # Carnaval e Corpus Christi
    datas_bloqueadas: tuple[date, ...] = ()  # feriados estaduais/municipais, recessos

    # Pagamento antecipado (LS-37)
    exige_pagamento_antecipado: bool = False
    pagamento_exigido_para: Literal["todos", "so_pacientes_novos"] = "todos"
    prazo_pagamento_horas: float = Field(2, gt=0)
    aviso_antes_do_prazo_min: int = Field(30, ge=0)

    # Lembrete e encaminhamento
    lembrete_d1_horario: time = time(10, 0)
    primeira_avaliacao_vai_para_humano: bool = True

    @field_validator("fuso")
    @classmethod
    def _fuso_valido(cls, valor: str) -> str:
        try:
            ZoneInfo(valor)
        except (ZoneInfoNotFoundError, ValueError) as erro:
            raise ValueError(f"fuso horário inválido: {valor!r}") from erro
        return valor

    @model_validator(mode="after")
    def _aviso_dentro_do_prazo(self) -> RegrasClinica:
        if self.aviso_antes_do_prazo_min >= self.prazo_pagamento_horas * 60:
            raise ValueError("aviso_antes_do_prazo_min precisa ser menor que o prazo de pagamento")
        return self

    @property
    def zona(self) -> ZoneInfo:
        return ZoneInfo(self.fuso)

    def exige_pagamento(self, paciente_novo: bool) -> bool:
        """Diz se este agendamento precisa ser pago antes para ser confirmado."""
        if not self.exige_pagamento_antecipado:
            return False
        if self.pagamento_exigido_para == "so_pacientes_novos":
            return paciente_novo
        return True
