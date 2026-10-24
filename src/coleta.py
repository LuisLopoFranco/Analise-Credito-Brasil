"""Baixa as séries do Banco Central e salva um CSV por série em dados/bruto/.

Uso: python -m src.coleta
"""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.series import DATA_INICIAL, SERIES

URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
PASTA_BRUTO = Path("dados/bruto")

# O SGS recusa consultas de séries diárias com mais de 10 anos;
# janelas de 5 anos funcionam para todas as séries.
ANOS_POR_JANELA = 5

# A API às vezes responde 502/503 por alguns segundos; nesses casos vale tentar de novo.
TENTATIVAS = 5


def janelas(inicio: date, fim: date, anos: int = ANOS_POR_JANELA) -> list[tuple[date, date]]:
    """Divide o período em janelas consecutivas de no máximo `anos` anos.

    `inicio` deve ser o dia 1 de um mês (29/02 não existe em todo ano).
    """
    resultado = []
    atual = inicio
    while atual <= fim:
        proximo = atual.replace(year=atual.year + anos)
        resultado.append((atual, min(proximo - timedelta(days=1), fim)))
        atual = proximo
    return resultado


def para_dataframe(registros: list[dict], codigo: int) -> pd.DataFrame:
    """Converte a resposta JSON do SGS ({"data": "dd/mm/aaaa", "valor": "1.23"}) em DataFrame."""
    df = pd.DataFrame(registros, columns=["data", "valor"])
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df.insert(0, "codigo", codigo)
    return df.dropna(subset=["valor"])


def criar_sessao(tentativas: int = TENTATIVAS) -> requests.Session:
    """Sessão HTTP que repete o pedido quando o servidor falha.

    A 1ª repetição é na hora; as seguintes esperam 2, 4, 8 e 16 segundos.
    """
    retry = Retry(
        total=tentativas,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    sessao = requests.Session()
    sessao.mount("https://", HTTPAdapter(max_retries=retry))
    return sessao


def baixar_serie(codigo: int, inicio: date, fim: date, sessao: requests.Session) -> pd.DataFrame:
    partes = []
    for ini, fi in janelas(inicio, fim):
        resposta = sessao.get(
            URL_SGS.format(codigo=codigo),
            params={
                "formato": "json",
                "dataInicial": ini.strftime("%d/%m/%Y"),
                "dataFinal": fi.strftime("%d/%m/%Y"),
            },
            timeout=60,
        )
        # Janela sem dados (por exemplo, no futuro) volta como 404.
        if resposta.status_code == 404:
            continue
        resposta.raise_for_status()
        partes.append(para_dataframe(resposta.json(), codigo))
    if not partes:
        return para_dataframe([], codigo)
    return pd.concat(partes).drop_duplicates(subset=["data"]).sort_values("data")


def main() -> None:
    PASTA_BRUTO.mkdir(parents=True, exist_ok=True)
    inicio = date.fromisoformat(DATA_INICIAL)
    with criar_sessao() as sessao:
        for codigo, nome in SERIES.items():
            df = baixar_serie(codigo, inicio, date.today(), sessao)
            df.to_csv(PASTA_BRUTO / f"{codigo}.csv", index=False)
            print(f"{codigo} {nome}: {len(df)} registros, último em {df['data'].max():%m/%Y}")


if __name__ == "__main__":
    main()