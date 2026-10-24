"""Carrega os CSVs de dados/bruto/ numa tabela `series` do DuckDB.

Uso: python -m src.carga
"""

from pathlib import Path

import duckdb

from src.series import SERIES

CAMINHO_BANCO = Path("dados/credito.duckdb")
PASTA_BRUTO = Path("dados/bruto")


def carregar(conexao: duckdb.DuckDBPyConnection, pasta: Path = PASTA_BRUTO) -> int:
    conexao.execute("""
        CREATE OR REPLACE TABLE series (
            codigo INTEGER,
            nome   VARCHAR,
            data   DATE,
            valor  DOUBLE
        )
    """)
    conexao.execute("CREATE OR REPLACE TEMP TABLE nomes (codigo INTEGER, nome VARCHAR)")
    conexao.executemany("INSERT INTO nomes VALUES (?, ?)", list(SERIES.items()))
    conexao.execute(f"""
        INSERT INTO series
        SELECT b.codigo, n.nome, b.data, b.valor
        FROM read_csv('{pasta.as_posix()}/*.csv', header = true,
                      columns = {{'codigo': 'INTEGER', 'data': 'DATE', 'valor': 'DOUBLE'}}) AS b
        JOIN nomes AS n USING (codigo)
    """)
    return conexao.execute("SELECT count(*) FROM series").fetchone()[0]


def main() -> None:
    with duckdb.connect(str(CAMINHO_BANCO)) as conexao:
        total = carregar(conexao)
    print(f"{total} linhas carregadas em {CAMINHO_BANCO}")


if __name__ == "__main__":
    main()