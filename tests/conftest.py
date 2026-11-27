from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from encaixe.dominio.disponibilidade import Expediente, Servico
from encaixe.dominio.regras import RegrasClinica

MACEIO = ZoneInfo("America/Maceio")


def em(ano, mes, dia, hora=0, minuto=0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=MACEIO)


@pytest.fixture
def regras() -> RegrasClinica:
    return RegrasClinica(antecedencia_minima_agendamento_horas=0, max_opcoes_oferecidas=50)


@pytest.fixture
def expediente_semana() -> list[Expediente]:
    """Segunda a sexta, 08–12 e 14–18 (almoço 12–14)."""
    blocos = []
    for dia in range(5):
        blocos.append(Expediente(dia, time(8), time(12)))
        blocos.append(Expediente(dia, time(14), time(18)))
    return blocos


@pytest.fixture
def sessao() -> Servico:
    return Servico("Sessão de fisioterapia", duracao_min=60)
