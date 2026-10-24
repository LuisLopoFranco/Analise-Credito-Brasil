"""Séries do SGS (Sistema Gerenciador de Séries Temporais) do Banco Central usadas no projeto.

Os códigos podem ser conferidos em https://dadosabertos.bcb.gov.br (busque pelo número).
"""

SERIES = {
    432: "Selic meta (% a.a.)",
    20714: "Juros médios do crédito - Total (% a.a.)",
    20715: "Juros médios do crédito - Pessoa jurídica (% a.a.)",
    20716: "Juros médios do crédito - Pessoa física (% a.a.)",
    21082: "Inadimplência - Total (%)",
    21083: "Inadimplência - Pessoa jurídica (%)",
    21084: "Inadimplência - Pessoa física (%)",
}

# As séries mensais de juros e inadimplência começam em março de 2011.
DATA_INICIAL = "2011-03-01"