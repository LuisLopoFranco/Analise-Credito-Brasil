-- A Selic alta leva a mais inadimplência? E quanto tempo depois?
-- Correlação entre a Selic média do mês e a inadimplência total de 0 a 18 meses depois.
WITH selic_mensal AS (
    SELECT date_trunc('month', data) AS mes, avg(valor) AS selic
    FROM series
    WHERE codigo = 432
    GROUP BY ALL
),
inadimplencia AS (
    SELECT date_trunc('month', data) AS mes, valor AS inadimplencia
    FROM series
    WHERE codigo = 21082
),
defasagens AS (
    SELECT unnest(range(0, 19)) AS meses
)
SELECT
    d.meses                                   AS defasagem_meses,
    round(corr(s.selic, i.inadimplencia), 3)  AS correlacao,
    count(*)                                  AS meses_comparados
FROM defasagens AS d
JOIN selic_mensal AS s ON true
JOIN inadimplencia AS i ON i.mes = s.mes + to_months(d.meses)
GROUP BY d.meses
ORDER BY d.meses;