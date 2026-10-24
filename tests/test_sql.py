from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.carga import carregar


@pytest.fixture
def conexao(tmp_path: Path):
    """Banco em memória com dados pequenos e conhecidos, para testar as consultas."""
    meses = pd.date_range("2020-01-01", periods=36, freq="MS")
    selic = [float(i) for i in range(36)]
    dados = {
        432: selic,
        20715: [20.0] * 36,
        20716: [50.0] * 36,
        21082: [0.0] * 12 + selic[:24],  # inadimplência = Selic de 12 meses antes
        21083: [2.0] * 36,
        21084: [5.0] * 36,
    }
    for codigo, valores in dados.items():
        pd.DataFrame({"codigo": codigo, "data": meses, "valor": valores}).to_csv(
            tmp_path / f"{codigo}.csv", index=False
        )
    con = duckdb.connect()
    carregar(con, tmp_path)
    yield con
    con.close()


def rodar(conexao, arquivo):
    return conexao.execute(Path("sql", arquivo).read_text(encoding="utf-8")).df()


def test_carga_traz_nome_da_serie(conexao):
    nome = conexao.execute("SELECT DISTINCT nome FROM series WHERE codigo = 21082").fetchone()[0]
    assert nome.startswith("Inadimplência")


def test_evolucao_anual_tem_uma_linha_por_serie_e_ano(conexao):
    df = rodar(conexao, "01_evolucao_anual.sql")
    assert len(df) == 6 * 3


def test_pf_vs_pj_compara_as_series_por_ano(conexao):
    df = rodar(conexao, "02_pf_vs_pj.sql")
    assert df["ano"].tolist() == [2020, 2021, 2022]
    assert (df["juros_pf_menos_pj"] == 30.0).all()
    assert (df["inadimplencia_pf_sobre_pj"] == 2.5).all()


def test_selic_vs_inadimplencia_acha_a_defasagem_certa(conexao):
    df = rodar(conexao, "03_selic_vs_inadimplencia.sql").set_index("defasagem_meses")
    assert df.loc[12, "correlacao"] == 1.0
    assert df.loc[12, "meses_comparados"] == 24