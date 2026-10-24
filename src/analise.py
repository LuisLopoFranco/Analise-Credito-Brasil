"""Roda as consultas de sql/, mostra os resultados e gera os gráficos em docs/graficos/.

Uso: python -m src.analise
"""

from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.carga import CAMINHO_BANCO  # noqa: E402

PASTA_SQL = Path("sql")
PASTA_GRAFICOS = Path("docs/graficos")

# Cores categóricas em ordem fixa (validadas para daltonismo), sempre na mesma ordem.
CORES = ["#2a78d6", "#eb6834", "#1baf7a"]
TINTA = "#3d3d3a"
GRADE = "#e3e2dc"


def consulta(conexao: duckdb.DuckDBPyConnection, arquivo: str):
    return conexao.execute((PASTA_SQL / arquivo).read_text(encoding="utf-8")).df()


def _estilo(ax, titulo: str, unidade: str) -> None:
    ax.set_title(titulo, loc="left", fontsize=12, color=TINTA, pad=28)
    ax.set_ylabel(unidade, color=TINTA)
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.tick_params(colors=TINTA, length=0)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(GRADE)


def grafico_linhas(conexao, codigos: dict[int, str], titulo: str, unidade: str, arquivo: str) -> Path:
    """Uma linha por série, com legenda e o último valor rotulado na ponta da linha."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for cor, (codigo, rotulo) in zip(CORES, codigos.items()):
        df = conexao.execute(
            "SELECT data, valor FROM series WHERE codigo = ? ORDER BY data", [codigo]
        ).df()
        ax.plot(df["data"], df["valor"], color=cor, linewidth=2, label=rotulo)
        ultimo = df.iloc[-1]
        ax.annotate(f"{rotulo} {ultimo['valor']:.1f}".replace(".", ","),
                    (ultimo["data"], ultimo["valor"]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9, color=TINTA)
    _estilo(ax, titulo, unidade)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1), ncol=len(codigos),
              labelcolor=TINTA, borderaxespad=0.2)
    fig.tight_layout()
    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_GRAFICOS / arquivo
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    return caminho


def main() -> None:
    with duckdb.connect(str(CAMINHO_BANCO), read_only=True) as conexao:
        print("\nMédia anual de cada série (colunas = código SGS, veja a tabela no README):")
        anual = consulta(conexao, "01_evolucao_anual.sql")
        print(anual.pivot(index="ano", columns="codigo", values="media").to_string())

        print("\nPessoa física x jurídica, por ano:")
        print(consulta(conexao, "02_pf_vs_pj.sql").to_string(index=False))

        print("\nSelic x inadimplência total, com defasagem:")
        defasagens = consulta(conexao, "03_selic_vs_inadimplencia.sql")
        print(defasagens.to_string(index=False))
        melhor = defasagens.loc[defasagens["correlacao"].idxmax()]
        print(f"Maior correlação: {melhor['correlacao']:.3f} "
              f"com {int(melhor['defasagem_meses'])} meses de defasagem")

        gerados = [
            grafico_linhas(conexao, {21082: "Total", 21084: "PF", 21083: "PJ"},
                           "Inadimplência da carteira de crédito", "% da carteira",
                           "inadimplencia.png"),
            grafico_linhas(conexao, {20714: "Total", 20716: "PF", 20715: "PJ"},
                           "Taxa média de juros das operações de crédito", "% ao ano",
                           "juros.png"),
        ]
    print("\nGráficos:", ", ".join(str(g) for g in gerados))


if __name__ == "__main__":
    main()