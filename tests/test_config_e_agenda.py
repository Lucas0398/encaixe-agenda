import pytest

from encaixe.agenda.porta import AgendaEmMemoria
from encaixe.config import Config, ConfigIncompleta
from encaixe.dominio.disponibilidade import Intervalo
from tests.conftest import em

ENV_MINIMO = {
    "DATABASE_URL": "postgresql://localhost/encaixe",
    "WHATSAPP_TOKEN": "t",
    "WHATSAPP_PHONE_NUMBER_ID": "123",
    "WHATSAPP_APP_SECRET": "s",
    "WHATSAPP_VERIFY_TOKEN": "v",
    "WHATSAPP_GRAPH_VERSAO": "v23.0",
}


def test_config_completa():
    cfg = Config.de_ambiente(ENV_MINIMO)
    assert cfg.whatsapp_phone_number_id == "123"
    assert cfg.ambiente == "desenvolvimento"


def test_config_lista_o_que_falta():
    with pytest.raises(ConfigIncompleta, match="WHATSAPP_TOKEN"):
        Config.de_ambiente({k: v for k, v in ENV_MINIMO.items() if k != "WHATSAPP_TOKEN"})


def test_agenda_em_memoria():
    agenda = AgendaEmMemoria()
    sessao = Intervalo(em(2026, 11, 30, 9), em(2026, 11, 30, 10))
    eid = agenda.criar_evento("cal", sessao, titulo="Sessão – Maria", agendamento_id="ag1")
    dia = Intervalo(em(2026, 11, 30), em(2026, 12, 1))
    assert [e.agendamento_id for e in agenda.listar_eventos("cal", dia)] == ["ag1"]

    nova = Intervalo(em(2026, 12, 1, 9), em(2026, 12, 1, 10))
    agenda.atualizar_evento("cal", eid, intervalo=nova)
    assert agenda.listar_eventos("cal", dia) == []

    agenda.remover_evento("cal", eid)
    assert agenda.eventos["cal"] == {}
