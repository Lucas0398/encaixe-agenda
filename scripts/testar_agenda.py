"""Testa o acesso ao Google Agenda pela conta de serviço (critério de pronto da LS-12).

Uso:
    python scripts/testar_agenda.py SEU_CALENDAR_ID            # lista os eventos de amanhã
    python scripts/testar_agenda.py SEU_CALENDAR_ID --escrever  # cria e apaga um evento de teste

O Calendar ID fica em Google Agenda → Configurações da agenda → Integrar agenda.
Lê GOOGLE_CREDENCIAIS_ARQUIVO do ambiente.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from encaixe.agenda.google import AgendaGoogle, janela_do_dia
from encaixe.dominio.disponibilidade import Intervalo

FUSO = "America/Maceio"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("calendario_id")
    parser.add_argument("--escrever", action="store_true", help="Cria e remove um evento de teste")
    args = parser.parse_args()

    agenda = AgendaGoogle(os.environ.get("GOOGLE_CREDENCIAIS_ARQUIVO", "credenciais/google-service-account.json"), FUSO)
    amanha = datetime.now(ZoneInfo(FUSO)).date() + timedelta(days=1)

    eventos = agenda.listar_eventos(args.calendario_id, janela_do_dia(amanha, FUSO))
    print(f"{len(eventos)} evento(s) em {amanha:%d/%m}:")
    for e in eventos:
        print(f"  {e.intervalo.inicio:%H:%M}–{e.intervalo.fim:%H:%M}  {e.titulo}")

    if args.escrever:
        inicio = datetime.combine(amanha, datetime.min.time(), tzinfo=ZoneInfo(FUSO)).replace(hour=7)
        evento_id = agenda.criar_evento(
            args.calendario_id,
            Intervalo(inicio, inicio + timedelta(minutes=30)),
            titulo="[TESTE] EncaixeAgenda",
            agendamento_id="teste",
        )
        print(f"Evento de teste criado: {evento_id}")
        agenda.remover_evento(args.calendario_id, evento_id)
        print("Evento de teste removido. Leitura e escrita funcionando.")


if __name__ == "__main__":
    main()
