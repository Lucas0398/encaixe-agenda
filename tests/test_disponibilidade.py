from datetime import date

import pytest

from encaixe.dominio.disponibilidade import (
    Intervalo,
    Servico,
    horarios_livres,
    ocupacao_maxima,
    pode_cancelar_sem_humano,
    tem_conflito,
)
from encaixe.dominio.regras import RegrasClinica
from tests.conftest import em

# 2026-11-30 é uma segunda-feira.
SEGUNDA = date(2026, 11, 30)


def livres(regras, expediente, servico, ocupados=(), agora=None, **kw):
    return horarios_livres(
        de=kw.pop("de", SEGUNDA),
        ate=kw.pop("ate", SEGUNDA),
        expediente=expediente,
        servico=servico,
        ocupados=list(ocupados),
        regras=regras,
        agora=agora or em(2026, 11, 27, 9),
        **kw,
    )


def inicios(intervalos):
    return [i.inicio.strftime("%H:%M") for i in intervalos]


def test_dia_livre_respeita_almoco(regras, expediente_semana, sessao):
    r = inicios(livres(regras, expediente_semana, sessao))
    assert r[0] == "08:00"
    assert "11:00" in r and "11:30" not in r  # 11:30 + 1h passaria do almoço
    assert "12:00" not in r and "13:00" not in r
    assert r[-1] == "17:00"


def test_horario_ocupado_nao_e_oferecido(regras, expediente_semana, sessao):
    ocupado = Intervalo(em(2026, 11, 30, 9), em(2026, 11, 30, 10))
    r = inicios(livres(regras, expediente_semana, sessao, [ocupado]))
    assert "09:00" not in r
    assert "08:30" not in r  # 08:30–09:30 sobrepõe
    assert "08:00" in r and "10:00" in r  # encostar não é conflito


def test_intervalo_entre_sessoes(expediente_semana, sessao):
    regras = RegrasClinica(
        antecedencia_minima_agendamento_horas=0, intervalo_entre_sessoes_min=15, max_opcoes_oferecidas=50
    )
    ocupado = Intervalo(em(2026, 11, 30, 9), em(2026, 11, 30, 10))
    r = inicios(livres(regras, expediente_semana, sessao, [ocupado]))
    assert "08:00" not in r and "10:00" not in r
    assert "10:30" in r


def test_capacidade_em_grupo(regras, expediente_semana):
    pilates = Servico("Pilates", duracao_min=60, capacidade=2)
    um = Intervalo(em(2026, 11, 30, 8), em(2026, 11, 30, 9))
    assert "08:00" in inicios(livres(regras, expediente_semana, pilates, [um]))
    assert "08:00" not in inicios(livres(regras, expediente_semana, pilates, [um, um]))


def test_ocupacao_conta_simultaneos_e_nao_soma():
    janela = Intervalo(em(2026, 11, 30, 8), em(2026, 11, 30, 10))
    a = Intervalo(em(2026, 11, 30, 8), em(2026, 11, 30, 9))
    b = Intervalo(em(2026, 11, 30, 9), em(2026, 11, 30, 10))
    assert ocupacao_maxima(janela, [a, b]) == 1  # um depois do outro, nunca juntos
    assert not tem_conflito(janela, [a, b], capacidade=2)


def test_bloqueio_vale_mesmo_com_capacidade(regras, expediente_semana):
    pilates = Servico("Pilates", duracao_min=60, capacidade=10)
    reuniao = Intervalo(em(2026, 11, 30, 8), em(2026, 11, 30, 12))
    r = inicios(livres(regras, expediente_semana, pilates, bloqueios=[reuniao]))
    assert r[0] == "14:00"


def test_fim_de_semana_sem_expediente(regras, expediente_semana, sessao):
    assert livres(regras, expediente_semana, sessao, de=date(2026, 11, 28), ate=date(2026, 11, 29)) == []


def test_feriado_nacional_bloqueado(regras, expediente_semana, sessao):
    natal = date(2026, 12, 25)  # sexta-feira
    assert livres(regras, expediente_semana, sessao, de=natal, ate=natal) == []


def test_data_bloqueada_pela_clinica(expediente_semana, sessao):
    regras = RegrasClinica(antecedencia_minima_agendamento_horas=0, datas_bloqueadas=(SEGUNDA,))
    assert livres(regras, expediente_semana, sessao) == []


def test_antecedencia_minima(expediente_semana, sessao):
    regras = RegrasClinica(antecedencia_minima_agendamento_horas=2, max_opcoes_oferecidas=50)
    r = inicios(livres(regras, expediente_semana, sessao, agora=em(2026, 11, 30, 8, 10)))
    assert r[0] == "10:30"


def test_periodo_tarde(regras, expediente_semana, sessao):
    r = inicios(livres(regras, expediente_semana, sessao, periodo="tarde"))
    assert r[0] == "14:00" and all(h >= "12:00" for h in r)


def test_limite_de_opcoes_atravessa_dias(expediente_semana, sessao):
    regras = RegrasClinica(antecedencia_minima_agendamento_horas=0, max_opcoes_oferecidas=3)
    r = livres(regras, expediente_semana, sessao, agora=em(2026, 11, 30, 16, 31), ate=date(2026, 12, 4))
    assert inicios(r) == ["17:00", "08:00", "08:30"]
    assert r[1].inicio.date() == date(2026, 12, 1)


def test_exige_fuso_em_agora(regras, expediente_semana, sessao):
    from datetime import datetime

    with pytest.raises(ValueError):
        livres(regras, expediente_semana, sessao, agora=datetime(2026, 11, 27, 9))


def test_cancelamento_respeita_antecedencia():
    regras = RegrasClinica(antecedencia_minima_cancelamento_horas=24)
    sessao = em(2026, 11, 30, 9)
    assert pode_cancelar_sem_humano(sessao, em(2026, 11, 29, 9), regras)
    assert not pode_cancelar_sem_humano(sessao, em(2026, 11, 29, 10), regras)
