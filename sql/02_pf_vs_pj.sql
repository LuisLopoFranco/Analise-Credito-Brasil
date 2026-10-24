-- Pessoa física x jurídica, ano a ano: a diferença nos juros e quantas vezes
-- a inadimplência de PF é a de PJ.
-- PIVOT transforma as séries (linhas) em colunas para poder comparar uma com a outra.
WITH mensal AS (
    PIVOT (SELECT codigo, data, valor FROM series WHERE codigo IN (20715, 20716, 21083, 21084))
    ON codigo
    USING first(valor)
)
SELECT
    year(data)                          AS ano,
    round(avg("20716" - "20715"), 2)    AS juros_pf_menos_pj,
    round(avg("21084" / "21083"), 2)    AS inadimplencia_pf_sobre_pj
FROM mensal
GROUP BY ALL
ORDER BY ano;