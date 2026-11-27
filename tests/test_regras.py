import pytest
from pydantic import ValidationError

from encaixe.dominio.regras import RegrasClinica


def test_clinica_nova_nasce_com_padroes():
    regras = RegrasClinica()
    assert regras.fuso == "America/Maceio"
    assert regras.exige_pagamento_antecipado is False
    assert regras.antecedencia_minima_cancelamento_horas == 24


def test_carrega_de_json_parcial():
    regras = RegrasClinica.model_validate_json('{"exige_pagamento_antecipado": true, "prazo_pagamento_horas": 3}')
    assert regras.exige_pagamento_antecipado
    assert regras.prazo_pagamento_horas == 3
    assert regras.granularidade_slots_min == 30  # o resto fica no padrão


def test_recusa_chave_desconhecida():
    with pytest.raises(ValidationError):
        RegrasClinica.model_validate({"prazo_pagamneto_horas": 2})  # erro de digitação


def test_recusa_fuso_invalido():
    with pytest.raises(ValidationError):
        RegrasClinica(fuso="Maceio")


def test_aviso_precisa_caber_no_prazo():
    with pytest.raises(ValidationError):
        RegrasClinica(prazo_pagamento_horas=0.5, aviso_antes_do_prazo_min=30)


@pytest.mark.parametrize(
    ("exige", "para", "paciente_novo", "esperado"),
    [
        (False, "todos", True, False),
        (True, "todos", False, True),
        (True, "so_pacientes_novos", True, True),
        (True, "so_pacientes_novos", False, False),
    ],
)
def test_exige_pagamento(exige, para, paciente_novo, esperado):
    regras = RegrasClinica(exige_pagamento_antecipado=exige, pagamento_exigido_para=para)
    assert regras.exige_pagamento(paciente_novo) is esperado
