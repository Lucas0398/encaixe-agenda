"""Feriados nacionais e pontos facultativos (usados na grade de horários).

Feriados estaduais e municipais variam por cidade: cadastre-os em
`RegrasClinica.datas_bloqueadas`, confirmando a lista com a clínica.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher, calendário gregoriano)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 - nome do algoritmo
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


@lru_cache(maxsize=64)
def feriados_nacionais(ano: int) -> frozenset[date]:
    fixos = [
        (1, 1),  # Confraternização Universal
        (4, 21),  # Tiradentes
        (5, 1),  # Dia do Trabalho
        (9, 7),  # Independência
        (10, 12),  # Nossa Senhora Aparecida
        (11, 2),  # Finados
        (11, 15),  # Proclamação da República
        (11, 20),  # Consciência Negra (Lei 14.759/2023)
        (12, 25),  # Natal
    ]
    datas = {date(ano, mes, dia) for mes, dia in fixos}
    datas.add(pascoa(ano) - timedelta(days=2))  # Sexta-feira Santa
    return frozenset(datas)


@lru_cache(maxsize=64)
def pontos_facultativos(ano: int) -> frozenset[date]:
    p = pascoa(ano)
    return frozenset(
        {
            p - timedelta(days=48),  # Carnaval (segunda)
            p - timedelta(days=47),  # Carnaval (terça)
            p + timedelta(days=60),  # Corpus Christi
        }
    )
