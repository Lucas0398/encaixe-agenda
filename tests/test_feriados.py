from datetime import date

import pytest

from encaixe.dominio.feriados import feriados_nacionais, pascoa, pontos_facultativos


@pytest.mark.parametrize(
    ("ano", "esperado"),
    [(2024, date(2024, 3, 31)), (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)), (2027, date(2027, 3, 28))],
)
def test_pascoa(ano, esperado):
    assert pascoa(ano) == esperado


def test_feriados_2026():
    f = feriados_nacionais(2026)
    assert date(2026, 4, 3) in f  # Sexta-feira Santa
    assert date(2026, 11, 20) in f  # Consciência Negra
    assert date(2026, 12, 25) in f
    assert date(2026, 12, 24) not in f


def test_pontos_facultativos_2026():
    p = pontos_facultativos(2026)
    assert {date(2026, 2, 16), date(2026, 2, 17), date(2026, 6, 4)} == set(p)
