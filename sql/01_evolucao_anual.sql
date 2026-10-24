-- Média anual de cada série: a visão geral de como juros e inadimplência evoluíram.
SELECT
    year(data)              AS ano,
    codigo,
    nome,
    round(avg(valor), 2)    AS media
FROM series
GROUP BY ALL
ORDER BY nome, ano;
