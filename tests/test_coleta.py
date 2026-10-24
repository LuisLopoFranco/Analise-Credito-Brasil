from datetime import date

from src.coleta import criar_sessao,janelas,para_dataframe


def test_janelas_cobrem_o_periodo_sem_sobreposicao():
    resultado = janelas(date(2011, 3, 1), date(2026, 10, 16))

    assert resultado[0] == (date(2011, 3, 1), date(2016, 2, 29))
    assert resultado[-1][1] == date(2026, 10, 16)
    for (_, fim), (inicio_seguinte, _) in zip(resultado, resultado[1:]):
        assert (inicio_seguinte - fim).days == 1


def test_para_dataframe_converte_data_e_valor():
    # Formato real devolvido pela API do SGS (série 21082).
    registros = [
        {"data": "01/06/2026", "valor": "4.58"},
        {"data": "01/07/2026", "valor": "4.88"},
        {"data": "01/08/2026", "valor": ""},
    ]

    df = para_dataframe(registros, 21082)

    assert list(df.columns) == ["codigo", "data", "valor"]
    assert len(df) == 2  # valor vazio é descartado
    assert df["valor"].tolist() == [4.58, 4.88]
    assert df["data"].dt.month.tolist() == [6, 7]
    assert (df["codigo"] == 21082).all()

def test_sessao_tenta_de_novo_quando_o_servidor_falha():
    retry = criar_sessao().get_adapter("https://api.bcb.gov.br").max_retries

    assert retry.total == 5
    assert 502 in retry.status_forcelist
    assert 404 not in retry.status_forcelist  # 404 = janela sem dados, não é falha