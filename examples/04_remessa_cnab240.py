"""Remessa CNAB 240 (Sicoob) com PIX no segmento Y-03.

    python examples/04_remessa_cnab240.py

Sai um arquivo com os segmentos P, Q, R (encargos) e Y (PIX).
"""

from __future__ import annotations

from datetime import date

from _comum import grava, titulo

from pycobranca.cnab import PagamentoPix, RemessaSicoob240Pix


def main() -> None:
    pagamentos = [
        PagamentoPix(
            nosso_numero="12345678",
            numero="DOC0001",
            valor=350.00,
            data_vencimento=date(2026, 8, 15),
            data_emissao=date(2026, 7, 23),
            documento_sacado="52998224725",
            nome_sacado="Cliente Final da Silva",
            endereco_sacado="Rua das Flores, 100",
            bairro_sacado="Centro",
            cep_sacado="30110000",
            cidade_sacado="Belo Horizonte",
            uf_sacado="MG",
            tipo_mora="2",
            percentual_mora=1.00,  # 1% ao mês
            codigo_multa="2",
            percentual_multa=2.00,
            # Bolepix: chave DICT + TXID vão para o segmento Y-03.
            tipo_chave_dict="cnpj",
            codigo_chave_dict="11222333000181",
            txid="TX2026080100001",
        ),
    ]

    remessa = RemessaSicoob240Pix(
        empresa_mae="Empresa Exemplo LTDA",
        documento_cedente="11222333000181",
        agencia="1234",
        conta_corrente="12345678",
        digito_conta="5",
        convenio="123456",
        modalidade_carteira="01",
        tipo_formulario="4",
        parcela="01",
        sequencial_remessa="1",
        data_geracao_fixa="23072026",
        hora_geracao_fixa="120000",
        pagamentos=pagamentos,
    )

    arquivo = remessa.gera_arquivo()
    linhas = arquivo.splitlines()
    segmentos = [linha[13] for linha in linhas if len(linha) > 13 and linha[7] == "3"]

    titulo("Remessa CNAB 240 — Sicoob (756) com PIX")
    print(f"Registros: {len(linhas)}  ·  tamanho: {len(linhas[0])} posições")
    print("Segmentos de detalhe:", " ".join(segmentos) or "(nenhum)")
    print("Header de arquivo:", linhas[0][:40])
    grava("04-remessa-sicoob-pix.rem", arquivo)


if __name__ == "__main__":
    main()
