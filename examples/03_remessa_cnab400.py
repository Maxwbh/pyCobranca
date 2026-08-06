"""Remessa CNAB 400 (Itaú) com juros, multa e desconto.

    python examples/03_remessa_cnab400.py

Os encargos são opcionais: sem eles, o boleto sai limpo e o caixa calcula.
"""

from __future__ import annotations

from datetime import date

from _comum import grava, titulo

from pycobranca.cnab import Pagamento, RemessaItau400


def main() -> None:
    pagamentos = [
        Pagamento(
            nosso_numero="12345678",
            numero="DOC0001",
            valor=199.90,
            data_vencimento=date(2026, 8, 15),
            data_emissao=date(2026, 7, 23),
            documento_sacado="52998224725",
            nome_sacado="Cliente Final da Silva",
            endereco_sacado="Rua das Flores, 100",
            bairro_sacado="Centro",
            cep_sacado="30110000",
            cidade_sacado="Belo Horizonte",
            uf_sacado="MG",
            # Juros de mora por dia (tipo_mora="1"); "2" seria taxa mensal em %.
            tipo_mora="1",
            valor_mora=1.53,
            # Multa por atraso — sempre percentual no padrão FEBRABAN.
            codigo_multa="2",
            percentual_multa=2.00,
            data_multa=date(2026, 8, 16),
            # Desconto por pontualidade (1ª faixa).
            cod_desconto="1",
            valor_desconto=10.00,
            data_desconto=date(2026, 8, 1),
        ),
    ]

    remessa = RemessaItau400(
        empresa_mae="Empresa Exemplo LTDA",
        documento_cedente="11222333000181",
        agencia="0057",
        conta_corrente="12345",
        digito_conta="7",
        carteira="109",
        data_geracao=date(2026, 7, 23),
        pagamentos=pagamentos,
    )

    # Coerência dos encargos (valor > 0, mora/multa/desconto consistentes).
    for pagamento in pagamentos:
        pagamento.validar()

    arquivo = remessa.gera_arquivo()
    linhas = arquivo.splitlines()

    titulo("Remessa CNAB 400 — Itaú (341)")
    print(f"Registros: {len(linhas)} (header + títulos + trailer)")
    print(f"Tamanho do registro: {len(linhas[0])} posições")
    print("Header: ", linhas[0][:60])
    print("Título: ", linhas[1][:60])
    grava("03-remessa-itau.rem", arquivo)


if __name__ == "__main__":
    main()
