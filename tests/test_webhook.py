import hashlib
import hmac
import json

from encaixe.whatsapp.webhook import (
    assinatura_valida,
    extrair_mensagens,
    extrair_status,
    responder_desafio,
)


def _payload(mensagens=None, statuses=None):
    valor = {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": "558230000000", "phone_number_id": "PNID123"},
        "contacts": [{"profile": {"name": "Maria"}, "wa_id": "5582999990000"}],
    }
    if mensagens is not None:
        valor["messages"] = mensagens
    if statuses is not None:
        valor["statuses"] = statuses
    return {
        "object": "whatsapp_business_account",
        "entry": [{"id": "WABA", "changes": [{"field": "messages", "value": valor}]}],
    }


def test_desafio_com_token_certo():
    params = {"hub.mode": "subscribe", "hub.verify_token": "segredo", "hub.challenge": "123"}
    assert responder_desafio(params, "segredo") == "123"


def test_desafio_com_token_errado():
    params = {"hub.mode": "subscribe", "hub.verify_token": "outro", "hub.challenge": "123"}
    assert responder_desafio(params, "segredo") is None
    assert responder_desafio(params | {"hub.verify_token": ""}, "") is None


def test_assinatura():
    corpo = b'{"a":1}'
    assinatura = "sha256=" + hmac.new(b"app-secret", corpo, hashlib.sha256).hexdigest()
    assert assinatura_valida(corpo, assinatura, "app-secret")
    assert not assinatura_valida(corpo + b" ", assinatura, "app-secret")
    assert not assinatura_valida(corpo, None, "app-secret")
    assert not assinatura_valida(corpo, assinatura, "")


def test_mensagem_de_texto():
    msg = {
        "from": "5582999990000",
        "id": "wamid.1",
        "timestamp": "1764244800",
        "type": "text",
        "text": {"body": "quero marcar"},
    }
    [m] = extrair_mensagens(_payload([msg]))
    assert m.tipo == "texto" and m.texto == "quero marcar"
    assert m.nome_perfil == "Maria" and m.numero_destino_id == "PNID123"
    assert m.recebida_em.isoformat() == "2025-11-27T12:00:00+00:00"


def test_botao_de_template():
    msg = {
        "from": "5582999990000",
        "id": "wamid.2",
        "timestamp": "1764244800",
        "type": "button",
        "button": {"payload": "confirmar_presenca", "text": "Confirmo"},
        "context": {"id": "wamid.lembrete"},
    }
    [m] = extrair_mensagens(_payload([msg]))
    assert (m.tipo, m.botao_id, m.texto, m.responde_a) == ("botao", "confirmar_presenca", "Confirmo", "wamid.lembrete")


def test_resposta_interativa_e_audio():
    msgs = [
        {
            "from": "1",
            "id": "a",
            "timestamp": "1",
            "type": "interactive",
            "interactive": {"type": "button_reply", "button_reply": {"id": "slot_3", "title": "Seg 09:00"}},
        },
        {"from": "1", "id": "b", "timestamp": "1", "type": "audio", "audio": {"id": "media"}},
        {"from": "1", "id": "c", "timestamp": "1", "type": "sticker"},
    ]
    a, b, c = extrair_mensagens(_payload(msgs))
    assert (a.tipo, a.botao_id) == ("botao", "slot_3")
    assert b.tipo == "audio"
    assert c.tipo == "nao_suportado"


def test_status_de_entrega():
    st = {
        "id": "wamid.9",
        "status": "failed",
        "timestamp": "1764244800",
        "recipient_id": "5582999990000",
        "errors": [{"code": 131047}],
    }
    payload = json.loads(json.dumps(_payload(statuses=[st])))
    [s] = extrair_status(payload)
    assert s.status == "failed" and s.erros[0]["code"] == 131047
    assert extrair_mensagens(payload) == []
