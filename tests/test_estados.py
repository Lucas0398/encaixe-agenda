from datetime import datetime

import pytest

from encaixe.dominio.estados import (
    COR_AGENDA,
    STATUS_ATIVOS,
    TRANSICOES,
    Despachante,
    Status,
    TransicaoInvalida,
    mudar_status,
)
from tests.conftest import em


def test_todo_status_tem_transicoes_e_cor():
    assert set(TRANSICOES) == set(Status)
    assert set(COR_AGENDA) == set(Status)


def test_pagamento_confirma():
    t = mudar_status(
        Status.PENDENTE_PAGAMENTO,
        Status.CONFIRMADO,
        motivo="pix pago",
        autor="sistema:pagamento",
        em=em(2026, 11, 27, 10),
    )
    assert (t.de, t.para) == (Status.PENDENTE_PAGAMENTO, Status.CONFIRMADO)


def test_pix_atrasado_reativa_agendamento():
    mudar_status(
        Status.CANCELADO_FALTA_PAGAMENTO,
        Status.CONFIRMADO,
        motivo="pix atrasado",
        autor="sistema:pagamento",
        em=em(2026, 11, 27),
    )


@pytest.mark.parametrize(
    ("de", "para"),
    [
        (Status.REALIZADO, Status.CONFIRMADO),
        (Status.CANCELADO_PACIENTE, Status.CONFIRMADO),
        (Status.CONFIRMADO, Status.PENDENTE_PAGAMENTO),
        (Status.CONFIRMADO, Status.CANCELADO_FALTA_PAGAMENTO),
        (Status.FALTOU, Status.REALIZADO),
    ],
)
def test_transicoes_proibidas(de, para):
    with pytest.raises(TransicaoInvalida):
        mudar_status(de, para, motivo="x", autor="bot", em=em(2026, 11, 27))


def test_exige_data_com_fuso():
    with pytest.raises(ValueError):
        mudar_status(Status.CONFIRMADO, Status.REALIZADO, motivo="x", autor="bot", em=datetime(2026, 11, 27))


def test_status_finais_nao_ocupam_agenda():
    assert Status.CANCELADO_FALTA_PAGAMENTO not in STATUS_ATIVOS
    assert Status.PENDENTE_PAGAMENTO in STATUS_ATIVOS  # horário fica reservado enquanto espera o Pix


def test_despachante_dispara_acao_ao_entrar_no_status():
    chamadas = []
    d = Despachante()
    d.ao_entrar(Status.CONFIRMADO, chamadas.append)
    t = mudar_status(Status.PENDENTE_PAGAMENTO, Status.CONFIRMADO, motivo="pix", autor="sistema", em=em(2026, 11, 27))
    d.publicar(t)
    d.publicar(
        mudar_status(Status.CONFIRMADO, Status.FALTOU, motivo="não veio", autor="secretaria:1", em=em(2026, 11, 28))
    )
    assert chamadas == [t]
