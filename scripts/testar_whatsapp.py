"""Testa o envio pela WhatsApp Cloud API (critério de pronto da LS-14).

Uso:
    python scripts/testar_whatsapp.py 5582999990000

Sem outros argumentos, envia o template `hello_world` (já vem aprovado em
toda conta nova, em inglês). Para testar texto livre, primeiro mande uma
mensagem do seu celular para o número de teste (abre a janela de 24h) e rode:
    python scripts/testar_whatsapp.py 5582999990000 --texto "Olá do EncaixeAgenda"

Lê WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_GRAPH_VERSAO do ambiente.
"""

from __future__ import annotations

import argparse
import asyncio
import os

from encaixe.whatsapp.cliente import ClienteWhatsApp


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("telefone", help="Número com DDI e DDD, só dígitos. Ex.: 5582999990000")
    parser.add_argument("--texto", help="Envia texto livre em vez do template hello_world")
    args = parser.parse_args()

    cliente = ClienteWhatsApp(
        token=os.environ["WHATSAPP_TOKEN"],
        phone_number_id=os.environ["WHATSAPP_PHONE_NUMBER_ID"],
        graph_versao=os.environ["WHATSAPP_GRAPH_VERSAO"],
    )
    try:
        if args.texto:
            wamid = await cliente.enviar_texto(args.telefone, args.texto)
        else:
            wamid = await cliente.enviar_template(args.telefone, "hello_world", idioma="en_US")
        print(f"Enviado. id da mensagem: {wamid}")
    finally:
        await cliente.fechar()


if __name__ == "__main__":
    asyncio.run(main())
